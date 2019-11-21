from .crypt import AES, RSA
from hashlib import sha256
from threading import Thread, Timer, Event
import time, random, string, re, traceback, sys, base64

Characters = string.punctuation + string.digits + string.ascii_letters

class TPorts:

	SEND_RECEIVE = 2
	SERVER_BROADCAST = 4

class TAddress:

	allAddresses = []

	@staticmethod
	def isRegisteredAddress(addr: str = "", port: int = 0):
		for addr in TAddress.allAddresses:
			if addr[0] == addr and addr[1] == port and addr.registered: return True
		return False

	def __init__(self, addr: str = "", port: int = 0):
		self.addr = (addr, port)
		self.registered = True
		TAddress.allAddresses.append(self)

	def __str__(self):
		return self.addr[0] + ":" + str(self.addr[1])

	def free(self):
		self.registered = False
		TAddress.allAddresses.remove(self)

class TData:

	def __init__(self, data: str = "", isBroadcast: bool = False):
		self.data = data
		self._read = False
		self._isBroadcast = isBroadcast

	def __len__(self):
		return len(self.data) if (not self._read) or self._isBroadcast else 0

	def get(self):
		if self._read == False or self._isBroadcast:
			self._read = True
			return self.data
		return None

class TSocket:

	allSockets = []

	@staticmethod
	def sendDataProtected(sender: TAddress = None, receiver: TAddress = None, data: str = None):
		for sock in TSocket.allSockets:
			if sock._addr.registered and str(sock._addr) == str(receiver): # In a real situation, any socket could receive this message but we're assuming that a socket only accepts messages for itself
				TThread(target=sock.receive, args=(sender, TData(data, False))).start()
				return

	@staticmethod
	def getSocket(getterIP: str = "127.0.0.1", addr: TAddress = None):
		for sock in TSocket.allSockets:
			if sock._addr == addr:
				return sock
		if type(getterIP) != str: return None
		return TSocket.createNewSocket(getterIP, addr)

	@staticmethod
	def createNewSocket(spawnerIP: str = "127.0.0.1", addr: TAddress = None):
		sock = TSocket(spawnerIP, addr)
		TSocket.allSockets.append(sock)
		return sock

	def __init__(self, ip: str = "127.0.0.1", addr: TAddress = None):
		self._spawnedFrom = ip
		self._addr = addr
		self._dataHistroy = []
		self._lastDatareceived = None
		self._receiveEvent = Event()
		self._receivers = 0
		self._callbackID = random.randint(-1 * (2 ** 32), 2 ** 32)

	def __str__(self):
		return f"Address: {self._addr}, Data History: {self._dataHistroy}, Last Data Received: {self._lastDatareceived}, \
Receive Event Set: {self._receiveEvent.is_set()}, Receivers: {self._receivers}, and Callback ID: {self._callbackID}"

	def receive(self, addr: TAddress = None, data: TData = None):
		if self.closed(): return
		if not (type(data) is TData): return
		data = data.get()
		if data is None:
			print("Data was already read before we received it, was this meant broadcasted message?")
			return
		self._dataHistroy.append([addr, data])
		while len(self._dataHistroy) > 25: del self._dataHistroy[0]
		self._lastDatareceived = [addr, data]
		timeout = 0
		while self._receiveEvent.is_set() and timeout < 3:
			time.sleep(.05)
			timeout += 1
			continue
		if timeout == 3: return
		self._receiveEvent.set()

	def receiveData(self):
		if self.closed(): return [None, None]
		if self._receivers > 1:
			print("2 Threads Listening For Data!")
			return [None, None]
		got = None
		self._receivers += 1
		while got is None:
			self._receiveEvent.wait()
			got = self._lastDatareceived
		self._lastDatareceived = None
		self._receiveEvent.clear()
		self._receivers -= 1
		return got

	def sendData(self, receiver: TAddress = None, data: str = None):
		if self.closed(): return
		if receiver.addr[0] == "<broadcast>":
			for sock in TSocket.allSockets:
				if sock._addr.registered and sock._addr.addr[0] == self._addr.addr[0] and sock._addr.addr[1] == self._addr.addr[1] and sock._callbackID != self._callbackID:
					sock.receive(self._addr, TData(data, True))
		else: TSocket.sendDataProtected(self._addr, receiver, data)

	def closed(self):
		return not self._addr.registered

	def close(self):
		self._addr.free()
		del TSocket.allSockets[TSocket.allSockets.index(self)]

