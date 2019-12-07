from .crypt import AES, RSA, FormatBytes
from Crypto.Random import random as rand
from hashlib import sha256
from threading import Thread, Timer, Event, current_thread as currThread, main_thread as mainThread
import time, string, re, traceback, sys, base64

Characters = string.punctuation + string.digits + string.ascii_letters

class TPorts:
	"""
	Theoretical ports used in simulation
	"""

	SEND_RECEIVE = 2 # Normal sending and receiving data
	SERVER_BROADCAST = 4 # For send and receiveing data from a broadcast

class TAddress:
	"""
	Theoretical addresses used to identify a socket/destination
	Requires both an ip and a port
	"""

	allAddresses = [] # All registered addresses

	@staticmethod
	def isRegisteredAddress(addr: str = "", port: int = 0):
		"""
		Checks if an address on a port has been registered

		:param addr str: The address
		:param port int: The port

		:returns bool: If the address is registered on that port
		"""
		for addr in TAddress.allAddresses: # Loop through all addresses
			if addr.addr == (addr, port) and addr.registered: return True # If the ip, port, and the address is still registered then return true
		return False # An address on the address and port was not found, return false

	def __init__(self, addr: str = "", port: int = 0):
		"""
		Init

		:param addr str: The address to register on
		:param port int: The port to register with

		:returns self: Instance
		"""
		self.addr = (addr, port) # Save address and port in tuple
		self.registered = True # Set that this address is registered
		TAddress.allAddresses.append(self) # Add this address to list of all addresses

	def __str__(self):
		"""
		To string

		:returns str: The format of ADDRESS:PORT
		"""
		return self.addr[0] + ":" + str(self.addr[1])

	def free(self):
		"""
		Unregisters an address, "frees" it up to be used by another
		
		:returns None: Nothing is returned
		"""
		self.registered = False # Set that this address is no longer registered
		TAddress.allAddresses.remove(self) # Remove this address from list of addresses

class TData:
	"""
	Theoretical data that is sent over a socket
	"""

	def __init__(self, data: str = "", isBroadcast: bool = False):
		"""
		Init

		:param data str: The message
		:param isBroadcast bool: If this message is being broadcasted

		:returns self: Instance
		"""
		self.data = data # Save message
		self._read = False # Set that it hasn't been read yet
		self._isBroadcast = isBroadcast # Save if it's a broadcast

	def __len__(self):
		"""
		Get Length

		:returns int: The length of the data
		"""
		return len(self.data) if (not self._read) or self._isBroadcast else 0 # if it has been read and isn't a broadcast, return 0 instead, else return data length

	def get(self):
		"""
		Read data

		:returns str: The data if it hasn't been read or it is a broadcast, else None
		"""
		if self._read == False or self._isBroadcast: # If it hasn't been read or it is a broadcast
			self._read = True # Set that the data has been read
			return self.data # Return the data
		return None # Return none

