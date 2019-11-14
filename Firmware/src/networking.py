from .crypt import AES, RSA
from hashlib import sha256
from threading import Thread, Timer, Event
import time, random, string, re, traceback, sys, base64

Characters = string.punctuation + string.digits + string.ascii_letters

class TPorts:

	SEND_RECIEVE = 2
	ENCRYPTED_SEND_RECIEVE = 4
	SERVER_BROADCAST = 6

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
	def sendDataProtected(sender: TAddress = None, reciever: TAddress = None, data: str = None):
		for sock in TSocket.allSockets:
			if sock._addr == reciever: # In a real situation, any socket could recieve this message but we're assuming that a socket only accepts messages for itself
				TThread(target=sock.recieve, args=(sender, TData(data, False))).start()
				return True
		return False

	@staticmethod
	def getSocket(getterIP: str = "127.0.0.1", addr: TAddress = None):
		for sock in TSocket.allSockets:
			if sock._addr == addr:
				return sock
		if getterIP is None or type(getterIP) != str: return None
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
		self._lastDataRecieved = None
		self._recieveEvent = Event()
		self._recievers = 0
		self._callbackID = random.randint(-1 * (2 ** 32), 2 ** 32)

	def __str__(self):
		return f"Address: {self._addr}, Data History: {self._dataHistroy}, Last Data Recieved: {self._lastDataRecieved}, \
Recieve Event Set: {self._recieveEvent.is_set()}, Recievers: {self._recievers}, and Callback ID: {self._callbackID}"

	def recieve(self, addr: TAddress = None, data: TData = None):
		if not (type(data) is TData): return
		data = data.get()
		if data is None:
			print("Data was already read before we recieved it, was this meant broadcasted message?")
			return
		self._dataHistroy.append([addr, data])
		while len(self._dataHistroy) > 25: del self._dataHistroy[0]
		self._lastDataRecieved = [addr, data]
		while self._recieveEvent.is_set():
			time.sleep(.5)
			continue
		self._recieveEvent.set()

	def recieveData(self):
		if self._recievers > 1:
			print("2 Threads Listening For Data!")
			return [None, None]
		got = None
		self._recievers += 1
		while got is None:
			self._recieveEvent.wait()
			got = self._lastDataRecieved
		self._lastDataRecieved = None
		self._recieveEvent.clear()
		self._recievers -= 1
		return got

	def sendData(self, reciever: TAddress = None, data: str = None):
		if type(reciever) is str:
			data = reciever
			reciever = self._addr
		if not (reciever is None) and reciever.addr[0] != "<broadcast>":
			return TSocket.sendDataProtected(reciever, data)
		if type(reciever) is TAddress and reciever.addr[0] == "<broadcast>":
			for sock in TSocket.allSockets:
				if sock._addr.addr[0] == self._addr.addr[0] and sock._addr.addr[1] == self._addr.addr[1] and sock._callbackID != self._callbackID:
					sock.recieve(self._addr, TData(data, True))

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

class TNetworkable:

	def __init__(self, isServer: bool = False, fakeRealIP: str = None):
		self._isServer = isServer
		self._ip = fakeRealIP
		self._broadcastSocket = TSocket.createNewSocket(fakeRealIP, TAddress("<broadcast>", TPorts.SERVER_BROADCAST))
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
		print("Client: Timeout:", self.invalidateProtocol(recipient, proto))

class TServer(TNetworkable):

	def __init__(self):
		super().__init__(True, "192.168.6.1")
		self.expectedClients = TClient.Clients
		self._clientsGot = []
		self._confirmedClients = {}
		self._broadcastProtoSaved = super().spawnProtocol(self._broadcastSocket._addr, None, Broadcast_IP, args = (0,))
		print("Server: My IP as a server is 192.168.6.1 and I'm looking for", self.expectedClients, "clients")

	def startBroadcasting(self):
		super().spawnThread("BroadcastingOut", self._broadcastOutThread, True).start()
		super().spawnThread("BroadcastingIn", self._broadcastInThread, True).start()

	def _broadcastOutThread(self):
		print("Server: Broadcasting!")
		self._broadcastProtoSaved._step = 0
		self._broadcastProtoSaved.step(self._broadcastSocket, self._broadcastSocket._addr)
		time.sleep(10)

	def _broadcastInThread(self):
		addr, data = self._broadcastSocket.recieveData()
		if data is None or not len(data): return
		print("Server: Got a packet!", data)
		if self._protocolHandler.incomingPacket(data, addr) == 2:
			super().closeThread("BroadcastingOut")
			super().closeThread("BroadcastingIn")
			super().invalidateProtocol(self._broadcastSocket._addr, Broadcast_IP)
			print("Server: Done, Found", len(self._clientsGot), "clients which were:", self._clientsGot)
		print("Server: So far I have", len(self._clientsGot), "clients", self._clientsGot)