class TThread:

	def __init__(self, target = None, loop: bool = False, args = (), kwargs = {}):
		self._internalThread = Thread(target=self._internal)
		self._target = target
		self._args = args
		self._kwargs = {} if kwargs is None else kwargs
		self._loop = loop
		self._stop = False
		self._running = True

	def stop(self):
		self._stop = True
		self._running = False
		return self

	def _internal(self):
		if self._loop:
			while not self._stop and self._running:
				try: self._target(*self._args, **self._kwargs)
				except BaseException:
					print(f"Theoretical Thread threw an error (1), closing thread\n{traceback.format_exc()}")
					break
		else:
			try: self._target(*self._args, **self._kwargs)
			except BaseException: print(f"Theoretical Thread threw an error (2), closing thread\n{traceback.format_exc()}")
		self.stop()
		del self._internalThread

	def start(self):
		self._internalThread.start()
		self._running = True
		return self

class TNetworkable:

	def __init__(self, isServer: bool = False, fakeRealIP: str = None):
		self._isServer = isServer
		self._ip = fakeRealIP
		self._broadcastSocket = TSocket.createNewSocket(fakeRealIP, TAddress("<broadcast>", TPorts.SERVER_BROADCAST))
		self._broadcastReceiveThread = TThread(self._broadcastReceive, True).start()
		self._generalSocket = TSocket.createNewSocket(fakeRealIP, TAddress(fakeRealIP, TPorts.SEND_RECEIVE))
		self._generalReceiveThread = TThread(self._generalReceive, True).start()
		self._networkingThreads = {}
		self._activeProtocols = {}
		self._protocolHandler = ProtocolHandler(not isServer, self)

	def isIP(self, ipaddr: str = None):
		if ipaddr is None or type(ipaddr) != str or not len(ipaddr): return False
		return re.match("((\\.)*\\d{1,3}){4}", ipaddr)

	def spawnThread(self, threadName: str = None, threadTarget = None, loop: bool = False, args = (), kwargs = {}):
		self.closeThread(threadName)
		T = TThread(threadTarget, loop = loop, *args, **kwargs)
		self._networkingThreads[threadName] = T
		return T

	def closeThread(self, threadName: str = None):
		try:
			self._networkingThreads[threadName].stop()
			del self._networkingThreads[threadName]
			return True
		except KeyError: return False

	def spawnProtocol(self, recipient: TAddress = None, timeout = None, protocolClass = None, args = (), kwargs = {}):
		proto = protocolClass(*args, **kwargs)
		recip = str(recipient)
		try: self._activeProtocols[recip].append(proto)
		except KeyError: self._activeProtocols[recip] = [proto]
		if type(timeout) == int: TThread(target = self._threadTimeout, loop = False,
			args=(recip, proto, timeout)).start()
		return proto

	def getSpawnedProtocol(self, recipient: TAddress = None, protocolClass = None):
		recip = str(recipient)
		try: self._activeProtocols[recip]
		except KeyError: return None
		for spawnedProtocol in self._activeProtocols[recip]:
			if spawnedProtocol.__class__.__name__.upper() == protocolClass.__name__.upper():
				return spawnedProtocol
		return None

	def invalidateProtocol(self, recipient: TAddress = None, protocolClass = None):
		recip = str(recipient)
		try: self._activeProtocols[recip]
		except KeyError: return -1 # Unable to find recipient
		for proto in self._activeProtocols[recip]:
			if proto.__class__.__name__.upper() == protocolClass.__class__.__name__.upper():
				del self._activeProtocols[recip][self._activeProtocols[recip].index(proto)]
				return 1 # Deleted a protocol instance
		return 0 # No work was done

	def _threadTimeout(self, recipient: str = None, proto = None, timeout: float = 5):
		time.sleep(timeout)
		self.invalidateProtocol(recipient, proto)

	def _broadcastReceive(self):
		if self._broadcastSocket.closed():
			self._broadcastReceiveThread.stop()
			return
		addr, data = self._broadcastSocket.receiveData()
		if data is None or not len(data): return
		self.broadcastReceive(addr, data)

	def _generalReceive(self):
		if self._generalSocket.closed():
			self._generalReceiveThread.stop()
			return
		addr, data = self._generalSocket.receiveData()
		if data is None or not len(data): return
		self.generalReceive(addr, data)

	def broadcastReceive(self, addr: TAddress = None, data: str = None): raise NotImplementedError()
	def generalReceive(self, addr: TAddress = None, data: str = None): raise NotImplementedError()