class TSocket:
	"""
	Theoretical socket used to send data
	"""

	allSockets = [] # All sockets

	@staticmethod
	def sendDataProtected(sender: TAddress = None, receiver: TAddress = None, data: str = None):
		"""
		Send data directly to an address without using a socket, only two address and data

		:param sender TAddress: The sender's address
		:param receiver TAddress: The receiver's address
		:param data str: The data to send

		:returns None: Nothing is returned
		"""
		for sock in TSocket.allSockets: # Loop through ever socket as sock
			if sock._addr.registered and str(sock._addr) == str(receiver): # If socket is registered and it's address matches the receiver
				# In a real situation, any socket could receive this message but we're assuming that a socket only accepts messages for itself
				SimpleThread(target=sock.receive, args=(sender, TData(data, False))).start() # Start a thread to send data so one socket can't hold up everything
				return # End loop as socket was sent message

	@staticmethod
	def getSocket(getterIP: str = "127.0.0.1", addr: TAddress = None):
		"""
		Get a socket with the address: addr and who is getting it, getterIP

		:param getterIP str: IP of socket get caller
		:param addr TAddress: The address to lookup

		:return TSocket: The found socket or a newly created one, or if getterIP isn't type str, then return None
		"""
		for sock in TSocket.allSockets: # Loop through ever socket as sock
			if sock._addr == addr: # If the socket's address matches the address to find
				return sock # Return the socket
		if type(getterIP) != str: return None #  If getterIP isn't type string, then return None
		return TSocket.createNewSocket(getterIP, addr) # If getterIP passed type check, then create a new socket and return it

	@staticmethod
	def createNewSocket(spawnerIP: str = "127.0.0.1", addr: TAddress = None):
		"""
		Creates a new socket for address addr from the spawner ip of spawnerIP

		:param spawnerIP str: IP of create new socket caller
		:param addr TAddress: The address to create the socket for

		:return TSocket: The socket created
		"""
		sock = TSocket(spawnerIP, addr) # Create new instance of socket
		TSocket.allSockets.append(sock) # Add socket to list of sockets
		return sock # Return the new socket instance

	def __init__(self, ip: str = "127.0.0.1", addr: TAddress = None):
		"""
		Init

		:param ip str: IP that socket was spawned from
		:param addr TAddress: Address for the socket

		:param self: Instance
		"""
		self._spawnedFrom = ip # Save ip
		self._addr = addr # Save address
		self._dataHistroy = [] # Create an empty data history
		self._lastDataReceived = None # No previous data has been received so make None
		self._receiveEvent = Event() # Create event for data being received
		self._receivers = 0 # Number of threads waiting for event
		self._callbackID = rand.randint(-1 * (2 ** 32), 2 ** 32) # Randomly generated callback id to prevent a socket from sending data to itself

	def __str__(self):
		"""
		To string

		:returns str: Data about the object: address, data histroy, last data received, event status, receivers, and callback id
		"""
		return f"Address: {self._addr}, Data History: {self._dataHistroy}, Last Data Received: {self._lastDataReceived}, \
Receive Event Set: {self._receiveEvent.is_set()}, Receivers: {self._receivers}, and Callback ID: {self._callbackID}" # All data from socket in string format

	def receive(self, addr: TAddress = None, data: TData = None):
		"""
		Internal function other sockets use to tell another socket that they've received data

		:param addr TAddress: Sender's address
		:param data TData: Data send by sender

		:returns None: Nothing is returned
		"""
		if self.closed(): return # If socket has been closed, cease execution
		if type(data) is not TData: return # If data type isn't TData, exit
		data = data.get() # Read data that was sent
		if data is None: # If None was returned then that means that the data has been A) read previously or B) was set to be None
			print("Data was already read before we received it, was this meant broadcasted message?") # Debug info
			return # Exit
		self._dataHistroy.append([addr, data]) # Added this to the data history
		while len(self._dataHistroy) > 25: del self._dataHistroy[0] # While the length of the data history is greater than 25, remove the first entry
		self._lastDataReceived = [addr, data] # Set the last received data to be the address and data
		timeout = 0 # Set timeout for mutliple receives being called at once
		while self._receiveEvent.is_set() and timeout < 3: # While the event is set and the timeout is less than 3
			time.sleep(.05) # Wait .05 seconds
			timeout += 1 # Increase timeout by 1
		if timeout == 3: return # If timeout == 3 then the receiveData wasn't called in time
		self._receiveEvent.set() # Set the event so receiveData listeners can read new data

	def receiveData(self):
		"""
		Function to call to halt thread until data has been received by socket
		This method should be called outside of the main thread
		Function will return None if it is called from main thread
		"""
		if self.closed(): return [None, None] # If socket has been closed, return None
		if currThread() is mainThread(): # If function has been called from main python thread
			print("An attempt was made to join a thread from the main python thread") # Debug info
			return [None, None] # Return None
		if self._receivers >= 1: # If receivers is greater than 1
			print("2+ Threads Listening For Data!") # Debug info
			return [None, None] # Return None
		got = None # Currently gotten data
		self._receivers += 1 # Increase number of receivers as now one has started a possibly infinite loop
		while got is None: # While gotten data is None
			self._receiveEvent.wait() # Wait for event to be set
			got = self._lastDataReceived # Set the data gotten to be the data last received
		self._lastDataReceived = None # Set last data received to be None
		self._receiveEvent.clear() # Reset event
		self._receivers -= 1 # Remove this listener from total receivers
		return got # Return the gotten data

	def sendData(self, receiver: TAddress = None, data: str = None):
		"""
		Send data to another address

		:param receiver TAddress: The address to send data to
		:param data str: The data to send

		:returns None: Nothing is returned
		"""
		if self.closed(): return # If this socket has been closed, cease execution
		if receiver.addr[0] == "<broadcast>": # If the receiving address is a broadcast
			for sock in TSocket.allSockets: # Loop through every socket as sock
				if sock._addr.registered and sock._addr.addr == self._addr.addr and sock._callbackID != self._callbackID: # If socket is registered, matches address, and callback doesn't equal this sockets
					sock.receive(self._addr, TData(data, True)) # Send data to the socket
		else: TSocket.sendDataProtected(self._addr, receiver, data) # If address isn't a broadcast, use send data protected

	def closed(self):
		"""
		Gets if the socket has been closed

		:returns bool: If the socket's address is not registered
		"""
		return not self._addr.registered

	def close(self):
		"""
		Closes a socket, prevents furture calls to the socket

		:returns None: Nothing is returned
		"""
		self._addr.free() # Free socket's address
		if self in TSocket.allSockets: # If this socket is in list of all sockets
			TSocket.allSockets.remove(self) # Remove this socket from list of all sockets

