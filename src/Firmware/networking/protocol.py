from typing import Dict, Tuple, Type, Any, Union
from threading import Event, RLock
from queue import Queue
from networking import net_io_handles

class ProtocolManager:

	__instance = None

	@staticmethod
	def is_unencrypted_protocol(protocol_id: int):
		return protocol_id >= 0 and protocol_id <= 255

	@staticmethod
	def is_encrypted_protocol(protocol_id: int):
		return protocol_id >= 256 and protocol_id <= 65535

	@staticmethod
	def is_recv_only_protocol(protocol_id: int):
		return protocol_id in (16, 272)

	@staticmethod
	def is_special_protocol(protocol_id: int):
		return protocol_id in (0, 256)

	@staticmethod
	def load_protocols():
		# Change to logger, no save, yes print
		print("Loading protocols")
		from networking import protocols
		mngr = ProtocolManager.get_manager()

		with mngr.lock:
			keys = sorted(mngr.protocols.keys())
			for key in keys:
				print("proto=", mngr.protocols[key].__name__, ",id=", key, sep="")

	@classmethod
	def get_manager(cls) -> "ProtocolManager":
		if cls.__instance is None:
			cls.__instance = cls.__new__(cls)
			self = cls.__instance

			self.protocols = {}
			self.lock = RLock()

		return cls.__instance

	def __init__(self):
		# For typing
		self.protocols: Dict[int, Protocol]
		self.lock: RLock

		raise RuntimeError("Get protocol manager from ProtocolManager.get_manager()")

	def get_protocol(self, protocol_id: int) -> Union[Type["Protocol"], None]:
		with self.lock:
			if protocol_id in self.protocols:
				return self.protocols[protocol_id]

	def spawn_protocol(self, protocol_id: int, *args, **kwargs) -> Union["Protocol", None]:
		with self.lock:
			if protocol_id in self.protocols:
				return self.protocols[protocol_id](*args, **kwargs)

	def is_registered_protocol(self, protocol_id: int) -> bool:
		with self.lock:
			return protocol_id in self.protocols

	def register_protocol(self, protocol_id: int, protocol_class: Type["Protocol"]) -> bool:
		with self.lock:
			if protocol_id not in self.protocols:
				self.protocols[protocol_id] = protocol_class
				return True

		return False

class ProtocolMeta(type):

	def __new__(cls, name: str, bases: Tuple[Type], namespace: Dict[str, Any], **kwargs):
		if "register" in kwargs and not kwargs["register"]:
			del kwargs["register"]
			return super().__new__(cls, name, bases, namespace, **kwargs)

		if "id" not in kwargs and not isinstance(kwargs["id"], int):
			raise RuntimeError("A protocol must be created with the kwargs \"id\" as an integer")

		mngr = ProtocolManager.get_manager()
		protocol_id = kwargs["id"]
		del kwargs["id"]

		with mngr.lock:
			if mngr.is_registered_protocol(protocol_id):
				conflicting = mngr.get_protocol(protocol_id)
				raise RuntimeError(f"Conflict between new protocol \"{name}\" (id={protocol_id}) and protocol \"{conflicting.__name__}\" (id={conflicting.protocol_id})")

			namespace["protocol_id"] = protocol_id
			instance = super().__new__(cls, name, bases, namespace, **kwargs)
			mngr.register_protocol(protocol_id, instance)
			return instance

class ProtocolEnded(Exception): pass # When a protocol has been ended by either party and an action is attempted on the protocol

# Allows for Protocol to just be inherited to make a class a protocol
# Adds helpers for protocols
class Protocol(object, metaclass = ProtocolMeta, register = False):

	__slots__ = tuple()

	def __init__(self):
		self.__recv_buffer: Queue[bytes] = Queue()
		self.__send_buffer: Queue[bytes] = Queue()
		self.__end_event = Event()
		self.__internal_thread: thread.EasyThread
		self.protocol_id: int

	def start_server(self, connection: net_io_handles.Connection):
		"""
		[Server side]
		Starts protocol as the server
		"""
		if self.__internal_thread is None:
			self.__internal_thread = thread.EasyThread(self.server_target, args = (connection,), catch = self.exception_catch)
			self.__internal_thread.start()

	def start_client(self, connection: net_io_handles.Connection):
		"""
		[Client side]
		Starts protocol as the client
		"""
		if self.__internal_thread is None:
			self.__internal_thread = thread.EasyThread(self.client_target, args = (connection,), catch = self.exception_catch)
			self.__internal_thread.start()

	def exception_catch(self, exc: Exception):
		if type(exc) == ProtocolEnded:
			try:
				self.end()
			except ProtocolEnded:
				pass

			return True

		return False

	def server_target(self, connection: net_io_handles.Connection):
		"""
		[Server side]
		This function will be put on a thread, it will
		contain the entire implmentation of the protocol
		excluding helpers. Instance variables are not needed
		due to protocol instances being destroyed after use
		"""
		raise NotImplementedError(f"{self.__class__.__name__} must implement server_target() to allow for send/received loop on the server side")

	def client_target(self, connection: net_io_handles.Connection):
		"""
		[Client side]
		This function will be put on a thread, it will
		contain the entire implmentation of the protocol
		excluding helpers. Instance variables are not needed
		due to protocol instances being destroyed after use
		"""
		raise NotImplementedError(f"{self.__class__.__name__} must implement server_target() to allow for send/received loop on the client side")

	def end(self) -> None:
		"""
		Ends the protocol and raises the ProtocolEnded exception
		"""
		if self.alive:
			self.send(b"") # Prevent code from waiting on sending_data
			self.__end_event.set()
			self.__internal_thread.kill()
			raise ProtocolEnded()

	def ending(self) -> None:
		self.__end_event.wait()

	@property
	def alive(self) -> bool:
		return not self.__end_event.is_set()

	def received_data(self, data: bytes) -> None:
		"""
		[External] Add data that the protocol received
		"""
		if not self.alive:
			raise ProtocolEnded()

		self.__recv_buffer.put_nowait(data)

	def recv(self) -> bytes:
		"""
		[Internal] Get data
		"""
		if not self.alive:
			raise ProtocolEnded()

		return self.__recv_buffer.get()

	def send(self, data: bytes) -> None:
		"""
		[Internal] Send data
		"""
		if not self.alive:
			raise ProtocolEnded()

		self.__send_buffer.put_nowait(data)

	def sending_data(self) -> bytes:
		"""
		[External] Get the data the protocol wants to send
		"""
		if not self.alive:
			raise ProtocolEnded()

		return self.__send_buffer.get()

import thread, sys

if "protocols" not in sys.modules:
	ProtocolManager.load_protocols()