class TClient(TNetworkable):

	Clients = 0

	def __init__(self):
		TClient.Clients += 1
		super().__init__(False, "192.168.6." + str(TClient.Clients + 1))
		self._serversIP = None
		self._serverSockets = [None, None]
		print("Client: My IP as a client is " + self._ip)

	def waitForServer(self):
		super().spawnThread("ServerListening", self._waitingForServerThread, True).start()

	def keyExchange(self):
		if None in self._serverSockets:
			self._serverSockets = [TSocket.createNewSocket(self._ip, TAddress(self._serversIP, TPorts.SEND_RECIEVE)),
				TSocket.createNewSocket(self._ip, TAddress(self._serversIP, TPorts.ENCRYPTED_SEND_RECIEVE))]
		ex = Key_Exchange(0)
		ex.step(self._serverSockets[0], self._serversIP)

	def _waitingForServerThread(self):
		addr, data = self._broadcastSocket.recieveData()
		if data is None or not len(data): return
		print("Client", self._ip, ": Got packet!", data)
		if self._protocolHandler.incomingPacket(data, addr) == 2:
			super().closeThread("ServerListening")
			super().invalidateProtocol(self._broadcastSocket._addr, Broadcast_IP)
			print("Client", self._ip, ": Found server, their ip is", self._serversIP)

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
			print("Client", self._instanceOfOwner._ip, ": Was spawned previously?:", wasSpawnedPreviously)
			if not wasSpawnedPreviously: spawned = self._instanceOfOwner.spawnProtocol(sentBy, 45, Broadcast_IP, args=(1,))
			print("Client", self._instanceOfOwner._ip, ": Was it the servers turn for the packet sent?:", spawned.isServersTurn(packet._step), ", Step On Packet:", packet._step)
			if not spawned.isServersTurn(packet._step): return 0
			print("Client", self._instanceOfOwner._ip, ": Is the packet sending a valid method for this protocol step?:", spawned.isProperPacket(packet))
			if not spawned.isProperPacket(packet): return 0
			print("Client", self._instanceOfOwner._ip, ": Do the steps align?:", spawned._step, packet._step)
			if spawned._step != packet._step: return 0
			if packet._step == 1:
				ip = packet.getDataAt(0)
				if self._instanceOfOwner.isIP(ip):
					self._instanceOfOwner._serversIP = ip
					print("Client", self._instanceOfOwner._ip, ": Got server's IP, It's", ip)
			if packet._step == 3:
				maybeMyIP = packet.getDataAt(0)
				print("Client", self._instanceOfOwner._ip, ": Is", maybeMyIP, "my ip, which is", self._instanceOfOwner._ip)
				if maybeMyIP == self._instanceOfOwner._ip:
					print("Client", self._instanceOfOwner._ip, ": It was my ip :)")
					return 2
				else:
					print("Client", self._instanceOfOwner._ip, ": It wasn't my ip :(")
					spawned._step = 1
			else: spawned.step(self._instanceOfOwner._broadcastSocket, sentBy)
			return 1

		def _server_Broadcast_IP():
			spawned = self._instanceOfOwner.getSpawnedProtocol(sentBy, Broadcast_IP)
			wasSpawnedPreviously = not spawned is None
			print("Server: Was spawned previously?:", wasSpawnedPreviously)
			if not wasSpawnedPreviously: return 0
			print("Server: Was it the clients turn for the packet sent?:", not spawned.isServersTurn(packet._step))
			if spawned.isServersTurn(packet._step): return 0
			print("Server: Is the packet sending a valid method for this protocol step?:", spawned.isProperPacket(packet))
			if not spawned.isProperPacket(packet): return 0
			print("Server: Do the steps align?:", spawned._step, packet._step)
			if spawned._step != packet._step: return 0
			if packet._step == 2:
				ip = packet.getDataAt(0)
				if self._instanceOfOwner.isIP(ip):
					self._instanceOfOwner._clientsGot.append(ip)
					spawned.step(self._instanceOfOwner._broadcastSocket, sentBy, ip)
			else: spawned.step(self._instanceOfOwner._broadcastSocket, sentBy)
			if len(self._instanceOfOwner._clientsGot) >= self._instanceOfOwner.expectedClients: return 2
			return 1

		packetProto = packet._protocol
		if packetProto == "BROADCAST_IP":
			if self._isClient: return _client_Broadcast_IP()
			else: return _server_Broadcast_IP()
		else: return -1

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

	def isProtocolDone(self): self._step > self._totalSteps

	def isServersTurn(self, step: int = 0): return step in self._serverSteps

	def isProperPacket(self, pkt: object = None):
		try: return pkt._method in self._packets[pkt._step - 1]
		except IndexError: return False

	def step(self, sender: TSocket = None, reciever: TAddress = None, *args, **kwargs): raise NotImplementedError