class TServer(TNetworkable):

	def __init__(self):
		super().__init__(True, "192.168.6.1")
		self.expectedClients = TClient.Clients
		self._clientsGot = []
		self._confirmedClients = {}
		self._broadcastProtoSaved = super().spawnProtocol(self._broadcastSocket._addr, None, Broadcast_IP, args = (0,))

	def startBroadcasting(self):
		super().spawnThread("Broadcasting", self._broadcastThread, True).start()

	def _broadcastThread(self):
		self._broadcastProtoSaved._step = 0
		self._broadcastProtoSaved.step(self._broadcastSocket, self._broadcastSocket._addr)
		time.sleep(5)

	def broadcastReceive(self, addr: TAddress = None, data: str = None):
		hndl = self._protocolHandler.incomingPacket(data, addr)
		if hndl[0] == 2:
			super().closeThread("Broadcasting")
			super().invalidateProtocol(str(self._broadcastSocket._addr), Broadcast_IP)
			self._broadcastSocket.close()
			print("Server: Done, Found", len(self._clientsGot), "clients which were:", self._clientsGot)
		else: print("Server: So far have:", self._clientsGot)

	def generalReceive(self, addr: TAddress = None, data: str = None):
		hndl = self._protocolHandler.incomingPacket(data, addr)
		print("Server: Handling returned", hndl[0])
		if hndl[0] == 2:
			super().invalidateProtocol(addr, hndl[1])

class TClient(TNetworkable):

	Clients = 0

	def __init__(self):
		TClient.Clients += 1
		super().__init__(False, "192.168.6." + str(TClient.Clients + 1))
		self._serversIP = None

	def keyExchange(self):
		ex = super().spawnProtocol(self._serversIP, None, Key_Exchange, args = (0,))
		clientRSA = RSA(True)
		ex.keys[1] = clientRSA
		print("Client's Public key: ", clientRSA.pubKey(), "\nClient's Private Key: ", clientRSA.privKey(), sep="")
		ex.step(self._generalSocket, self._serversIP)

	def broadcastReceive(self, addr: TAddress = None, data: str = None):
		hndl = self._protocolHandler.incomingPacket(data, addr)
		if hndl[0] == 2:
			super().invalidateProtocol(str(self._broadcastSocket._addr), Broadcast_IP)
			self._broadcastSocket.close()
			print("Client (", self._ip, "): Found server, their ip is ", self._serversIP, " and server found me!", sep="")
			self._serversIP = TAddress(self._serversIP, TPorts.SEND_RECEIVE)
			self.keyExchange()

	def generalReceive(self, addr: TAddress = None, data: str = None):
		hndl = self._protocolHandler.incomingPacket(data, addr)
		print("Client: Handling returned", hndl[0])
		if hndl[0] == 2:
			super().invalidateProtocol(addr, hndl[1])

