import re, time
from bluetooth import BluetoothSocket, RFCOMM, PORT_ANY, BluetoothError
from . import protocol as _protocol, util as _util, packet as _packet
from .. import threading as _threading, logging as _logging, file as _file
from threading import current_thread, main_thread

SessionsFolder = _file.FileSystem.GetOrCreate(_file.FileSystem, "sessions")

class Networkable:

	def __init__(self, is_server: bool = True):
		self.is_server = is_server
		self._threads = {}
		self._connections = {}
		self._sessions = {}
		self.protoHandler = _protocol.ProtocolHandler(self)
		self.socket = BluetoothSocket(RFCOMM)
		self.socket_is_ready = False

	def connect(self, id: str = ""):
		done = False
		client_rate_limit = 5
		client_time = time.time()
		while not done:
			if self.is_server:
				_logging.Log(_logging.LogType.Debug, "Advertising!", False).post()
				self.socket.bind(("", PORT_ANY))
				self.socket.listen(8)
				_util.AdvertiseService(True, self.socket, id)
				_logging.Log(_logging.LogType.Debug, "Advertising called!", False).post()
				done = True
			else:
				_logging.Log(_logging.LogType.Debug, "Looking for valid devices", False).post()
				found = _util.FindValidDevices(False)
				_logging.Log(_logging.LogType.Debug, "Found " + str(len(found)) + " devices", False).post()
				if len(found) >= 1:
					for address in found.keys():
						try:
							host, port = address.split("~")
							_logging.Log(_logging.LogType.Debug, "Got host \"" + str(host) + "\" and port \"" + str(port) + '"', False).post()
							self.socket.connect((host, int(port)))
							done = True
							break
						except Exception as e:
							if type(e) == _threading.SimpleClose: return
							else: continue
				else:
					if client_time + client_rate_limit < time.time():
						client_time = time.time()
						_logging.Log(_logging.LogType.Info, "Unable to find a server!", False).post()
		_logging.Log(_logging.LogType.Debug, "Socket is ready!", False).post()
		self.socket_is_ready = True
		self.socket_invoke()
		_logging.Log(_logging.LogType.Debug, "Socket has been started!", False).post()

	def socket_invoke(self): raise NotImplementedError()

	def recieve(self, connection: object = None, data: str = None):
		output = self.protoHandler.got_packet(data, connection)
		code = output[0]
		if code == 1 or code == 2:
			pkt = _packet.Packet(output[1], type(output[2]), output[2].current_step)
			for data in output[2:]:
				pkt.addData(data)
			pkt.send(connection)
		else: pass

	def spawn_thread(self, name: str = None, target = None, loop: bool = False, args = tuple(), kwargs = {}):
		if self._threads is None: return None
		self.close_thread(name)
		T = _threading.SimpleThread(target, loop, args, kwargs)
		self._threads[name] = T
		return T

	def start_thread(self, name: str = None):
		thread = self.get_thread(name)
		if thread is not None:
			thread.start()
			return True
		return False

	def close_thread(self, name: str = None):
		if self.thread_exists(name) and self._threads is not None:
			T = self._threads[name]
			del self._threads[name]
			T.stop()
			return True
		else: return False

	def thread_exists(self, name: str = None):
		return name in self._threads

	def get_thread(self, name: str = None):
		if self.thread_exists(name):
			return self._threads[name]
		return None

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
			return {}

	def add_session(self, addr: str = None, session: str = ""):
		

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
		self.spawn_thread("Accepting", self.accept, True, tuple(), {})

	def socket_invoke(self):
		self.start_thread("Accepting")

	def accept(self):
		if not self.socket_is_ready or self.socket is None: return
		_logging.Log(_logging.LogType.Debug, "Accepting new connections", False).post()
		sock, addr = self.socket.accept()
		_logging.Log(_logging.LogType.Debug, "Got a connection from " + str(addr), False).post()
		if not self.has_connection(addr):
			self.save_connection(sock, addr)

class Client(Networkable):

	def __init__(self): super().__init__(False)

	def socket_invoke(self): pass

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

		data = None
		try:
			data = self.socket.recv(4096)
		except BluetoothError:
			self.close()
			return

		if self.closed:
			self._receivingThread.stop()
			return

		if data is not None:
			self._invoke(self, data)

	def respond(self, data: str = None):
		if self.socket is None or data is None or type(data) != str or not len(data): return False
		self.socket.send(data)
		return True

	def close(self):
		if self._receivingThread is not None:
			self._receivingThread.stop()
			self._receivingThread = None
		if self.socket is not None:
			self.socket.close()
			self.socket = None

	def __del__(self):
		self.close()

class Session:

	@staticmethod
	def fromString(session: str = ""):
		if session.count("~") != 1: return None
		split = session.split("~")[0]
		expires = split[0]
		id = split[1]

		try: expires = int(expires)
		except ValueError: return None

		return Session(expires, id)

	def __init__(self, expires: int = 0, id: str = ""):
		self.expires = expires
		self.id = id

	@property
	def expired(self):
		return self.expires < time.time()

	def __str__(self):
		return str(self.expires) + "~" + self.id