class SimpleThread:
	"""
	My own implementation of threading made simple
	Still uses a Thread object for underlying threading but has better control
	Adds for looping threads to continuously call the target function
	"""

	def __init__(self, target = None, loop: bool = False, args = (), kwargs = {}):
		"""
		Init

		:param target function: The function that will be called by the thread
		:param loop bool: Should the function be continuously called
		:param args tuple: Arguments to pass to the function
		:param kwargs dict: Keyword arguments to pass to the function
		"""
		self._internalThread = Thread(target=self._internal) # Create internal thread, does actual threading
		self._target = target # Save target
		self._args = args # Save args
		self._kwargs = {} if kwargs is None else kwargs # If kwargs is None then added empty kwargs, else save kwargs
		self._loop = loop # Save whether function should loop
		self._running = False # Thread isn't running yet

	def stop(self):
		"""
		Stop the thread (change internal variable)

		:returns SimpleThread: self
		"""
		self._running = False # Set that thread isn't running
		return self # Return self

	def _internal(self):
		try: # Try-except to always delete isntance of the internal thread, args, and kwargs
			if self._loop: # If thread should loop
				while self._running: # While the thread is running
					try: self._target(*self._args, **self._kwargs) # Try to call the function with the args and kwargs
					except BaseException: # Catch all exceptions
						print(f"Theoretical Thread threw an error (1), closing thread\n{traceback.format_exc()}") # Debug info
						break # Break from loop
			else: # If thread shouldn't loop
				try: self._target(*self._args, **self._kwargs) # Call function with args and kwargs
				except BaseException: print(f"Theoretical Thread threw an error (2), closing thread\n{traceback.format_exc()}") # Catch all exceptions and print debug info
		finally: # Always execute
			self.stop() # Mark thread as stopped
			del self._internalThread, self._args, self._kwargs # Destroy instances of the internal thread, args, and kwargs

	def start(self):
		"""
		Start the internal thread

		:returns SimpleThread: self
		"""
		if self._running: return self # If thread is already running, return self
		self._running = True # Set that thread is running
		self._internalThread.start() # Start internal thread
		return self # Return self

	def join(self, timeout: int = 5):
		"""
		Allows for thread to join internal thread
		Should not and cannot be called form main thread

		:returns None: Nothing is returned
		"""
		if currThread() is mainThread(): # If function has been called from main thread
			print("An attempt was made to join a thread from the main python thread") # Debug info
			return [None, None] # return None
		self._internal.join(timeout) # Wait for thread to terminal but added timeout

