import re, time
from bluetooth import BluetoothSocket, RFCOMM, PORT_ANY
from . import protocol as _protocol, util as _util
from .. import threading as _threading, logging as _logging, file as _file
from threading import current_thread, main_thread

SessionsFolder = _file.FileSystem.GetOrCreate(_file.FileSystem, "sessions")

class Networkable:

	def __init__(self, is_server: bool = True):
		self.is_server = is_server
		self._threads = {}
		self._connections = {}
		self._sessions = {}
		self.socket = BluetoothSocket(RFCOMM)
		self.socket_is_ready = False
		self.socket_thread = self.spawn_thread("Accepting", self._accept, True)

	def connect(self):
		while True:
			if self.is_server:
				self.socket.bind(("", PORT_ANY))
				self.socket.listen(8)
				_util.AdvertiseService(True, self.socket)
				self.socket_is_ready = True
				self.socket_thread.start()
				return
			else:
				found = _util.FindValidDevices(False)
				if len(found) >= 1:
					for address in found.keys():
						try:
							host, port = address.split("~")
							self.socket.connect((host, int(port)))
							self.socket_is_ready = True
							self.socket_thread.start()
							return
						except Exception:
							continue
				else:
					_logging.Log(_logging.LogType.Info, "Unable to find a server!", False).post()

	def _accept(self):
		if not self.socket_is_ready or self.socket is None: return
		sock, addr = self.socket.accept()
		if not self.has_connection(addr):
			self.save_connection(sock, addr)

	def recieve(self, connection: object = None, data: str = None):
		raise NotImplementedError()

	def spawn_thread(self, name: str = None, target = None, loop: bool = False, args = tuple(), kwargs = {}):
		if self._threads is None: return None
		self.close_thread(name)
		T = _threading.SimpleThread(target, loop, args, kwargs)
		self._threads[name] = T
		return T

	def close_thread(self, name: str = None):
		if self.thread_exists(name) and self._threads is not None:
			T = self._threads[name]
			del self._threads[name]
			T.stop()
			return True
		else: return False

	def thread_exists(self, name: str = None):
		return name in self._threads

	def save_connection(self, socket: BluetoothSocket = None, addr: str = None):
		if self._connections is None: return
		c = Connection(addr, socket, self.recieve)
		self._connections[addr] = c
		return c

	def close_connection(self, addr: str = None):
		if self.has_connection(addr) and self._connections is not None:
			connection = self._connections[addr]
			del self._connections[addr]
			connection.close()
			return True
		else: return False

	def has_connection(self, addr: str = None):
		return addr in self._connections and not self._connections[addr].closed

	def get_sessions(self, addr: str = None):
		if _file.File.Exists(SessionsFolder, addr):
			file_format = _file.SessionIDFormat.loadFrom(_file.File.GetOrCreate(SessionsFolder, addr))
			return file_format.ids
		else:
			return None

	def save_sessions(self, addr: str = None, sessions: dict = None):
		file_format = _file.SessionIDFormat(sessions)
		file_dest = _file.File.GetOrCreate(SessionsFolder, addr)
		file_format.write(file_dest)

	def __del__(self):
		# Close connections and threads
		for thread in self._threads.values():
			thread.stop()
		for connection in self._connections.values():
			connection.close()
		self._threads = None
		self._connections = None

		# Close socket related items
		self.socket_is_ready = False
		self.socket.close()
		self.socket = None

class Server(Networkable):

	def __init__(self):
		super().__init__(True)

class Client(Networkable):

	def __init__(self):
		super().__init__(False)

class Connection:

	def __init__(self, addr: str = None, socket: BluetoothSocket = None, invoke = None):
		self.addr = addr
		self.socket = socket
		self._invoke = invoke
		self._receivingThread = _threading.SimpleThread(self._receive, True).start()
		self._auth_level = -1

	@property
	def closed(self):
		return self.socket is None

	def _receive(self):
		if self.closed:
			self._receivingThread.stop()
			return

		data = self.socket.recv(4096)
		if self.closed:
			self._receivingThread.stop()
			return

		self._invoke(self, data)

	def respond(self, data: str = None):
		if self.socket is None or data is None or type(data) != str or not len(data): return False
		self.socket.send(data)
		return True

	def close(self):
		self._receivingThread.stop()
		self.socket.close()
		self.socket = None

	def __del__(self):
		self.close()
