import re, time
from ..codes import LogCode, Networking, Threading
from ..crypt import RSA
from . import protocol as _protocol, threading as _threading
from threading import current_thread, main_thread

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
		"""
		self._isServer = isServer # Save if server
		self._broadcastSocket = None # Create broadcasting socket
		self._broadcastReceiveThread = _threading.SimpleThread(self._broadcastReceive, True).start() # Create broadcasting listening thread
		self._generalSocket = None # Create general data receiving socket
		self._generalReceiveThread = _threading.SimpleThread(self._generalReceive, True).start() # Create general data listening thread
		self._networkingThreads = {} # Currently active networking threads {thread name: thread instance}
		self._activeProtocols = {} # Currently active protocol {"ip:port": [Protocol instance,]}
		self._protocolHandler = _protocol.ProtocolHandler(self) # Create protocol handler

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
		T = _threading.SimpleThread(threadTarget, loop = loop, *args, **kwargs) # Create instance of thread
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
		if type(timeout) == int: _threading.SimpleThread(target = self._threadTimeout, loop = False,
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
		if current_thread() is main_thread(): # If function has been called from main thread
			LogCode(Threading.JOIN_FROM_MAIN)
			return -2 # Exit function, return -2 error
		time.sleep(timeout) # Sleep for timeout seconds
		self.invalidateProtocol(recipient, proto) # Invalidate the protocol

	def _broadcastReceive(self):
		"""
		An internal function that listens for data being sent to the broadcasting socket of the networkable

		Returns:
			None
		"""
		if self._broadcastSocket is None: # If socket is closed
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
		if self._generalSocket is None: # If socket is closed
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
		self._broadcastProtoSaved = super().spawnProtocol("<broadcast>", None, _protocol.Broadcast_IP, args = (0,)) # Broadcast ip protocol instance

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
			super().invalidateProtocol("<broadcast>", _protocol.Broadcast_IP) # Invalidate Broadcast_IP protocol
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
		_threading.SimpleThread(threading, False, args=(self,)).start() # Create threaded handler and start thread

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
		ex = super().spawnProtocol(self._serversIP, None, _protocol.Key_Exchange, args = (0,)) # Create an instance of the Key_Exchange protocol
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
			super().invalidateProtocol("<broadcast>", _protocol.Broadcast_IP) # Invalidate the broadcast ip protocol
			self._broadcastSocket.close() # Close the broadcasting socket
			self._serversIP = self._serversIP # Set server's ip to be a TAddress
			self.keyExchange() # Start key exchange proto

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