class Broadcast_IP(Protocol):

	def __init__(self, step: int = 0):
		super().__init__(step, 3, (1, 3), (("BROADCAST_IP",), ("CONFIRM",), ("AGREE",)))

	def step(self, sender: TSocket = None, reciever: TAddress = None, confirming: str = "(Unknown)"):
		protoName = self.__class__.__name__.upper()
		self._step += 1
		if self._step == 1: # Server
			Packet("BROADCAST_IP", protoName, self._step).addData(sender._spawnedFrom).finalize(sender, reciever)
		elif self._step == 2: # Client
			Packet("CONFIRM", protoName, self._step).addData(sender._spawnedFrom).finalize(sender, reciever)
		elif self._step == 3: # Server
			Packet("AGREE", protoName, self._step).addData(confirming).finalize(sender, reciever)
		self._step += 1

class Key_Exchange(Protocol):

	def __init__(self, step: int = 0):
		self.keys = [None, None, None]
		# 0 = Server RSA, 1 = Client RSA, 2 = Shared AES
		self.sessionIds = ["", ""]
		# 0 = Server uuid, Client uuid
		super().__init__(step, 0, 5, (("QUERY_DATA",), ("QUERY_RESPONSE",), ("DATA",), ("DATA",), ("DATA",)))

	def session(self, key):
		seed = sha256((key.privKey() + str(random.randint(-(2 ** 64 - 1), 2 ** 64 - 1))).encode("utf-8")).digest()
		rand = random.Random(seed)
		return "".join([rand.choice("0123456789abcdef") for i in range(64)])

	def step(self, sender: TSocket = None, reciever: TAddress = None):
		protoName = self.__class__.__name__.upper()
		nextStep = self._step + 1
		if self._step == 1: # Client
			Packet("QUERY_DATA", protoName, nextStep).addData("PUB_RSA").finalize(sender, reciever)
		elif self._step == 2: # Server
			Packet("QUERY_RESPONSE", protoName, nextStep).addData(self.keys[0].pubKey()).finalize(sender, reciever)
		elif self._step == 3: # Client
			Packet("DATA", protoName, nextStep).addData(self.keys[1].encrypt(self.keys[1].privKey())).finalize(sender, reciever)
		elif self._step == 4: # Server
			self.sessionIds[1] = self.keys[2].encrypt(self.session(self.keys[1]))
			Packet("DATA", protoName, nextStep).addData(self.sessionIds[1]).finalize(sender, reciever)
		elif self._step == 5: # Client
			self.sessionIds[0] = self.keys[2].encrypt(self.session(self.keys[0]))
			Packet("DATA", protoName, nextStep).addData(self.sessionIds[0]).finalize(sender, reciever)

class Packet:

	Methods = {
		"ERROR":         -1,
		"CONFIRM":        1,
		"AGREE":          2,
		"DISAGREE":       3,
		"BROADCAST_IP":   4,
		"QUERY_DATA":     5,
		"QUERY_RESPONSE": 6,
		"DATA":           7
	}

	@staticmethod
	def methodFromString(mtdName: str = None):
		if mtdName is None or len(mtdName) == 0 or not (mtdName in Packet.Methods.keys()): return -1
		return Packet.Methods[mtdName]

	@staticmethod
	def stringFromMethod(mtdID: int = None):
		if mtdID is None or mtdID < -1 or mtdID > len(Packet.Methods.keys()) - 2: return "ERROR"
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
			decodedData = base64.b64decode(rawData.encode("utf-8"), b"-=").decode("utf-8")
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
			encodedData = base64.b64encode(dataPoint.encode("utf-8"), b"-=").decode("utf-8")
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
		socket.sendData(toSendItTo, self._packetString)
		return self

	def finalize(self, socket: TSocket = None, toSendItTo: TAddress = None): self.build().send(socket, toSendItTo)
