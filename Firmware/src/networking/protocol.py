from . import packet as _packet
from enum import Enum

class Protocol:

	@staticmethod
	def AllProtocols():
		return [_cls.__name__.upper() for _cls in Protocol.__subclasses__()]

	Steps = None

	def __init__(self, step: int = 1):
		self.current_step = step

	def take_step(self, previous_packet: _packet.Packet = None, fromClient: bool = True):
		if previous_packet is not None:
			if not self.is_proper_response(previous_packet, fromClient):
				return False
		self.step(self.current_step)
		self.current_step += 1
		return True

	def step(self, step: int = 1): raise NotImplementedError()

	def is_proper_response(self, packet: _packet.Packet = None, fromClient: bool = True):
		if packet._protocol != type(self): return False
		elif packet._step != self.current_step: return False
		elif not self.__class__.Steps[self.current_step - 1].valid_method(packet._method): return False
		elif self.__class__.Steps[self.current_step - 1].is_server_step and fromClient: return False
		else: return False

	def step(self, function):
		def wrapper():
			function()
		return wrapper

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

	def step(self, step: int = 1):