class TNetworkable:
	"""
	An object that uses networking (server and client)
	"""

	def __init__(self, isServer: bool = False, fakeRealIP: str = None):
		"""
		Init

		:param isServer bool: Is instance a server
		:param fakeRealIP str: Fake ip of server or client

		:returns self: Instance
		"""
		self._isServer = isServer # Save if server
		self._ip = fakeRealIP # Save ip
		self._broadcastSocket = TSocket.createNewSocket(fakeRealIP, TAddress("<broadcast>", TPorts.SERVER_BROADCAST)) # Create broadcasting socket
		self._broadcastReceiveThread = SimpleThread(self._broadcastReceive, True).start() # Create broadcasting listening thread
		self._generalSocket = TSocket.createNewSocket(fakeRealIP, TAddress(fakeRealIP, TPorts.SEND_RECEIVE)) # Create general data receiving socket
		self._generalReceiveThread = SimpleThread(self._generalReceive, True).start() # Create general data listening thread
		self._networkingThreads = {} # Currently active networking threads {thread name: thread instance}
		self._activeProtocols = {} # Currently active protocol {"ip:port": Protocol instance}
		self._protocolHandler = ProtocolHandler(not isServer, self) # Create protocol handler

	def isIP(self, ipaddr: str = None):
		"""
		Checks if a string is an ip (valid format)

		:param ipaddr str: Possible ip address

		:returns bool: If it is an ip address or not
		"""
		if ipaddr is None or type(ipaddr) != str or not len(ipaddr): return False # If address is None type, isn't a string type, or is empty, return false
		return re.match("((\\.)*\\d{1,3}){4}", ipaddr) # Check if the string matches a normal IPv4 address' format

	def spawnThread(self, threadName: str = None, threadTarget = None, loop: bool = False, args = (), kwargs = {}):
		"""
		Create a thread with a name

		:param threadName str: The name of the thread
		:param threadTarget function: The target function to call
		:param loop bool: Whether the thread should loop
		:param args tuple: Arguments for the thread
		:param kwargs dict: Keyword arguments for the thread

		:returns SimpleThread: The thread created
		"""
		self.closeThread(threadName) # Try to close a thread by the same name of the one we're creating
		T = SimpleThread(threadTarget, loop = loop, *args, **kwargs) # Create instance of thread
		self._networkingThreads[threadName] = T # Save thread to list of threads
		return T # Return the thread

	def closeThread(self, threadName: str = None):
		"""
		Tries to close a thread by a name

		:param threadName str: The name of the thread you want to close

		:returns bool: If the thread was found
		"""
		try: # Try-except for finding thread
			self._networkingThreads[threadName].stop() # Try to find thread at key: threadName and stop it
			del self._networkingThreads[threadName] # Delete it from dictionary of networking threads
			return True # Return true that thread was found by that name, doesn't mean thread has been terminated
		except KeyError: return False # Return false if thread wasn't found (KeyError in dictionary of networking threads)

	def spawnProtocol(self, recipient: TAddress = None, timeout = None, protocolClass = None, args = (), kwargs = {}):
		proto = protocolClass(*args, **kwargs)
		recip = str(recipient)
		try: self._activeProtocols[recip].append(proto)
		except KeyError: self._activeProtocols[recip] = [proto]
		if type(timeout) == int: SimpleThread(target = self._threadTimeout, loop = False,
			args=(recip, proto, timeout)).start()
		return proto

	def getSpawnedProtocol(self, recipient: TAddress = None, protocolClass = None):
		recip = str(recipient)
		try: self._activeProtocols[recip]
		except KeyError: return None
		for spawnedProtocol in self._activeProtocols[recip]:
			if spawnedProtocol.__class__.__name__.upper() == protocolClass.__name__.upper():
				return spawnedProtocol
		return None

	def invalidateProtocol(self, recipient: TAddress = None, protocolClass = None):
		recip = str(recipient)
		try: self._activeProtocols[recip]
		except KeyError: return -1 # Unable to find recipient
		for proto in self._activeProtocols[recip]:
			if proto.__class__.__name__.upper() == protocolClass.__class__.__name__.upper():
				del self._activeProtocols[recip][self._activeProtocols[recip].index(proto)]
				return 1 # Deleted a protocol instance
		return 0 # No work was done

	def _threadTimeout(self, recipient: str = None, proto = None, timeout: float = 5):
		time.sleep(timeout)
		self.invalidateProtocol(recipient, proto)

	def _broadcastReceive(self):
		if self._broadcastSocket.closed():
			self._broadcastReceiveThread.stop()
			return
		addr, data = self._broadcastSocket.receiveData()
		if data is None or not len(data): return
		self.broadcastReceive(addr, data)

	def _generalReceive(self):
		if self._generalSocket.closed():
			self._generalReceiveThread.stop()
			return
		addr, data = self._generalSocket.receiveData()
		if data is None or not len(data): return
		self.generalReceive(addr, data)

	def broadcastReceive(self, addr: TAddress = None, data: str = None): raise NotImplementedError()
	def generalReceive(self, addr: TAddress = None, data: str = None): raise NotImplementedError()

