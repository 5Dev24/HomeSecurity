from .crypt import AES, RSA
from Crypto.Random import random as rand
from hashlib import sha256
from threading import Thread, Timer, Event, current_thread as currThread, main_thread as mainThread
from enum import Enum
from .logging import Log, LogType
from uuid import getnode
import time, string, re, traceback, sys, base64, binascii, datetime

Characters = string.punctuation + string.digits + string.ascii_letters
"""
All of the punctuation, digits, and letters of english
"""

def MyMac():
	raw = getnode()[2:]
	return ":".join([raw[i:i+2] for i in range(0, len(raw), 2)])

class Ports:
	"""
	Theoretical ports used in simulation
	"""

	SEND_RECEIVE = 32001 # Normal sending and receiving data
	"""
	Port used for sending and receiving data for regular protocols that don't need to be done over broadcasting
	"""

	SERVER_BROADCAST = 23002 # For send and receiveing data from a broadcast
	"""
	Port used for only sending and receiving data for the Broadcast_IP protocol to find clients
	"""

class SimpleThread:
	"""
	My own implementation of threading made simple

	Still uses a Thread object for underlying threading but has better control

	Adds for looping threads to continuously call the target function
	"""

	def __init__(self, target = None, loop: bool = False, args = tuple(), kwargs = {}):
		"""
		Init

		Args:
			target (function): The function that will be called by the thread
			loop (bool): Should the function be continuously called
			args (tuple): Arguments to pass to the function
			kwargs (dict): Keyword arguments to pass to the function

		Attributes:
			_internalThread (Thread): The internal thread using to call the target thread
			_target (function): Function to call in internal thread
			_args (tuple, optional): Arguments to pass to target, default: empty tuple
			_kwargs (dict): Keyword arguments to pass to target, default: empty dictionary
			_loop (bool): If the thread should loop
			_running (bool): If the thread is running currently
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

		Returns:
			SimpleThread: self
		"""
		self._running = False # Set that thread isn't running
		return self # Return self

	def _internal(self):
		"""
		Internal threading method to call target function

		Returns:
			None
		"""
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

		Returns:
			SimpleThread: self
		"""
		if self._running: return self # If thread is already running, return self
		self._running = True # Set that thread is running
		self._internalThread.start() # Start internal thread
		return self # Return self

	def join(self, timeout: int = 5):
		"""
		Allows for thread to join internal thread

		Should not and cannot be called form main thread

		Args:
			timeout (int, optional): Number of seconds to wait before exiting thread join, default 5

		Returns:
			None
		"""
		if currThread() is mainThread(): # If function has been called from main thread
			print("An attempt was made to join a thread from the main python thread") # Debug info
			return # Exit function
		self._internalThread.join(timeout) # Wait for thread to terminal but added timeout

class Networkable:
	"""
	An object that uses networking (server and client)
	"""

	@staticmethod
	def isIP(ipaddr: str = None):
		"""
		Checks if a string is an ip (valid format)

		Args:
			ipaddr (str): Possible ip address

		Returns:
			bool: If it is an ip address or not
		"""
		if ipaddr is None or type(ipaddr) != str or not len(ipaddr): return False # If address is None type, isn't a string type, or is empty, return false
		return re.match("((\\.)*\\d{1,3}){4}", ipaddr) # Check if the string matches a normal IPv4 address' format

	def __init__(self, isServer: bool = False):
		"""
		Init

		Args:
			isServer (bool): Is instance a server
			fakeRealIP (str): Fake ip of server or client

		Attributes:
			_isServer (bool): If this is a server or not
			_ip (str): The ip address of this networkable
			_broadcastSocket (socket.socket): The broadcasting socket
			_broadcastReceiveThread (SimpleThread): Thread for receiving data from the broadcasting socket
			_generalSocket (socket.socket): The general socket
			_generalReceiveThread (SimpleThread): Thread for receiving data from the general socket
			_networkingThreads (dict): All currently active networking threads
			_activeProtocols (dict): All currently active protocols
			_protocolHandler (ProtocolHandler): Handler for packets for protocols
			MacAddress (str): The devices MAC address
		"""
		self._isServer = isServer # Save if server
		self._broadcastSocket = None # Create broadcasting socket
		self._broadcastReceiveThread = SimpleThread(self._broadcastReceive, True).start() # Create broadcasting listening thread
		self._generalSocket = None # Create general data receiving socket
		self._generalReceiveThread = SimpleThread(self._generalReceive, True).start() # Create general data listening thread
		self._networkingThreads = {} # Currently active networking threads {thread name: thread instance}
		self._activeProtocols = {} # Currently active protocol {"ip:port": [Protocol instance,]}
		self._protocolHandler = ProtocolHandler(self) # Create protocol handler

	@property
	def MacAddress(self):
		return MyMac()

	def spawnThread(self, threadName: str = None, threadTarget = None, loop: bool = False, args = tuple(), kwargs = {}):
		"""
		Create a thread with a name

		Args:
			threadName (str): The name of the thread
			threadTarget (function): The target function to call
			loop (bool): Whether the thread should loop
			args (tuple): Arguments for the thread
			kwargs (dict): Keyword arguments for the thread

		Returns:
			SimpleThread: The thread created
		"""
		self.closeThread(threadName) # Try to close a thread by the same name of the one we're creating
		T = SimpleThread(threadTarget, loop = loop, *args, **kwargs) # Create instance of thread
		self._networkingThreads[threadName] = T # Save thread to list of threads
		return T # Return the thread

	def closeThread(self, threadName: str = None):
		"""
		Tries to close a thread by a name

		Args:
			threadName (str): The name of the thread you want to close

		Returns:
			bool: If the thread was found
		"""
		try: # Try-except for finding thread
			self._networkingThreads[threadName].stop() # Try to find thread at key: threadName and stop it
			del self._networkingThreads[threadName] # Delete it from dictionary of networking threads
			return True # Return true that thread was found by that name, doesn't mean thread has been terminated
		except KeyError: return False # Return false if thread wasn't found (KeyError in dictionary of networking threads)

	def spawnProtocol(self, recipient: str = None, timeout: int = None, protocolClass = None, args = tuple(), kwargs = {}):
		"""
		Spawns a protocol and saves it as being created by the recipient

		Args:
			recipient (str): Who the other party is in the protocol
			timeout (int): Timeout to invalidate the protocol after timeout seconds
			protocolClass (type): The class of protocol to create instance of
			args (tuple): Arguments for protocol
			kwargs (dict): Keyword arguments for protocol

		Returns:
			Protocol: The protocol created
		"""
		proto = protocolClass(*args, **kwargs) # Create instance of class with args and kwargs
		try: self._activeProtocols[recipient].append(proto) # Try to add the protocol as part of the protocol list that this recipient has spawned
		except KeyError: self._activeProtocols[recipient] = [proto] # If no key exists for the recipient, create new one with list only containing the new protocol instance
		if type(timeout) == int: SimpleThread(target = self._threadTimeout, loop = False,
			args=(recipient, proto, timeout)).start() # If the timeout is an int, create a simple thread to invalidate it after timeout seconds
		return proto # Return instance of protocol

	def getSpawnedProtocol(self, recipient: str = None, protocolClass = None):
		"""
		Gets a protocol that was created by the recipient

		Args:
			recipient (str): The address that caused the spawning of the protocol
			protocolClass (type): The class of the protocol

		Returns:
			Protocol: The protocol if it was found, else None
		"""
		try: self._activeProtocols[recipient] # Try to lookup the recipient in the dictionary of active protocols
		except KeyError: return None # If a KeyError was thrown from the key not existing in the dictionary then, return None
		for spawnedProtocol in self._activeProtocols[recipient]: # Loop through each active protocol as spawnedProtocol
			if spawnedProtocol.__class__.__name__.upper() == protocolClass.__name__.upper(): # If class names match
				return spawnedProtocol # Return the found protocol
		return None # Return None as no protocol was found

	def invalidateProtocol(self, recipient: str = None, protocolClass = None):
		"""
		Marks a protocol as invalid and will remove it from use

		Args:
			recipient (str): The address that caused the intial spawning of the protocol
			protocolClass (type): The class of the protocol to invalidate

		Returns:
			int: Return exit code
		"""
		"""
		Exit Codes:
		   -1 -> The recipient wasn't found to have any protocols registered (Good)
		    0 -> The recipient has created protocols but just not the one we're lookin' for (Good)
		    1 -> The recipient had created the protocl(s) we were lookin' for and they/it were/was removed (Good)
		"""
		try: self._activeProtocols[recipient] # Try to lookup the value of the key: recip, in the dictionary of active protocols
		except KeyError: return -1 # Unable to find recipient, return -1 as the recipient wasn't found
		outCode = 0 # Returned to determine if work was done
		for proto in self._activeProtocols[recipient]: # Loop through each protocol for a recipient as proto
			if proto.__class__.__name__.upper() == protocolClass.__class__.__name__.upper(): # If class names match
				self._activeProtocols[recipient].remove(proto) # Remove protocol from list of protocols
				outCode += 1 # Increase output code by 1 as a protocol was invalidated
		if outCode > 0: return 1 # If the output code is greater than 0 then return that at least 1 protocol was invalidated
		else: return 0 # Return that no work was done (0)

	def _threadTimeout(self, recipient: str = None, proto = None, timeout: float = 5):
		"""
		An internal method to be put into a thread for automatically invalidating protocol after a time period

		Should not and cannot be called from main thread

		Returns:
			int: Return exit code
		"""
		"""
		Exit Codes:
		   -2 -> Fucntion was called from main thread (Bad)

		Refer to invalidateProtocol's exit codes for any other exit codes for this function
		"""
		if currThread() is mainThread(): # If function has been called from main thread
			print("An attempt was made to join a thread from the main python thread") # Debug info
			return -2 # Exit function, return -2 error
		time.sleep(timeout) # Sleep for timeout seconds
		self.invalidateProtocol(recipient, proto) # Invalidate the protocol

	def _broadcastReceive(self):
		"""
		An internal function that listens for data being sent to the broadcasting socket of the networkable

		Returns:
			None
		"""
		if self._broadcastSocket.closed(): # If socket is closed
			self._broadcastReceiveThread.stop() # Stop this thread
			return # Exit function
		addr, data = self._broadcastSocket.receiveData() # Wait until data is received
		if data is None or not len(data): return # If data is invalid, exit function
		self.broadcastReceive(addr, data) # Call, hopefully implemented, child function

	def _generalReceive(self):
		"""
		An internal function that listens for data being sent to the general socket of the networkable

		Returns:
			None
		"""
		if self._generalSocket.closed(): # If socket is closed
			self._generalReceiveThread.stop() # Stop this thread
			return # Exit function
		addr, data = self._generalSocket.receiveData() # Wait until data is received
		if data is None or not len(data): return # If data is invalid, exit function
		self.generalReceive(addr, data) # Call, hopefully impelemented, child function

	def broadcastReceive(self, addr: str = None, data: str = None):
		"""
		A function that child classes must implement

		It is called when data is received on the broadcasting socket of the networkable

		Args:
			addr (str): Sender of data
			data (str): The data sent

		Returns:
			None

		Raises:
			NotImplementedError: Raised when function ins't implemented
		"""
		raise NotImplementedError() # Raise error as function wasn't implemented by child class

	def generalReceive(self, addr: str = None, data: str = None):
		"""
		A function that child classes must implement
		It is called when data is received on the general receiving socket of the networkable

		Args:
			addr (str): Sender of data
			data (str): The data sent

		Returns:
			None

		Raises:
			NotImplementedError: Raised when function isn't implemented
		"""
		raise NotImplementedError() # Raise error as function wasn't implemented by child class

class Server(Networkable):
	"""
	The server object

	Handles server side related things
	"""

	def __init__(self, clients: int = 0):
		"""
		Init

		Args:
			clients (int): Number of clients to wait for in Broadcast_IP protocol

		Attributes:
			expectedClients (int): Number of clients expected
			_clientsGot (list): List of ip addresses from clients
			_broadcastProtoSaved (Broadcast_IP): Broadcast_IP protocol instance
		"""
		super().__init__(True) # Tell networking that I am a server
		self.expectedClients = clients # Set expected clients to be the current number of created ones
		self._clientsGot = [] # List of clients gotten from Broadcast_IP protocol
		self._broadcastProtoSaved = super().spawnProtocol("<broadcast>", None, Broadcast_IP, args = (0,)) # Broadcast ip protocol instance

	def startBroadcasting(self):
		"""
		Starts the broadcasting protocol thread

		Returns:
			None
		"""
		t = super().spawnThread("Broadcasting", self._broadcastThread, True) # Create the thread
		t.start() # Start the thread

	def _broadcastThread(self):
		"""
		An internal method to reset the broadcast ip protoocl step and start over

		It waits 5 seconds between each one of these calls

		Returns:
			None
		"""
		self._broadcastProtoSaved._step = 0 # Sets the step to be 0 (will be incremented to 1)
		self._broadcastProtoSaved.step("<broadcast>") # Call step function
		time.sleep(5) # Wait 5 seconds

	def broadcastReceive(self, addr: str = None, data: str = None):
		"""
		Implementation from parent class to handle data received from the broadcasting socket

		Args:
			addr (str): Sender address
			data (str): Data sent

		Returns:
			None
		"""
		hndl = self._protocolHandler.incomingPacket(data, addr) # Call the packet handler to handle the packet
		if hndl[0] == 2: # If packet handler returned 2 (see Exit Codes)
			super().closeThread("Broadcasting") # Close broadcasting thread
			super().invalidateProtocol("<broadcast>", Broadcast_IP) # Invalidate Broadcast_IP protocol
			self._broadcastSocket.close() # Close broadcasting socket

	def generalReceive(self, addr: str = None, data: str = None):
		"""
		Implementation from parent class to handled data received from the general receiving socket

		Args:
			addr (str): Sender address
			data (str): Data received

		Returns:
			None
		"""
		def threading(self):
			"""
			Thread for handling requests so that no request is missed
			(A queue could be implemented to handle all packets in order instead of having to open new threads)

			Returns:
				None
			"""
			hndl = self._protocolHandler.incomingPacket(data, addr) # Call the packet handler to handle the incoming packet
			if hndl[0] == 2: # If packet handler returned 2 (see Exit codes)
				super().invalidateProtocol(addr ,hndl[1]) # Invalidate the protocol
		if not (addr.addr[0] in self._clientsGot): return # If address isn't from the found client list then exit function
		SimpleThread(threading, False, args=(self,)).start() # Create threaded handler and start thread

class Client(Networkable):
	"""
	The client object

	Handles client side related things
	"""

	def __init__(self):
		"""
		Init

		Attributes:
			_serversIP (str): The server's ip address
		"""
		super().__init__(False) # Tell parent that you're a client and your ip
		self._serversIP = None # Server's ip address, gotten after Broadcast_IP finishes

	def keyExchange(self):
		"""
		Starts the Key_Exchange protocol after server has registered you as a client

		Returns:
			None
		"""
		ex = super().spawnProtocol(self._serversIP, None, Key_Exchange, args = (0,)) # Create an instance of the Key_Exchange protocol
		clientRSA = RSA(True) # Generate a new rsa key (client)
		ex.keys[1] = clientRSA # Save rsa key to key list in protocol
		ex.step(self._serversIP) # Call first step in key exchange

	def broadcastReceive(self, addr: str = None, data: str = None):
		"""
		Implemented function from parent class to handle packets on broadcasting socket

		Args:
			addr (str): Sender's address
			data (str): Data sender sent

		Returns:
			None
		"""
		hndl = self._protocolHandler.incomingPacket(data, addr) # Handle packet
		if hndl[0] == 2: # If exit code is 2 (see Exit codes)
			super().invalidateProtocol("<broadcast>", Broadcast_IP) # Invalidate the broadcast ip protocol
			self._broadcastSocket.close() # Close the broadcasting socket
			self._serversIP = self._serversIP # Set server's ip to be a TAddress
			#self.keyExchange() <- Thread wouldn't normally be needed!
			SimpleThread(self.keyExchange, False, (), {}).start() # Start key exchange protocol

	def generalReceive(self, addr: str = None, data: str = None):
		"""
		Implemented function from parent class to handle general packets

		Args:
			addr (TAddress): Sender's address
			data (str): Data sent

		Returns:
			None
		"""
		if addr.addr[0] != self._serversIP.addr[0]: return # If address isn't server's, exit function
		hndl = self._protocolHandler.incomingPacket(data, addr) # Handle packet
		if hndl[0] == 2: # If exit code 2 is returned (see Exit codes)
			super().invalidateProtocol(addr, hndl[1]) # Invalidate the protocol

class SessionID:

	@staticmethod
	def Now():
		return int(datetime.datetime.utcnow().timestamp() * 1000)

	def __init__(self, id: str = "", timeCreated: int = 0):
		if not timeCreated: timeCreated = SessionID.Now()
		self.id = id
		self.timeCreated = timeCreated

	@property
	def expired(self):
		return SessionID.Now() - self.timeCreated > 600 * 1000 # Session expires after 600 seconds (10 minutes)

class ProtocolHandler:
	"""
	Handles incoming packets

	Verifies if a packet is legit and if steps should be done because of it
	"""

	def __init__(self, selfInstance: Networkable = None):
		"""
		Init

		Args:
			selfInstance (Networkable): The instance of a client or server

		Attributes:
			_instanceOfOwner (Networkable): The instance of the object that created this object
		"""
		self._instanceOfOwner = selfInstance # Save owner

	def incomingPacket(self, packet: str = None, sentBy: str = None):
		"""
		Handles incoming packets

		Args:
			packet (str): The raw packet
			sentBy (str): The address to send data back to

		Returns:
			int: An exit code
		"""
		"""
		Exit Codes:
		   -2 -> Packet was invalid or packet supplied wasn't of type string (Bad)
		   -1 -> No method currently exists to handle that protocol (Bad)
		    0 -> Failed checks so no step was done (Bad)
		    1 -> Execution went fine but protocol isn't finished (Good)
			2 -> Execution went fine and protocl has finished (Good)
		"""
		if type(packet) != str or not Packet.isValidPacket(packet): return -2 # If packet isn't a string or isn't a valid packet, return -2
		return self._handlePacket(Packet.fromString(packet), sentBy) # Return exit code from the internal handler returns

	def _handlePacket(self, packet: object = None, sentBy: str = None):
		"""
		Internal packet handler

		Args:
			packet (object): The packet object
			sentBy (str): the address to send data back to

		Returns:
			int: An exit code (see handlePacket's exit codes for reference)
		"""
		def _client_Broadcast_IP():
			"""
			Internal function for handling a Broadcast_IP packet for clients

			Returns:
				int: An exit code (see handlePacket's exit codes for reference)
			"""
			spawned = self._instanceOfOwner.getSpawnedProtocol(sentBy, Broadcast_IP) # Get the spawned protocol
			wasSpawnedPreviously = not spawned is None # Was the protocol already created (is it not None when got)
			if not wasSpawnedPreviously: # If protocl wasn't previously spawned
				spawned = self._instanceOfOwner.spawnProtocol(sentBy, 10, Broadcast_IP, args=(1,)) # Create instance of Broadcast_IP that timesout in 10 seconds
			if not spawned.isServersTurn(packet._step): return 0 # If the packet isn't from the server's turn, return 0
			if not spawned.isProperPacket(packet): return 0 # If the packet's method isn't one that should be used, return 0
			if spawned._step != packet._step: return 0 # If the steps of the packet and protocol object don't align, return 0
			if packet._step == 1: # If the packet's step is 1
				self._instanceOfOwner._serversIP = sentBy # Save the server's ip to be the sender of the packet
			if packet._step == 3: # If the packet's step is 3
				maybeMyIP = packet.getDataAt(0) # Get first data point
				if maybeMyIP == self._instanceOfOwner._ip: return 2 # If it is my ip, return 2
				else:
					self._instanceOfOwner.invalidateProtocol(sentBy, Broadcast_IP) # Invalid protocol but don't return 2 as protocol didn't finish, just failed
			else: spawned.step(sentBy) # If step isn't 3, call step function
			return 1 # Return that execution went well

		def _server_Broadcast_IP():
			"""
			Internal function for handling a Broadcast_IP packet for a server

			Returns:
				int: An exit code (see handlePacket's exit codes for reference)
			"""
			spawned = self._instanceOfOwner.getSpawnedProtocol(sentBy, Broadcast_IP) # Get the spawned protocol
			if spawned is None: return 0 # If Broadcast_IP protocol instance wasn't previously spawned, return 0
			if spawned.isServersTurn(packet._step): return 0 # If the packet isn't from the client's turn, return 0
			if not spawned.isProperPacket(packet): return 0 # If the packet's method isn't one that should be used, return 0
			if spawned._step != packet._step: return 0 # If steps of the packet and protocol instance don't align, return 0
			if packet._step == 2: # If packet step is 2
				if sentBy not in self._instanceOfOwner._clientsGot: # If ip isn't in the list of clients gotten so far
					self._instanceOfOwner._clientsGot.append(sentBy) # Added ip to list of clients
				spawned.step(sentBy) # Call step function and confirm an ip
				spawned._step = 2 # Reset step to 2 to allow for another client to start confirm process
			else: spawned.step(sentBy) # Call step function
			if len(self._instanceOfOwner._clientsGot) >= self._instanceOfOwner.expectedClients: return 2 # Return 2 when number of client gotten is greater than or equal to the number of expected clients
			return 1 # Return that execution went well

		def _client_Key_Exchange():
			"""
			Internal function for handling a Key_Exchange packet for clients

			Returns:
				int: An exit code (see handlePacket's exit codes for reference)
			"""
			spawned = self._instanceOfOwner.getSpawnedProtocol(sentBy, Key_Exchange) # Get the spawned protocol
			if spawned is None: return 0 # If Key_Exchange protocol instance wasn't previously spawned, return 0
			if not spawned.isServersTurn(packet._step): return 0 # If the packet isn't from the server's turn, return 0
			if not spawned.isProperPacket(packet): return 0 # If the packet's method isn't one that should be used, return 0
			if spawned._step != packet._step: return 0 # If steps of the packet and protocol instance don't align, return 0
			if packet._step == 2: # If packet step is 2
				firstDataPoint = packet.getDataAt(0) # Get data at position 1
				if firstDataPoint is None: return 0 # If data is None, return 0
				serverPubKey = RSA.addExtraDetailToKey(firstDataPoint, True) # Add back detail to the key
				spawned.keys[0] = RSA.new(False, serverPubKey) # Create new instance of RSA from key and save in protocol
				spawned.createAESKey() # Create the AES key for cryptography
			if packet._step == 4: # If packet step is 4
				firstDataPoint = packet.getDataAt(0) # Get data at position 1
				if firstDataPoint is None: return 0 # If data is None, return 0
				spawned.sessionIds[1] = spawned.keys[2].decrypt(firstDataPoint) # Decrypt data from packet and save in session ids
				spawned.step(sentBy) # Call step function
				Log(LogType.Info, f"Client ({self._instanceOfOwner.MacAddress}) is done with Key Exchange ({spawned.sessionIds[1]})", False).post()
				return 2 # Return that the protocol has finished
			spawned.step(sentBy) # Call step function
			return 1 # Return that execution went well

		def _server_Key_Exchange():
			"""
			Internal function for handling a Key_Exchange packet for a server

			Returns:
				int: An exit code (see handlePacket's exit codes for reference)
			"""
			spawned = self._instanceOfOwner.getSpawnedProtocol(sentBy, Key_Exchange) # Get the spawned protocol
			if spawned is None: # If Key_Exchange protocol wasn't gotten
				spawned = self._instanceOfOwner.spawnProtocol(sentBy, 60, Key_Exchange, args=(1,)) # Spawn instance of Key_Exchange
				serverRSA = RSA(False) # Create instance of RSA for server
				spawned.keys[0] = serverRSA # Save RSA instance in protocol
			if spawned.isServersTurn(packet._step): return 0 # If the packet was from a server's turn, return 0
			if not spawned.isProperPacket(packet): return 0 # If the packet's method isn't one that should be used, return 0
			if spawned._step != packet._step: return 0 # If protocol step and packet's step don't align, return 0
			if packet._step == 3: # If packet step is 3
				firstDataPoint = packet.getDataAt(0) # Get data at position 1
				if firstDataPoint is None: return 0 # If data at position 1 is None, return 0
				decryptedClientKey = spawned.keys[0].decrypt(firstDataPoint) # Decrypt data point as RSA key
				key = RSA.addExtraDetailToKey(decryptedClientKey, False) # Added back details to key
				spawned.keys[1] = RSA.new(True, key) # Save key to protocol
				spawned.createAESKey() # Create AES key for cryptography
			if packet._step == 5: # If packet step is 5
				firstDataPoint = packet.getDataAt(0) # Get data at position 1
				if firstDataPoint is None: return 0 # If data is None, return 0
				spawned.sessionIds[0] = spawned.keys[2].decrypt(firstDataPoint) # Decrypt data as a session key
				Log(LogType.Info, f"Server ({self._instanceOfOwner.MacAddress}) is done with Key Exchange with {sentBy} ({spawned.sessionIds[0]})", False).post()
				return 2 # Return that the protocol has finished
			else:
				spawned.step(sentBy) # Call step function
				return 1 # Return that execution went well

		if type(packet) is not Packet: return (0, None) # packet wasn't a Packet, exit 0
		packetProto = Protocol.protocolClassNameFromID(packet._protocol) # Get the packet's protocol
		isClient = not self._instanceOfOwner._isServer # Get if the owner is a client or not
		if packetProto == "BROADCAST_IP": # If the packet's protocol is BROADCAST_IP
			if isClient: return (_client_Broadcast_IP(), Broadcast_IP) # If it's the client, return the exit code from the client handle function and the protocol class
			else: return (_server_Broadcast_IP(), Broadcast_IP) # If it's the server, return the exit code from the server handle function and the protocol class
		elif packetProto == "KEY_EXCHANGE": # If the packet's protocol is KEY_EXCHANGE
			if isClient: return (_client_Key_Exchange(), Key_Exchange) # If it's the client, return the exit code from the client handle function and the protocol class
			else: return (_server_Key_Exchange(), Key_Exchange) # If it's the server, return the exit code from the server handle function and the protocol class
		else: return (-1, None) # No handle for the protocol of the packet so return -1

class Protocol:
	"""
	The parent class for all protocols
	"""

	@staticmethod
	def allProtocols():
		"""
		Gets all sub classes' names in all caps

		Returns:
			list: All sub classes' names
		"""
		return [_class.__name__.upper() for _class in Protocol.__subclasses__()] # Creates and returns a list of all sub classes' names made uppercase

	@staticmethod
	def protocolClassNameFromID(id: int = 0):
		"""
		Gets a class from an id

		Args:
			id (int): The id of the class

		Returns:
			class: The class of the protocol with id: id
		"""
		protos = Protocol.allProtocols() # Get all protocols
		if id < 0 or id > len(protos) - 1: return None # If id out of range/bounds, return None
		return protos[id] # Return protocol at index id

	def __init__(self, step: int = 0, serverSteps: tuple = tuple(), packetMethods: tuple = tuple()):
		"""
		Init

		Args:
			step (int): The current step of the protocol
			serverSteps (tuple): All of the steps belonging to the server
			packetMethods (tuple): All of the methods for each step

		Attributes:
			_step (int): The current step of the protocol
			_serverSteps (tuple): All of the steps belonging to the server
			_packets (tuple): All of the methods for each step
		"""
		self._step = step # Save protocol step
		self._serverSteps = serverSteps # Save server's steps
		self._packets = packetMethods # Save packet methods

	def isServersTurn(self, step: int = 0):
		"""
		Determines if a step is a server's step

		Args:
			step (int): The step to check

		Returns:
			bool: True if the step is a server step, false otherwise
		"""
		return step in self._serverSteps # If the step is within the server step list

	def isProperPacket(self, packet: object = None):
		"""
		Checks if a packet is of a correct method

		Args:
			packet (Packet): The packet object

		Returns:
			bool: True if the packet's method is one for its step, false otherwise
		"""
		method = Method.methodFromID(packet._method) # Get method from the enum
		if method is None: return False # If it wasn't found, return false
		try: return method in self._packets[packet._step - 1] # Tries to return if the packet's method is in the list of method for a given step
		except IndexError: return False # If a KeyError is raised, return false

	def step(self, receiver: str = None, *args, **kwargs):
		"""
		Step function that all sub classes must implement

		Args:
			receiver (str): The reciever's address
			args (tuple): Arguments for use in sub classes
			kwargs (dict): Keyword arguments for use in sub classes

		Raises:
			NotImplementedError: Raised when function isn't implemented

		Returns:
			Doesn't as an error is raised
		"""
		raise NotImplementedError() # Raised because function wasn't implemented by sub class

class Broadcast_IP(Protocol):
	"""
	The Broadcast_IP protocol class

	Allows for the server to get a list of clients in order to do networking with them

	Must always be done as no central server exists to do authentication
	"""

	def __init__(self, step: int = 0):
		"""
		Init

		Args:
			step (int): The current step of the protocol

		Attributes:
			(see Attributes from Protocol)
		"""
		super().__init__(step, (1, 3), ((Method.DATA,), (Method.CONFIRM,), (Method.AGREE,))) # Pass protocol details to parent

	def step(self, receiver: str = None, confirming: str = "*"):
		"""
		The step function

		Args:
			receiver (str): The receiver's address
			confirming (str): IP address that server is confirming it has

		Returns:
			None
		"""
		self._step += 1 # Increment the current step

		# No commenting will be done for the steps, read the documentation for each
		if self._step == 1: # Server
			Packet(Method.DATA, 0, self._step).finalize(receiver)

		elif self._step == 2: # Client
			Packet(Method.CONFIRM, 0, self._step).finalize(receiver)

		elif self._step == 3: # Server
			Packet(Method.AGREE, 0, self._step).addData(confirming).finalize(receiver)

		self._step += 1 # Increment the current step again

class Key_Exchange(Protocol):

	def __init__(self, step: int = 0):
		"""
		Init

		Args:
			step (int): The current step of the protocol

		Attributes:
			keys (list): Cryptography keys in order: Server's RSA, Client's RSA, Shared AES
			previousIds (list): Previously used session ids: Server's uuid, Client's uuid
			sessionIds (list): Current session ids: Server's uuid, Client's uuid
			(see Attributes from Protocol)
		"""
		super().__init__(step, (2, 4), ((Method.QUERY,), (Method.RESPONSE,), (Method.DATA,), (Method.DATA,), (Method.DATA,))) # Pass protocol details to parent
		self.keys = [None, None, None] # List of crypto keys
		self.previousIds = ["", ""] # List of previous session ids
		self.sessionIds = ["", ""] # List of current session ids

	def session(self, key: RSA = None):
		"""
		Creates a random session uuid from an RSA

		Args:
			key (RSA): An instance of RSA to base the key off of

		Returns:
			str: The new uuid from the key
		"""
		seed = sha256((key.privKey() + str(rand.randint(-(2 ** 64), 2 ** 64))).encode("utf-8")).digest().hex() # Apply sha256 to the private key plus a random number
		shuffle = [c for c in seed] # Create list of each character
		rand.shuffle(shuffle) # Shuffle around the characters
		return "".join([rand.choice(shuffle) for i in range(64)]) # Join a random character from the shuffled list, repeat this 64 times and return it

	def aesKey(self):
		"""
		Creates the AES key's key

		Returns:
			bytearray: The AES key
		"""
		return sha256((self.keys[0].pubKey() + self.keys[1].privKey() + self.previousIds[0] + self.previousIds[1]).encode("utf-8")).digest() # Generate key from Server Public RSA Key, Client Private RSA key, and the previous uuids

	def createAESKey(self):
		"""
		Creates an instance of AES and uses the key generated from aesKey

		Returns:
			None
		"""
		self.keys[2] = AES(self.aesKey()) # Saves the instance of AES to the keys

	def step(self, receiver: str = None):
		"""
		The step function

		Args:
			receiver (str): The receiver's address

		Returns:
			None
		"""
		self._step += 1 # Increment the current step

		# No commenting will be done for the steps, read the documentation for each
		if self._step == 1: # Client
			Packet(Method.QUERY, 1, self._step).finalize(receiver)

		elif self._step == 2: # Server
			Packet(Method.RESPONSE, 1, self._step).addData(self.keys[0].pubKey()).finalize(receiver)

		elif self._step == 3: # Client
			Packet(Method.DATA, 1, self._step).addData(self.keys[0].encrypt(self.keys[1].privKey())).finalize(receiver)

		elif self._step == 4: # Server
			self.sessionIds[1] = self.session(self.keys[1])
			data = self.keys[2].encrypt(self.sessionIds[1])
			Packet(Method.DATA, 1, self._step).addData(data).finalize(receiver)

		elif self._step == 5: # Client
			self.sessionIds[0] = self.session(self.keys[0])
			data = self.keys[2].encrypt(self.sessionIds[0])
			Packet(Method.DATA, 1, self._step).addData(data).finalize(receiver)

		self._step += 1 # Increment the current step again

class Method(Enum):
	"""
	All of the methods used in steps of a packet
	"""

	CONFIRM  = 1 # Used to ask to confirm
	AGREE    = 2 # To affirm a confirm
	DISAGREE = 3 # To deny a confirm
	QUERY    = 4 # Used to request for data
	RESPONSE = 5 # To give data back
	DATA     = 6 # The generalized sending of data, unspecific

	@staticmethod
	def methodFromID(mtdID: int = None):
		"""
		Gets a method from an id

		Args:
			mtdID (int): The id of the method

		Returns:
			Method: The method if its found, else None
		"""
		try: return Method(mtdID)
		except ValueError: return None

	def __str__(self):
		"""
		Converts the method to a string

		Returns:
			str: The method name and value seperated by a "~"
		"""
		return f"{self.name}~{self.value}"

class Packet:
	"""
	Used to be sent as data for steps in a protocol
	"""

	@staticmethod
	def fromString(packet: str = None):
		"""
		Tries to generate a packet from a string

		Args:
			packet (str): The raw packet

		Returns:
			Packet: The built packet, None if packet was an invalid format or decoded improperly
		"""
		if packet is None or len(packet) < 8: return None # IF packet is None or doesn't meet minimum packet length
		try: # Catch errors from casting or base 64 decoding
			mtd = int(packet[:2]) # Get the method
			proto = int(packet[2:4]) # Get the protocol
			step = int(packet[4:6]) # Get the step
			numberOfDataPoints = int(packet[6:8]) # Get the number of data points in the packet
			packetInstance = Packet(mtd, proto, step) # Create a packet object with this data
			offset = 0 # Current data read offset
			for i in range(numberOfDataPoints): # Loop x times where x is the number of data points
				del i # Remove unused i
				dataLength = int(packet[8 + offset: 12 + offset]) + 1 # Find the length of the data
				rawData = packet[12 + offset: 12 + offset + dataLength] # Read for that length of the data
				data = base64.b64decode(rawData) # Decode the data from base64
				try: # Catch error for decoding as utf-8
					decodedUTF8 = data.decode("utf-8") # Try to decode the data as utf-8 data
					packetInstance.addData(decodedUTF8) # Add data to packet
				except UnicodeDecodeError: # If error occurs
					packetInstance.addData(data) # Add raw data decoded data as it couldn't be decoded with utf-8
				offset += 4 + dataLength # Increase offset
			packetInstance.build() # Build the packet as it currently is
			return packetInstance # Return the built packet
		except (ValueError, IndexError, binascii.Error): # Error was thrown
			return None # Return none as a part of the packet building process failed

	@staticmethod
	def isValidPacket(packet: str = None):
		"""
		Checks if a packet from a string was built successfully

		Args:
			packet (str): The raw packet

		Returns:
			bool: Whether or not the packet was built successfully
		"""
		return Packet.fromString(packet) is not None # Generate a packet and see if it returned something other than none

	def __init__(self, method: int = 0, protocol: int = 0, step: int = 0):
		"""
		Init

		Args:
			method (int): The method for the packet
			protocol (int): The protocol for the packet
			step (int): Current step of the protocol

		Attributes:
			_method (int): The method
			_protocol (int): The protocol
			_step (int): The step
			_packetString (str): The built packet
			_data (list): All data points added to the packet
		"""
		if type(method) is Method: method = method.value # If method is a Method, get the integer representation
		self._method = method # Save method
		self._protocol = protocol # Save protocol
		self._step = step # Save step
		self._packetString = "" # Create empty packet string
		self._data = [] # Create empty list of data points

	def __str__(self):
		"""
		Converts the object to a string

		Returns:
			str: All of the data about the packet
		"""
		return f"Method: {self._method}, Protocol: {self._protocol}, Step: {self._step}, Data: {self._data}, Current Packet String: {self._packetString}" # All data in a string

	def addData(self, data: object = None):
		"""
		Adds data to the packet to for it to be built with

		Args:
			data (object): The data to add, string is preferred

		Returns:
			Packet: The packet
		"""
		if data is None or len(data) == 0: return self # If data is none or length is 0, return self
		self._data.append(data) # Add data to list of data points
		return self # Return self

	def build(self):
		"""
		Builds the packet into a string form and saves it to the _packetString to be sent

		Building must be done in order to get a string version of the packet else it will be nothing, empty

		Returns:
			Packet: The packet
		"""
		opt = lambda length, value: "0" * (length - len(str(value))) + str(value) # Quickly appends zeros so the string is a length
		data = opt(2, self._method) + opt(2, self._protocol) + opt(2, self._step) + opt(2, len(self._data)) # Adds the base data for the packet, all the required data
		for dataPoint in self._data: # Loop through each data point as dataPoint
			if type(dataPoint) is not bytes: dataPoint = str(dataPoint) # Check type to prevent objects that are not strings from being encoded
			if type(dataPoint) is str: dataPoint = dataPoint.encode("utf-8") # If the dataPoint is a string, convert it to a bytearray
			encodedData = base64.b64encode(dataPoint).decode("utf-8") # Use base64 to encode it and then decode it into a utf-8 string
			data += opt(4, len(encodedData) - 1) + encodedData # Add data to the built packet
		self._packetString = data # Packet string
		return self # Return self

	def getDataAt(self, index: int = 0):
		"""
		Reads data at an index

		Args:
			index (int): The index to read

		Returns:
			object: The object that that index and none if the index doesn't exist
		"""
		try: return self._data[index] # Try to return data at an index
		except IndexError: return None # Return none as data requested was at an invalid index

	def send(self, reciever: str = None):
		"""
		Sends the packet's string to an address

		Args:
			reciever (str): The address to send the data to

		Returns:
			Packet: The packet
		"""
		if self._packetString is None or len(self._packetString) == 0: return # If socket is none, packet string is none, or the length of the packet is 0, then return none
		#socket.sendData(toSendItTo, self._packetString) # Send the data to an address from a socket
		return self # Return self

	def finalize(self, reciever: str = None):
		"""
		Calls both build then send, works as a shortcut

		Args:
			reciever (str): The address to send the data to

		Returns:
			Packet: The packet
		"""
		return self.build().send(reciever) # Builds the packet, sends the packet, then returns self