class ProtocolHandler:

	def __init__(self, isClient: bool = False, selfInstance: TNetworkable = None):
		self._isClient = isClient
		self._instanceOfOwner = selfInstance

	def incomingPacket(self, packet: str = None, sentBy: TAddress = None):
		if type(packet) != str or not Packet.isValidPacket(packet): return -2
		return self._handlePacket(Packet.fromString(packet), sentBy)

	def _handlePacket(self, packet: object = None, sentBy: TAddress = None):
		def _client_Broadcast_IP():
			spawned = self._instanceOfOwner.getSpawnedProtocol(sentBy, Broadcast_IP)
			wasSpawnedPreviously = not spawned is None
			if not wasSpawnedPreviously: spawned = self._instanceOfOwner.spawnProtocol(sentBy, 5, Broadcast_IP, args=(1,))
			if not spawned.isServersTurn(packet._step): return 0
			if not spawned.isProperPacket(packet): return 0
			if spawned._step != packet._step: return 0
			if packet._step == 1:
				ip = packet.getDataAt(0)
				if self._instanceOfOwner.isIP(ip):
					self._instanceOfOwner._serversIP = ip
			if packet._step == 3:
				maybeMyIP = packet.getDataAt(0)
				if maybeMyIP == self._instanceOfOwner._ip: return 2
				else:
					spawned._step = 1
					spawned.step(self._instanceOfOwner._broadcastSocket, sentBy)
					self._instanceOfOwner.invalidateProtocol(sentBy, Broadcast_IP)
			else: spawned.step(self._instanceOfOwner._broadcastSocket, sentBy)
			return 1

		def _server_Broadcast_IP():
			spawned = self._instanceOfOwner.getSpawnedProtocol(sentBy, Broadcast_IP)
			wasSpawnedPreviously = not spawned is None
			if not wasSpawnedPreviously: return 0
			if spawned.isServersTurn(packet._step): return 0
			if not spawned.isProperPacket(packet): return 0
			if spawned._step != packet._step: return 0
			if packet._step == 2:
				ip = packet.getDataAt(0)
				if self._instanceOfOwner.isIP(ip):
					if not ip in self._instanceOfOwner._clientsGot:
						self._instanceOfOwner._clientsGot.append(ip)
					spawned.step(self._instanceOfOwner._broadcastSocket, sentBy, ip)
				spawned._step = 2
			else: spawned.step(self._instanceOfOwner._broadcastSocket, sentBy)
			if len(self._instanceOfOwner._clientsGot) >= self._instanceOfOwner.expectedClients: return 2
			return 1

		def _client_Key_Exchange():
			spawned = self._instanceOfOwner.getSpawnedProtocol(sentBy, Key_Exchange)
			print("Client: Recieved step", packet._step)
			wasSpawnedPreviously = not spawned is None
			if not wasSpawnedPreviously: return 0
			if not spawned.isServersTurn(packet._step): return 0
			if not spawned.isProperPacket(packet): return 0
			if spawned._step != packet._step: return 0
			print("Client: Doing work")
			if packet._step == 2:
				serverPubKey = RSA.addExtraDetailToKey(packet.getDataAt(0), True)
				print("Adding in the servers public RSA key, which is\n", serverPubKey, sep="")
				spawned.keys[0] = RSA.new(False, serverPubKey)
			spawned.step(self._instanceOfOwner._generalSocket, sentBy)
			if packet._step == 4:
				print("Received new UUID from server")
				return 2

		def _server_Key_Exchange():
			spawned = self._instanceOfOwner.getSpawnedProtocol(sentBy, Key_Exchange)
			print("Server: Recieved step", packet._step)
			wasSpawnedPreviously = not spawned is None
			if not wasSpawnedPreviously:
				spawned = self._instanceOfOwner.spawnProtocol(sentBy, 30, Key_Exchange, args=(1,))
				serverRSA = RSA(False)
				spawned.keys[0] = serverRSA
				print("Server's Public key: ", serverRSA.pubKey(), "\nServer's Private Key: ", serverRSA.privKey(), sep="")
			if spawned.isServersTurn(packet._step): return 0
			if not spawned.isProperPacket(packet): return 0
			if spawned._step != packet._step: return 0
			print("Server: Doing work")
			if packet._step == 3:
				print("A")
				encryptedClientKey = packet.getDataAt(0)
				print("B:", encryptedClientKey)
				decryptedClientKey = spawned.keys[0].decrypt(encryptedClientKey)
				print("C:", decryptedClientKey)
				key = RSA.addExtraDetailToKey(decryptedClientKey, False)
				print("Decrypted Client Key:", key)
				spawned.keys[1] = RSA.new(True, key)
				print("D")
			if packet._step == 5:
				print("Final packet received containiny my new UUID")
				return 2
			else: spawned.step(self._instanceOfOwner._generalSocket, sentBy)

		packetProto = packet._protocol
		if packetProto == "BROADCAST_IP":
			if self._isClient: return (_client_Broadcast_IP(), Broadcast_IP)
			else: return (_server_Broadcast_IP(), Broadcast_IP)
		elif packetProto == "KEY_EXCHANGE":
			if self._isClient: return (_client_Key_Exchange(), Key_Exchange)
			else: return (_server_Key_Exchange(), Key_Exchange)
		else: return (-1, None)