class TServer(TNetworkable):

	def __init__(self):
		super().__init__(True, "192.168.6.1")
		self.expectedClients = TClient.Clients
		self._clientsGot = []
		self._broadcastProtoSaved = super().spawnProtocol(self._broadcastSocket._addr, None, Broadcast_IP, args = (0,))

	def startBroadcasting(self):
		t = super().spawnThread("Broadcasting", self._broadcastThread, True)
		t.start()

	def _broadcastThread(self):
		self._broadcastProtoSaved._step = 0
		self._broadcastProtoSaved.step(self._broadcastSocket, self._broadcastSocket._addr)
		time.sleep(5)

	def broadcastReceive(self, addr: TAddress = None, data: str = None):
		hndl = self._protocolHandler.incomingPacket(data, addr)
		if hndl[0] == 2:
			super().closeThread("Broadcasting")
			super().invalidateProtocol(str(self._broadcastSocket._addr), Broadcast_IP)
			self._broadcastSocket.close()

	def generalReceive(self, addr: TAddress = None, data: str = None):
		def threading(self):
			hndl = self._protocolHandler.incomingPacket(data, addr)
			if hndl[0] == 2:
				super().invalidateProtocol(addr ,hndl[1])
		if not (addr.addr[0] in self._clientsGot): return
		SimpleThread(threading, False, args=(self,)).start()

class TClient(TNetworkable):

	Clients = 0

	def __init__(self):
		TClient.Clients += 1
		super().__init__(False, "192.168.6." + str(TClient.Clients + 1))
		self._serversIP = None

	def keyExchange(self):
		ex = super().spawnProtocol(self._serversIP, None, Key_Exchange, args = (0,))
		clientRSA = RSA(True)
		ex.keys[1] = clientRSA
		ex.step(self._generalSocket, self._serversIP)

	def broadcastReceive(self, addr: TAddress = None, data: str = None):
		hndl = self._protocolHandler.incomingPacket(data, addr)
		if hndl[0] == 2:
			super().invalidateProtocol(str(self._broadcastSocket._addr), Broadcast_IP)
			self._broadcastSocket.close()
			self._serversIP = TAddress(self._serversIP, TPorts.SEND_RECEIVE)
			#self.keyExchange() <- Thread wouldn't normally be needed!
			SimpleThread(self.keyExchange, False, (), {}).start()

	def generalReceive(self, addr: TAddress = None, data: str = None):
		if addr.addr[0] != self._serversIP.addr[0]: return
		hndl = self._protocolHandler.incomingPacket(data, addr)
		if hndl[0] == 2:
			super().invalidateProtocol(addr, hndl[1])

