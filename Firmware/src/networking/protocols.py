from . import protocol as _protocol
from .. import crypt as _crypt
from hashlib import sha256
import random

Protocol = _protocol.Protocol
Step = _protocol.Step
Method = _protocol.Method

class Key_Exchange(Protocol):

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

	def do_step(self):
		if self.current_step == 1:
			return (1, Method.QUERY, self)

		elif self.current_step == 2 and self.keys[0] is not None:
			return (1, Method.RESPONSE, self, self.keys[0].pubKey())

		elif self.current_step == 3 and self.keys[0] is not None and self.keys[1] is not None:
			return (1, Method.DATA, self, self.keys[0].encrypt(self.keys[1].privKey()))

		elif self.current_step == 4 and self.keys[1] is not None and self.keys[2] is not None and self.newSessionIDS[1] is None:
			_id = self.session(self.keys[1])
			self.newSessionIDS[1] = _id
			_id = self.keys[2].encrypt(_id)
			return (2, Method.DATA, self, _id)

		elif self.current_step == 5 and self.keys[0] is not None and self.keys[2] is not None and self.newSessionIDS[0] is None:
			_id = self.session(self.keys[0])
			self.newSessionIDS[0] = _id
			_id = self.keys[2].encrypt(_id)
			return (2, Method.DATA, self, _id)

		return (0, Method.NONE,)

# Register all default protocols

Protocol.registerProtocol(Key_Exchange)