class Protocol:

	@staticmethod
	def allProtocols(): return [_class.__name__.upper() for _class in Protocol.__subclasses__()]

	@staticmethod
	def protocolClassNameFromID(id: int = 0):
		protos = Protocol.allProtocols()
		if id < 0 or id > len(protos): return None
		return protos[id]

	@staticmethod
	def protocolClassFromID(id: int = 0):
		protos = Protocol.__subclasses__()
		if id < 0 or id > len(protos): return None
		return protos[id]

	@staticmethod
	def idFromProtocolName(name: str = None):
		if name is None or type(name) != str or not (name.upper() in Protocol.allProtocols()): return -1
		return Protocol.allProtocols().index(name)

	def __init__(self, step: int = 0, totalSteps: int = 0, serverSteps: int = 0, packetMethods: list = None, *args, **kwargs):
		self._step = step
		self._packets = packetMethods
		self._totalSteps = totalSteps
		self._serverSteps = serverSteps

	def isServersTurn(self, step: int = 0): return step in self._serverSteps

	def isProperPacket(self, pkt: object = None):
		try: return pkt._method in self._packets[pkt._step - 1]
		except IndexError: return False

	def step(self, sender: TSocket = None, receiver: TAddress = None, *args, **kwargs): raise NotImplementedError()

class Broadcast_IP(Protocol):

	def __init__(self, step: int = 0):
		super().__init__(step, 3, (1, 3), (("DATA",), ("CONFIRM",), ("AGREE",)))

	def step(self, sender: TSocket = None, receiver: TAddress = None, confirming: str = "(Unknown)"):
		protoName = self.__class__.__name__.upper()
		self._step += 1
		if self._step == 1: # Server
			Packet("DATA", protoName, self._step).addData(sender._spawnedFrom).finalize(sender, receiver)
		elif self._step == 2: # Client
			Packet("CONFIRM", protoName, self._step).addData(sender._spawnedFrom).finalize(sender, receiver)
		elif self._step == 3: # Server
			Packet("AGREE", protoName, self._step).addData(confirming).finalize(sender, receiver)
		self._step += 1

class Key_Exchange(Protocol):

	def __init__(self, step: int = 0):
		self.keys = [None, None, None]
		# 0 = Server RSA, 1 = Client RSA, 2 = Shared AES
		self.sessionIds = ["", ""]
		# 0 = Server uuid, Client uuid
		super().__init__(step, 0, (2, 4), (("QUERY_DATA",), ("QUERY_RESPONSE",), ("DATA",), ("DATA",), ("DATA",)))

	def session(self, key):
		seed = sha256((key.privKey() + str(random.randint(-(2 ** 64 - 1), 2 ** 64 - 1))).encode("utf-8")).digest()
		rand = random.Random(seed)
		return "".join([rand.choice("0123456789abcdef") for i in range(64)])

	def step(self, sender: TSocket = None, receiver: TAddress = None):
		protoName = self.__class__.__name__.upper()
		self._step += 1
		print("Doing step", self._step)
		if self._step == 1: # Client
			Packet("QUERY_DATA", protoName, self._step).finalize(sender, receiver)
		elif self._step == 2: # Server
			# Server get's their own public key (0)
			Packet("QUERY_RESPONSE", protoName, self._step).addData(self.keys[0].pubKey()).finalize(sender, receiver)
		elif self._step == 3: # Client
			# Client encrypts their private key (1) with the server's public key (0)
			Packet("DATA", protoName, self._step).addData(self.keys[0].encrypt(self.keys[1].privKey())).finalize(sender, receiver)
		elif self._step == 4: # Server
			self.sessionIds[1] = self.keys[2].encrypt(self.session(self.keys[1]))
			Packet("DATA", protoName, self._step).addData(self.sessionIds[1]).finalize(sender, receiver)
		elif self._step == 5: # Client
			self.sessionIds[0] = self.keys[2].encrypt(self.session(self.keys[0]))
			Packet("DATA", protoName, self._step).addData(self.sessionIds[0]).finalize(sender, receiver)
		self._step += 1