class ProtocolHandler:

	def __init__(self, isClient: bool = False, selfInstance: TNetworkable = None):
		self._isClient = isClient
		self._instanceOfOwner = selfInstance

	def incomingPacket(self, packet: str = None, sentBy: TAddress = None):
		if type(packet) != str or not Packet.isValidPacket(packet): return -2
		return self._handlePacket(Packet.fromString(packet), sentBy)

	def _handlePacket(self, packet: object = None, sentBy: TAddress = None):
		def _client_Broadcast_IP():
			spawned = self._instanceOfOwner.getSpawnedProtocol(sentBy, Broadcast_IP)
			wasSpawnedPreviously = not spawned is None
			if not wasSpawnedPreviously: spawned = self._instanceOfOwner.spawnProtocol(sentBy, 10, Broadcast_IP, args=(1,))
			if not spawned.isServersTurn(packet._step): return 0
			if not spawned.isProperPacket(packet): return 0
			if spawned._step != packet._step: return 0
			if packet._step == 1:
				ip = packet.getDataAt(0)
				if self._instanceOfOwner.isIP(ip):
					self._instanceOfOwner._serversIP = ip
			if packet._step == 3:
				maybeMyIP = packet.getDataAt(0)
				if maybeMyIP == self._instanceOfOwner._ip: return 2
				else:
					spawned._step = 1
					spawned.step(self._instanceOfOwner._broadcastSocket, sentBy)
					self._instanceOfOwner.invalidateProtocol(sentBy, Broadcast_IP)
			else: spawned.step(self._instanceOfOwner._broadcastSocket, sentBy)
			return 1

		def _server_Broadcast_IP():
			spawned = self._instanceOfOwner.getSpawnedProtocol(sentBy, Broadcast_IP)
			wasSpawnedPreviously = not spawned is None
			if not wasSpawnedPreviously: return 0
			if spawned.isServersTurn(packet._step): return 0
			if not spawned.isProperPacket(packet): return 0
			if spawned._step != packet._step: return 0
			if packet._step == 2:
				ip = packet.getDataAt(0)
				if self._instanceOfOwner.isIP(ip):
					if not ip in self._instanceOfOwner._clientsGot:
						self._instanceOfOwner._clientsGot.append(ip)
					spawned.step(self._instanceOfOwner._broadcastSocket, sentBy, ip)
				spawned._step = 2
			else: spawned.step(self._instanceOfOwner._broadcastSocket, sentBy)
			if len(self._instanceOfOwner._clientsGot) >= self._instanceOfOwner.expectedClients: return 2
			return 1

		def _client_Key_Exchange():
			spawned = self._instanceOfOwner.getSpawnedProtocol(sentBy, Key_Exchange)
			wasSpawnedPreviously = not spawned is None
			if not wasSpawnedPreviously: return 0
			if not spawned.isServersTurn(packet._step): return 0
			if not spawned.isProperPacket(packet): return 0
			if spawned._step != packet._step: return 0
			if packet._step == 2:
				serverPubKey = RSA.addExtraDetailToKey(packet.getDataAt(0), True)
				spawned.keys[0] = RSA.new(False, serverPubKey)
				spawned.createAESKey()
			if packet._step == 4:
				spawned.sessionIds[1] = spawned.keys[2].decrypt(packet.getDataAt(0))
				print(f"Server => Client ({self._instanceOfOwner._ip}): New UUID is {spawned.sessionIds[1]}")
				spawned.step(self._instanceOfOwner._generalSocket, sentBy)
				return 2
			spawned.step(self._instanceOfOwner._generalSocket, sentBy)
			return 1

		def _server_Key_Exchange():
			spawned = self._instanceOfOwner.getSpawnedProtocol(sentBy, Key_Exchange)
			wasSpawnedPreviously = not spawned is None
			if not wasSpawnedPreviously:
				spawned = self._instanceOfOwner.spawnProtocol(sentBy, 60, Key_Exchange, args=(1,))
				serverRSA = RSA(False)
				spawned.keys[0] = serverRSA
			if spawned.isServersTurn(packet._step): return 0
			if not spawned.isProperPacket(packet): return 0
			if spawned._step != packet._step: return 0
			if packet._step == 3:
				decryptedClientKey = spawned.keys[0].decrypt(packet.getDataAt(0))
				key = RSA.addExtraDetailToKey(decryptedClientKey, False)
				spawned.keys[1] = RSA.new(True, key)
				spawned.createAESKey()
			if packet._step == 5:
				spawned.sessionIds[0] = spawned.keys[2].decrypt(packet.getDataAt(0))
				print(f"Client ({sentBy.addr[0]}) => Server: New UUID is {spawned.sessionIds[0]}")
				return 2
			else:
				spawned.step(self._instanceOfOwner._generalSocket, sentBy)
				return 1

		packetProto = packet._protocol
		if packetProto == "BROADCAST_IP":
			if self._isClient: return (_client_Broadcast_IP(), Broadcast_IP)
			else: return (_server_Broadcast_IP(), Broadcast_IP)
		elif packetProto == "KEY_EXCHANGE":
			if self._isClient: return (_client_Key_Exchange(), Key_Exchange)
			else: return (_server_Key_Exchange(), Key_Exchange)
		else: return (-1, None)

