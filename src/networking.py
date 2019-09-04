import socket
import threading
from error import Error, Codes

class Server:

	def __init__(self, port: int = 25565):
		self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self._sock.bind(("localhost", port))
		self._sock.listen(25)

	def _listeningThread(self):
		while True: pass
			#sock, addr = self._sock.accept()
			#addr = ":".join(addr)
			#Protocol()

"""
AA BB CCCC (D) EEEE (F) GGGG (H)

No space would actually be pressent, it's just easier to read

A = request code
B = how many pieces of data are present, default to 0, maxd is 100 but that should never occur
C, E, G = length of the next piece of data,
	note that a piece of data cannot exceed length 10000 as the
	value goes from 1 to 10000 instead of 0 to 9999 because no
	piece of data would be 0 in length
D, F, G = the data itself

"""

class Request:

	ERROR = 0
	NULL = 1
	CLIENT_CONNECT = 2
	CLIENT_RECIEVED = 3
	CLIENT_DISCONNECT = 4
	SERVER_CONNECT = 5
	SERVER_RECIEVED = 6
	SERVER_DISCONNECT = 7
	QUERY_DATA = 8
	QUERY_RESPONSE = 9

	@staticmethod
	def new(requestString: str = None):
		print("Req: \"", requestString, '"', sep='')
		if requestString is None or len(requestString) < 4: return None
		if type(requestString) == bytes: requestString = requestString.decode("utf-8")
		method = int(requestString[:2])
		dataPoints = int(requestString[2:4])
		proto = Request(method)
		currentOffset = 0
		while dataPoints > 0:
			dataPointLength = int(requestString[4 + currentOffset:6 + currentOffset])
			dataPointValue = requestString[6 + currentOffset:dataPointLength + currentOffset]
			print("Data Length:", dataPointLength)
			print("Data Value: \"", dataPointValue, '"', sep = '')
			proto.addData(dataPointValue)
			dataPoints -= 1
		return proto


	def __init__(self, method: int = 0):
		if method < 0 or method > 9: method = -1
		self._mtd = method
		self.data = None

	def __str__(self):
		return self.getRequestString()

	def addData(self, data: str = None):
		if data is None or len(data) == 0: return False
		if self._mtd >= 8:
			if type(data) == bytes: data = data.decode("utf-8")
			if self.data is None: self.data = [data]
			elif type(self.data) == list: self.data.append(data)
			else: return False
			return True
		return False

	def getRequestString(self):
		opt = lambda val, length: "0" * (length - len(str(val))) + str(val)
		request = opt(self._mtd, 2) + opt(0 if self.data is None else len(self.data), 2)
		if self.data is None: return request
		for data in self.data:
			request += opt(len(data), 4) + data
		return request

	def sendData(self, sock: socket.socket = None):
		if sock is None: return
		sock.send(bytes(self.getRequestString(), "utf-8"))
		sock.close()

"""import socket
import threading
from error import Error, Codes

class Service:

	def __init__(self, ip: str = "127.0.0.1", port: int = 8080, isServer: bool = False):
		self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		try: self._socket.bind((ip, port))
		except socket.error as e: Error(e, Codes.EXIT, "Failed to bind to socket (1)")
		self._isServer = isServer
		if self._isServer:
			threading.Thread(target=self._thread).start()
		self.clients = []

	def _thread(self):
		self._socket.listen(10)
		while True:
			sock, addr = self._socket.accept()
			print("New Connection: ", addr[0], ':', addr[1], sep = '')
			c = SockAddr(sock, addr, None)
			thread = threading.Thread(target=self._listener, args=[c])
			c.thread = thread
			self.clients.append(c)
			thread.start()

	def _listener(self, c: object = None):
		while not c.stop:
			try:
				sock, addr = c.sock, c.addr[0] + ":" + str(c.addr[1])
				data = sock.recv(1024).decode("utf-8")
				if len(data) == 0: continue
				data = Protocall.new(data)
				print("Recieved \"" + str(data) + "\" from " + addr)
				if data._method == Methods.DISCONNECT:
					print("Disconnect Handled")
					c.stop = True
					continue
				'''if not data:
					Error(socket.error(), Codes.CONTINUE, "Invalid data sent in client listener for client " + addr)'''
			except BaseException as e:
				Error(e, Codes.CONTINUE, "Exception occured in client listener for client " + addr)

class SockAddr:

	def __init__(self, sock: socket.socket = None, addr: list = None, thread: threading.Thread = None):
		self.sock = sock
		self.addr = addr
		self.thread = thread
		self.stop = False

class Client:

	def __init__(self, ip: str = None, port: int = None):
		self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		try: self._socket.bind((ip, port))
		except socket.error as e: Error(e, Codes.EXIT, "Failed to bind to socket (2)")
		self._address = [ip, port]

	def connectToServer(self, ip: str = None):
		self._server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self._server.connect((ip, 8080))
		self._server.send(Protocall(Methods.CONNECT).generateRequest())
		self._thread = threading.Thread(target=self._listener)
		self._thread.start()

	def _listener(self):
		while True:
			self._server.send(Protocall(Methods.ALIVE, "").generateRequest())

class Methods:

	CONNECT = 0
	REQUEST = 1
	DISCONNECT = 2
	SEND_DATA = 3
	ALIVE = 4

	def toString(self, method: int = 0):
		if method == 0: return "CONNECT"
		elif method == 1: return "REQUEST"
		elif method == 2: return "DISCONNECT"
		elif method == 3: return "SEND_DATA"
		elif method == 4: return "ALIVE"

class Protocall:

	@staticmethod
	def new(request: str = None):
		first = request.split("-")[0]
		rest = request.split("-")[1:]
		rest = "-".join(rest)
		print("Rest", rest)
		return Protocall(int(first), rest)

	def __init__(self, method: int = 3, data: str = None):
		if method < 0: method = 0
		elif method > 3: method = 3
		self._method = method
		if data is None: data = ""
		self._data = data

	def generateRequest(self):
		return (str(self._method) + "-" + self._data.replace(";", "!") + ";").encode("utf-8")

	def __str__(self):
		return "Method: " + Methods.toString(self._method) + ", Data: \"" + self._data + '"'
"""