class Packet:

	Methods = {
		"ERROR":         -1,
		"CONFIRM":        1,
		"AGREE":          2,
		"DISAGREE":       3,
		"QUERY_DATA":     4,
		"QUERY_RESPONSE": 5,
		"DATA":           6
	}

	@staticmethod
	def methodFromString(mtdName: str = None):
		if mtdName is None or len(mtdName) == 0 or not (mtdName in Packet.Methods.keys()): return -1
		return Packet.Methods[mtdName]

	@staticmethod
	def stringFromMethod(mtdID: int = None):
		if mtdID is None or mtdID < -1 or mtdID > len(Packet.Methods.keys()) - 1: return "ERROR"
		for key, val in Packet.Methods.items():
			if val == mtdID: return key
		return "ERROR"

	@staticmethod
	def fromString(packet: str = None):
		if packet is None or len(packet) < 8: return None
		mtd = Packet.stringFromMethod(int(packet[:2]))
		protoID = int(packet[2:4])
		step = int(packet[4:6])
		numberOfDataPoints = int(packet[6:8])
		packetInstance = Packet(mtd, Protocol.protocolClassNameFromID(protoID), step)
		packetInstance._packetString = packet
		offset = 0
		for i in range(numberOfDataPoints):
			del i
			dataLength = int(packet[8 + offset: 12 + offset]) + 1
			rawData = packet[12 + offset: 12 + offset + dataLength]
			decodedData = base64.b64decode(rawData.encode("utf-8")).decode("utf-8")
			if decodedData.endswith("?"): decodedData = decodedData[:len(decodedData) - 1]
			packetInstance.addData(decodedData)
			offset += 4 + dataLength
		return packetInstance

	@staticmethod
	def isValidPacket(packet: str = None):
		return type(Packet.fromString(packet)) == Packet

	def __init__(self, method: str = None, protocolName: str = None, step: int = 0):
		# Step is the step that the recieving service should do in the protocol
		self._method = method
		self._protocol = protocolName
		self._step = step
		self._packetString = ""
		self._data = []

	def __str__(self):
		return f"Method: {self._method}, Protocol: {self._protocol}, Step: {self._step}\
, Current Packet String: \n{self._packetString}, Data: {self._data}"

	def addData(self, data: str = None):
		if data is None or len(data) == 0: return self
		self._data.append(data)
		return self

	def build(self):
		opt = lambda length, value: "0" * (length - len(str(value))) + str(value)
		data = "" + opt(2, Packet.methodFromString(self._method)) + opt(2, Protocol.idFromProtocolName(self._protocol)) + opt(2, self._step) + opt(2, len(self._data))
		for dataPoint in self._data:
			encodedData = base64.b64encode(dataPoint.encode("utf-8")).decode("utf-8")
			data += opt(4, len(encodedData) - 1) + encodedData
		self._packetString = data
		return self

	def getDataAt(self, index: int = 0):
		if index < 0: index = 0
		if index >= len(self._data): index = len(self._data) - 1
		if index == -1: raise LookupError(f"Unable to get data at index {index}")
		return self._data[index]

	def send(self, socket: TSocket = None, toSendItTo: TAddress = None):
		if socket is None or self._packetString is None or len(self._packetString) == 0: return
		print("Sending Packet:", self._packetString)
		socket.sendData(toSendItTo, self._packetString)
		return self

	def finalize(self, socket: TSocket = None, toSendItTo: TAddress = None): self.build().send(socket, toSendItTo)
