from networking.net_io_handles import Connection
from networking.protocol import Protocol

class EOP(Protocol, id = 0): # End of Protocol

	def server_target(self, conn: Connection):
		raise RuntimeError("EOP cannot be started")

	def client_target(self, conn: Connection):
		raise RuntimeError("EOP cannot be started")

class SP(Protocol, id = 16): # Simple Protocol

	def server_target(self, conn: Connection):
		print("Told", self.recv(), "by", conn.mac)

	def client_target(self, conn: Connection):
		print("Told", self.recv(), "by", conn.mac)

class KEv1(Protocol, id = 17): # Key Exchange

	def server_target(self, conn: Connection):
		pass

	def client_target(self, conn: Connection):
		pass

class EOSP(Protocol, id = 256): # End of Secure Protocol

	def server_target(self, conn: Connection):
		raise RuntimeError("EOSP cannot be started")

	def client_target(self, conn: Connection):
		raise RuntimeError("EOSP cannot be started")

class SSP(Protocol, id = 272): # Secure Simple Protocol

	def server_target(self, conn: Connection):
		print("Told", self.recv(), "by", conn.mac)

	def client_target(self, conn: Connection):
		print("Told", self.recv(), "by", conn.mac)

class SKEv1(Protocol, id = 273): # Secure Key Exchange

	def server_target(self, conn: Connection):
		pass

	def client_target(self, conn: Connection):
		pass

class TestProtocol(Protocol, id = 1):

	def server_target(self, conn: Connection):
		initial = self.recv()

		print("Client says \"", initial, '"', sep="")

		if initial == b"Good morning":
			self.send(b"Good morning")
		elif initial == b"Bad morning":
			self.send(b"Well I hope it gets better")

		final_trans = self.recv()

		print("Client says \"", final_trans, '"', sep="")

		self.end()

	def client_target(self, conn: Connection):
		from random import randint

		saying = b"Good morning" if randint(0, 1) else b"Bad morning"

		print("Going to say \"", saying, '"', sep="")

		self.send(saying)

		server_response = self.recv()

		print("Server says \"", server_response, '"', sep="")

		if server_response == b"Good morning":
			self.send(b"It's gonna be a good day")
		elif server_response == b"Well I hope it gets better":
			self.send(b"I hope so")

		self.end()