class Protocol:

	@staticmethod
	def allProtocols(): return [_class.__name__.upper() for _class in Protocol.__subclasses__()]

	@staticmethod
	def protocolClassNameFromID(id: int = 0):
		protos = Protocol.allProtocols()
		if id < 0 or id > len(protos): return None
		return protos[id]

	@staticmethod
	def protocolClassFromID(id: int = 0):
		protos = Protocol.__subclasses__()
		if id < 0 or id > len(protos): return None
		return protos[id]

	@staticmethod
	def idFromProtocolName(name: str = None):
		if name is None or type(name) != str or not (name.upper() in Protocol.allProtocols()): return -1
		return Protocol.allProtocols().index(name)

	def __init__(self, step: int = 0, totalSteps: int = 0, serverSteps: int = 0, packetMethods: list = None, *args, **kwargs):
		self._step = step
		self._packets = packetMethods
		self._totalSteps = totalSteps
		self._serverSteps = serverSteps

	def isServersTurn(self, step: int = 0): return step in self._serverSteps

	def isProperPacket(self, pkt: object = None):
		try: return pkt._method in self._packets[pkt._step - 1]
		except IndexError: return False

	def step(self, sender: TSocket = None, receiver: TAddress = None, *args, **kwargs): raise NotImplementedError()

class Broadcast_IP(Protocol):

	def __init__(self, step: int = 0):
		super().__init__(step, 3, (1, 3), (("DATA",), ("CONFIRM",), ("AGREE",)))

	def step(self, sender: TSocket = None, receiver: TAddress = None, confirming: str = "(Unknown)"):
		protoName = self.__class__.__name__.upper()
		self._step += 1
		if self._step == 1: # Server
			Packet("DATA", protoName, self._step).addData(sender._spawnedFrom).finalize(sender, receiver)
		elif self._step == 2: # Client
			Packet("CONFIRM", protoName, self._step).addData(sender._spawnedFrom).finalize(sender, receiver)
		elif self._step == 3: # Server
			Packet("AGREE", protoName, self._step).addData(confirming).finalize(sender, receiver)
		self._step += 1

class Key_Exchange(Protocol):

	def __init__(self, step: int = 0):
		self.keys = [None, None, None]
		# 0 = Server RSA, 1 = Client RSA, 2 = Shared AES
		self.previousIds = ["", ""]
		self.sessionIds = ["", ""]
		# 0 = Server uuid, Client uuid
		super().__init__(step, 0, (2, 4), (("QUERY_DATA",), ("QUERY_RESPONSE",), ("DATA",), ("DATA",), ("DATA",)))

	def session(self, key):
		seed = sha256((key.privKey() + str(rand.randint(-(2 ** 64 - 1), 2 ** 64 - 1))).encode("utf-8")).digest().hex()
		rand.shuffle(shuffle := [c for c in seed])
		return "".join([rand.choice(shuffle) for i in range(64)])

	def aesKey(self):
		return sha256((self.keys[0].pubKey() + self.keys[1].privKey() + self.previousIds[0] + self.previousIds[1]).encode("utf-8")).digest()

	def createAESKey(self):
		self.keys[2] = AES(self.aesKey())

	def step(self, sender: TSocket = None, receiver: TAddress = None):
		protoName = self.__class__.__name__.upper()
		self._step += 1
		if self._step == 1: # Client
			Packet("QUERY_DATA", protoName, self._step).finalize(sender, receiver)
		elif self._step == 2: # Server
			# Server get's their own public key (0)
			Packet("QUERY_RESPONSE", protoName, self._step).addData(self.keys[0].pubKey()).finalize(sender, receiver)
		elif self._step == 3: # Client
			# Client encrypts their private key (1) with the server's public key (0)
			Packet("DATA", protoName, self._step).addData(self.keys[0].encrypt(self.keys[1].privKey())).finalize(sender, receiver)
		elif self._step == 4: # Server
			self.sessionIds[1] = self.session(self.keys[1])
			data = self.keys[2].encrypt(self.sessionIds[1])
			Packet("DATA", protoName, self._step).addData(data).finalize(sender, receiver)
		elif self._step == 5: # Client
			self.sessionIds[0] = self.session(self.keys[0])
			data = self.keys[2].encrypt(self.sessionIds[0])
			Packet("DATA", protoName, self._step).addData(data).finalize(sender, receiver)
		self._step += 1

