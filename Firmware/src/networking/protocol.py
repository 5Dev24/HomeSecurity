from . import packet as _packet, networkables as _networkables
from .. import crypt as _crypt
from enum import Enum
from hashlib import sha256
import random

class ProtocolHandler:

	def __init__(self, parent: _networkables.Networkable = None):
		self.protocols = {}
		self.parent = parent

	def got_packet(self, packet: str = None, connection: _networkables.Connection = None):
		"""
		-3 = Passed packet was invalid
		-2 = Passed connection was invalid
		-1 = No method exists to handle the packet's protocol
		 0 = Failed internal checks, nothing was done
		 1 = All went fine but protocol is still active
		 2 = All went fine and protocol finished
		"""
		if packet is None or type(packet) != str or not len(packet): return -3
		if connection is None or type(connection) != _networkables.Connection or connection.closed: return -2
		return self._handle_packet(_packet.Packet.fromString(packet), connection)

	def _handle_packet(self, packet: _packet.Packet = None, connection: _networkables.Connection = None):
		if packet is None or type(packet) != _packet.Packet: return -3
		if connection is None or type(connection) != _networkables.Connection or connection.closed: return -2

	def get_protocols(self, connection: _networkables.Connection = None):
		if connection is None or type(connection) != _networkables.Connection or connection.closed: return None
		if connection.addr in self.protocols: return self.protocols[connection.addr]
		return None

	def get_specific_protocol(self, connection: _networkables.Connection = None, protocolClass = None):
		protos = self.get_protocols(connection)
		if protos is not None:
			pass
		else: return None

	def spawn_protocol(self, connection: _networkables.Connection = None, timeout: int = None, protocolClass = None, args = tuple(), kwargs = {}):
		proto = protocolClass(*args, **kwargs)

class Protocol:

	@staticmethod
	def AllProtocols():
		return [_cls.__name__.upper() for _cls in Protocol.__subclasses__()]

	Steps = None

	def __init__(self, step: int = 1):
		self.current_step = step
		self._finished = False

	def take_step(self, received_packet: _packet.Packet = None, fromClient: bool = True):
		if received_packet is not None:
			if not self.is_proper_response(received_packet, fromClient):
				return False
		self.do_step(self.current_step)
		self.current_step += 1
		return True

	def do_step(self, step: int = 1): raise NotImplementedError()

	def is_proper_response(self, packet: _packet.Packet = None, fromClient: bool = True):
		if packet._protocol != type(self): return False
		elif packet._step != self.current_step: return False
		elif not self.__class__.Steps[self.current_step - 1].valid_method(packet._method): return False
		elif self.__class__.Steps[self.current_step - 1].is_server_step and fromClient: return False
		else: return False

class Method(Enum):
	"""
	All of the methods used in steps of a packet
	"""

	NONE     = 0 # Error method
	CONFIRM  = 1 # Used to ask to confirm
	AGREE    = 2 # To affirm a confirm
	DISAGREE = 3 # To deny a confirm
	QUERY    = 4 # Used to request for data
	RESPONSE = 5 # To give data back
	DATA     = 6 # The generalized sending of data, unspecific

	@staticmethod
	def methodFromID(mtdID: int = None):
		try: return Method(mtdID)
		except ValueError: return None

class Step:

	def __init__(self, is_server_step: bool = False, methods: object = None):
		self.is_server_step = is_server_step

		if type(methods) == Method: self.methods = (methods,)
		elif type(methods) == tuple: self.methods = methods
		elif type(methods) == list: self.methods = tuple(methods)
		else: self.methods = tuple()

	def valid_method(self, method: Method = Method.NONE):
		return method in self.methods

class Key_Exchange:

	Steps = [
		Step(False, Method.QUERY),
		Step(True, Method.RESPONSE),
		Step(False, Method.DATA),
		Step(True, Method.DATA),
		Step(False, Method.DATA)
	]

	def __init__(self, step: int = 1):
		super().__init__(step)
		self.keys = [None] * 3
		self.previousSessionIDs = [None] * 2
		self.newSessionIDS = [None] * 2

	def session(self, key: _crypt.RSA = None):
		randSeed = sha256((key.privKey() + str(random.randint(-(2 ** 64), 2 ** 64))).encode("utf-8")).digest().hex()
		shuffle = [c for c in randSeed]
		random.shuffle(shuffle)
		return "".join([random.choice(shuffle) for i in range(64)])

	def aes_key(self):
		return sha256((
			self.keys[0].pubKey() +
			self.keys[1].privKey() +
			self.previousSessionIDs[0] +
			self.previousSessionIDs[1]).encode("utf-8")).digest()

	def aes(self):
		if self.keys[2] is None:
			self.keys[2] = _crypt.AES(self.aes_key())

	def step(self, step: int = 1):
		if step == 1:
			return (Method.QUERY,)

		elif step == 2 and self.keys[0] is not None:
			return (Method.RESPONSE, self.keys[0].pubKey())

		elif step == 3 and self.keys[0] is not None and self.keys[1] is not None:
			return (Method.DATA, self.keys[0].encrypt(self.keys[1].privKey()))

		elif step == 4 and self.keys[1] is not None and self.keys[2] is not None and self.newSessionIDS[1] is None:
			_id = self.session(self.keys[1])
			self.newSessionIDS[1] = _id
			_id = self.keys[2].encrypt(_id)
			return (Method.DATA, _id)

		elif step == 5 and self.keys[0] is not None and self.keys[2] is not None and self.newSessionIDS[0] is None:
			_id = self.session(self.keys[0])
			self.newSessionIDS[0] = _id
			_id = self.keys[2].encrypt(_id)
			return (Method.DATA, _id)

		return (Method.NONE,)