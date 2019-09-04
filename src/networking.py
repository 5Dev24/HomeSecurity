from __future__ import annotations
import socket
from threading import Thread, Timer
from error import Error, Codes


class Ports:

	BROADCAST = 25566
	SERVER_CLIENT = 25565

class Server:

	def __init__(self, port: int = Ports.SERVER_CLIENT):
		self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self._sock.bind(("localhost", port))
		self._sock.listen(25)
		self._broadcastSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self._broadcastSock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
		self._stopBroadcast = False

	def _broadcastIP(self):
		self._broadcastSock.sendto(socket.gethostbyname(socket.gethostname()), ("<broadcast>", Ports.BROADCAST))
		Thread(target=self._broadcastIPResponseHandler).start()
		Timer(600.0, self._stopBroadcasting).start()

	def _stopBroadcasting(self): self._stopBroadcast = True

	def _broadcastIPResponseHandler(self):
		while not self._stopBroadcast:
			resp, addr = self._broadcastSock.recvfrom(Ports.BROADCAST)
			if not len(resp): continue
			print("Broadcast Response " + addr[0] + ":" + addr[1] + " => \"" + resp + '"')

	def _listeningThread(self):
		while True:
			sock, addr = self._sock.accept()
			addr = ":".join(addr)
			Request(Request.methodFromString("SERVER_RECIEVED")).sendData(sock)

class Client:

	def __init__(self, port: int = Ports.SERVER_CLIENT):
		pass


"""
AA BB CCCC (D) EEEE (F) GGGG (H)

No space would actually be pressent, it's just easier to read

All numbers and in decimal, possibility for base64 or hex to store data length in case of large amounts of data needing to be sent

A = request code
B = how many pieces of data are present, default to 0, maxd is 100 but that should never occur
C, E, G = length of the next piece of data,
	note that a piece of data cannot exceed length 10000 as the
	value goes from 1 to 10000 instead of 0 to 9999 because no
	piece of data would be 0 in length
D, F, G = the data itself

"""

class Protocol:

	@staticmethod
	def _generateClassList():
		classes = {}
		for _class in Protocol.__subclasses__():
			classes[_class.__name__] = _class
		return classes

	def __init__(self, isServer: bool = False):
		self._isServer = isServer

	def execute(self): raise NotImplementedError()

class IP_BROADCAST(Protocol): pass

class DOOR_STATE_CHANGE(Protocol): pass

class DOOR_SENSOR_LOW_BATTERY(Protocol): pass

class DOOR_STATE_SYNC(Protocol): pass

class Request:

	Methods = [
		"ERROR",
		"NULL",
		"CLIENT_CONNECT",
		"CLIENT_RECIEVED",
		"CLIENT_DISCONNECT",
		"SERVER_CONNECT",
		"SERVER_RECIEVED",
		"SERVER_DISCONNECT",
		"QUERY_DATA",
		"QUERY_RESPONSE",
		"SERVER_IP_BROADCAST",
		"CLIENT_IP_BROADCAST"
	]

	@staticmethod
	def methodFromString(methodName: str = None):
		if methodName is None or len(methodName) == 0 or not (methodName in Request.Methods): return 0
		return Request.Methods.index(methodName)

	@staticmethod
	def new(requestString: str = None):
		if requestString is None or len(requestString) < 4: return None
		if type(requestString) == bytes: requestString = requestString.decode("utf-8")
		method = int(requestString[:2])
		dataPoints = int(requestString[2:4])
		proto = Request(method)
		currentOffset = 0
		while dataPoints > 0:
			dataPointLength = int(requestString[4 + currentOffset:8 + currentOffset])
			dataPointValue = requestString[8 + currentOffset:8 + dataPointLength + currentOffset]
			proto.addData(dataPointValue)
			dataPoints -= 1
		return proto


	def __init__(self, method: int = 0):
		if method < 0 or method > len(Request.Methods): method = 0
		self._mtd = method
		self.data = []

	def __str__(self):
		return self.getRequestString()

	def toPrint(self):
		base = "Method: " + Request.Methods[self._mtd].replace("_", " ").title() + "\nData Length: " + str(len(self.data))
		for dataPoint in self.data:
			base += "\n\tData Point #" + str(self.data.index(dataPoint) + 1) + ": \"" + dataPoint + '"'
		return base

	def addData(self, data: str = None):
		if data is None or len(data) == 0: return False
		if self._mtd >= 8:
			if type(data) == bytes: data = data.decode("utf-8")
			if type(self.data) == list: self.data.append(data)
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
