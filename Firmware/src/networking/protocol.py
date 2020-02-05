from . import packet as _packet, util as _util
from ..crypt import RSA, AES
from enum import Enum
import random

class ProtocolHandler:
	"""
	Handles incoming packets

	Verifies if a packet is legit and if steps should be done because of it
	"""

	def __init__(self, selfInstance: object = None):
		"""
		Init

		Args:
			selfInstance (Networkable): The instance of a client or server

		Attributes:
			_instanceOfOwner (Networkable): The instance of the object that created this object
		"""
		self._instanceOfOwner = selfInstance # Save owner

	def isBroadcastIPPacket(self, packet: str = None):
		if type(packet) != str or not _packet.Packet.isValidPacket(packet): return False
		return _packet.Packet.fromString(packet)._protocol == 0

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
		if type(packet) != str or not _packet.Packet.isValidPacket(packet): return -2 # If packet isn't a string or isn't a valid packet, return -2
		return self._handlePacket(_packet.Packet.fromString(packet), sentBy) # Return exit code from the internal handler returns

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
				Log(LogType.Info, f"Client ({_util.DeviceID()}) is done with Key Exchange ({spawned.sessionIds[1]})", False).post()
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
				Log(LogType.Info, f"Server ({_util.DeviceID()}) is done with Key Exchange with {sentBy} ({spawned.sessionIds[0]})", False).post()
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
			_packet.Packet(Method.DATA, 0, self._step).finalize(receiver)

		elif self._step == 2: # Client
			_packet.Packet(Method.CONFIRM, 0, self._step).finalize(receiver)

		elif self._step == 3: # Server
			_packet.Packet(Method.AGREE, 0, self._step).addData(confirming).finalize(receiver)

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
		seed = sha256((key.privKey() + str(random.randint(-(2 ** 64), 2 ** 64))).encode("utf-8")).digest().hex() # Apply sha256 to the private key plus a random number
		shuffle = [c for c in seed] # Create list of each character
		random.shuffle(shuffle) # Shuffle around the characters
		return "".join([random.choice(shuffle) for i in range(64)]) # Join a random character from the shuffled list, repeat this 64 times and return it

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
			_packet.Packet(Method.QUERY, 1, self._step).finalize(receiver)

		elif self._step == 2: # Server
			_packet.Packet(Method.RESPONSE, 1, self._step).addData(self.keys[0].pubKey()).finalize(receiver)

		elif self._step == 3: # Client
			_packet.Packet(Method.DATA, 1, self._step).addData(self.keys[0].encrypt(self.keys[1].privKey())).finalize(receiver)

		elif self._step == 4: # Server
			self.sessionIds[1] = self.session(self.keys[1])
			data = self.keys[2].encrypt(self.sessionIds[1])
			_packet.Packet(Method.DATA, 1, self._step).addData(data).finalize(receiver)

		elif self._step == 5: # Client
			self.sessionIds[0] = self.session(self.keys[0])
			data = self.keys[2].encrypt(self.sessionIds[0])
			_packet.Packet(Method.DATA, 1, self._step).addData(data).finalize(receiver)

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