class Packet:

	Methods = {
		"ERROR":         -1,
		"CONFIRM":        1,
		"AGREE":          2,
		"DISAGREE":       3,
		"QUERY_DATA":     4,
		"QUERY_RESPONSE": 5,
		"DATA":           6
	}

	@staticmethod
	def methodFromString(mtdName: str = None):
		if mtdName is None or len(mtdName) == 0 or not (mtdName in Packet.Methods.keys()): return -1
		return Packet.Methods[mtdName]

	@staticmethod
	def stringFromMethod(mtdID: int = None):
		if mtdID is None or mtdID < -1 or mtdID > len(Packet.Methods.keys()) - 1: return "ERROR"
		for key, val in Packet.Methods.items():
			if val == mtdID: return key
		return "ERROR"

	@staticmethod
	def fromString(packet: str = None):
		if packet is None or len(packet) < 8: return None
		mtd = Packet.stringFromMethod(int(packet[:2]))
		protoID = int(packet[2:4])
		step = int(packet[4:6])
		numberOfDataPoints = int(packet[6:8])
		packetInstance = Packet(mtd, Protocol.protocolClassNameFromID(protoID), step)
		packetInstance._packetString = packet
		offset = 0
		for i in range(numberOfDataPoints):
			del i
			dataLength = int(packet[8 + offset: 12 + offset]) + 1
			rawData = packet[12 + offset: 12 + offset + dataLength]
			data = base64.b64decode(rawData)
			try:
				decodedUTF8 = data.decode("utf-8")
				data = decodedUTF8
			except: pass
			packetInstance.addData(data)
			offset += 4 + dataLength
		return packetInstance

	@staticmethod
	def isValidPacket(packet: str = None):
		return type(Packet.fromString(packet)) == Packet

	def __init__(self, method: str = None, protocolName: str = None, step: int = 0):
		self._method = method
		self._protocol = protocolName
		self._step = step
		self._packetString = ""
		self._data = []

	def __str__(self):
		return f"Method: {self._method}, Protocol: {self._protocol}, Step: {self._step}\
, Current Packet String: \n{self._packetString}, Data: {self._data}"

	def addData(self, data: str = None):
		if data is None or len(data) == 0: return self
		if len(data) > 10000:
			input("Data limit hit!")
			return self
		self._data.append(data)
		return self

	def build(self):
		opt = lambda length, value: "0" * (length - len(str(value))) + str(value)
		data = "" + opt(2, Packet.methodFromString(self._method)) + opt(2, Protocol.idFromProtocolName(self._protocol)) + opt(2, self._step) + opt(2, len(self._data))
		for dataPoint in self._data:
			if type(dataPoint) == str: dataPoint = dataPoint.encode("utf-8")
			encodedData = base64.b64encode(dataPoint).decode("utf-8")
			data += opt(4, len(encodedData) - 1) + encodedData
		self._packetString = data
		return self

	def getDataAt(self, index: int = 0):
		if index < 0: index = 0
		if index >= len(self._data): index = len(self._data) - 1
		if index == -1: return None
		return self._data[index]

	def send(self, socket: TSocket = None, toSendItTo: TAddress = None):
		if socket is None or self._packetString is None or len(self._packetString) == 0: return
		socket.sendData(toSendItTo, self._packetString)
		return self

	def finalize(self, socket: TSocket = None, toSendItTo: TAddress = None):
		self.build().send(socket, toSendItTo)
