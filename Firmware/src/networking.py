from __future__ import annotations
import socket
from .crypt import AES, RSA
from threading import Thread, Timer, Event
from .error import Error, Codes
import time
import random
import string

# T at the beginning of each class means theoretical

class TPorts:

	SEND_RECIEVE = 2
	ENCRYPTED_SEND_RECIEVE = 4
	SERVER_BROADCAST = 6

class TAddress:

	allAddresses = []

	@staticmethod
	def isRegisteredAddress(addr: str = "", port: int = 0):
		for addr in TAddress.allAddresses:
			if addr.addr == addr and addr.port == port: return True
		return False

	def __init__(self, addr: str = "", port: int = 0):
		self.addr = (addr, port)
		TAddress.allAddresses.append(self)

	def free(self):
		TAddress.allAddresses.remove(self)
		del self

class TData:

	def __init__(self, data: str = ""):
		self.data = data
		self._read = False

	def get(self):
		self._read = True
		return self.data

class TSocket:

	allSockets = []

	@staticmethod
	def getSocketFromAddr(addr: str = "", port: int = 0):
		if TAddress.isRegisteredAddress(addr, port):
			for sock in TSocket.allSockets:
				if sock._addr.addr == addr and sock._addr.port == port: return sock
		return None

	def __init__(self, addr: str = "", port: int = 0):
		self._addr = TAddress(addr, port)
		self._dataHistroy = []
		self._lastDataRecieved = None
		self._recieveEvent = Event()
		self._recievers = 0

	def recieve(self, data: TData = None):
		if type(data) != TData: return
		self._dataHistroy.append(data)
		self._lastDataRecieved = data
		while self._recieveEvent.is_set(): continue
		self._recieveEvent.set()

	def recieveData(self):
		if self._recievers > 1:
			print("2 Threads Listening For Data!")
			return None
		got = None
		self._recievers += 1
		while got is None:
			self._recieveEvent.wait()
			got = self._lastDataRecieved
		self._lastDataRecieved = None
		self._recieveEvent.clear()
		self._recievers -= 1
		return got

	def send(self, reciever: TAddress = None, data: TData = None):
		if type(reciever) != TSocket: return
		if type(data) != TData: return
		self.sendData(reciever, data)

	def sendData(self, reciever: object = None, data: TData = None):
		Thread(target=reciever.recieve, args=(data)).start()

class TNetworkable:

	def __init__(self, isServer: bool = False):
		self._isServer = isServer
		self._broadcastSocket = TSocket("<broadcast>", TPorts.SERVER_BROADCAST)

class TServer(TNetworkable):

	def __init__(self):
		super().__init__(True)

	def onBroadcastListeningThread(self):
		pass

	def _communicationThread(self, addr: TAddress = None):
		senderSock = TSocket(addr.addr, addr.port)
		while True:
			data = senderSock.recieveData()
			print("Got Data: \"" + data + '"')

'''
Unable to continue use of code due to not being able to starts ports on machine

Theoretical sockets will be used with 100% accurate data transformation 
'''

class Ports:

	SEND_RECIEVE =           8082
	ENCRYPTED_SEND_RECIEVE = 8084
	SERVER_BROADCAST =       8086

	@staticmethod
	def fastSocket(addr: str = "", port: int = 0):
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.connect((addr, port))
		return s

class Networkable:

	def __init__(self, isServer: bool = False):
		if isServer:
			self._broadcastSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
			self._broadcastSocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
			self._broadcastSocket.settimeout(60)
			self._broadcastSocket.bind(("", Ports.SERVER_BROADCAST))
		self._directSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self._directSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self._directSocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
		self._directSocket.bind(("", Ports.SERVER_BROADCAST))
		self._isServer = isServer
		self._threads = {}
		print("Starting To Listen!")
		if not isServer: self.listenOn("direct", self._directSocket)
		print("Direct Thread Started!")

	def sendDataOn(self, data: str = None, sock: socket.socket = None): sock.send(data.encode("utf-8"))

	def broadcastData(self, data: str = None):
		self._broadcastSocket.sendto(data.encode("utf-8"), ("<broadcast>", Ports.SERVER_BROADCAST))

	def listenOn(self, name: str = None, sock: socket.socket = None):
		name += "-THREAD"
		listenThread = Thread(target = self._listenThread, args=(name, sock))
		listenThread.start()
		self._threads[name] = [True, listenThread]

	def _listenThread(self, name: str = None, sock: socket.socket = None):
		print("SOCKET OBJECT:", sock)
		sock.listen(5)
		while name in self._threads and self._threads[name][0]:
			print("Listening!")
			data, addr = sock.recv(1024)
			data = data.decode("utf-8")
			if not len(data): continue
			print("Recieved data from ", addr, ", it was \"", data, '"', sep = '')
			pkt = Packet.fromString(data)
			if pkt is None:
				print("Invalid packet!")
				continue
			else: self.onPacketRecieved(pkt, Ports.fastSocket(addr[0], addr[1]))
		self.closeThread(name)

	def closeThread(self, name: str = None):
		name += "-THREAD"
		if name in self._threads:
			self._threads[name][0] = False
			self._threads[name][1]._stop()
			del self._threads[name]

	def onPacketRecieved(self, pkt: Packet = None, pktFrom: socket.socket = None): raise NotImplementedError

class Server(Networkable):

	def __init__(self, expectedClients: int = 0):
		super().__init__(True)
		self._broadcastThreadInst = None
		self._expectedClient = expectedClients

	def beginBroadcast(self):
		self._broadcastThreadInst = Thread(target = self._broadcastThread)
		self._broadcastThreadInst.start()
		#Broadcast_IP(1, 1).step(self._broadcastSocket)

	def _broadcastThread(self):
		foundClients = 0
		while foundClients < self._expectedClient:
			print("Broadcasting! Found", foundClients, "clients!")
			Broadcast_IP(1).step(self._broadcastSocket, "")

	def onPacketRecieved(self, pkt: Packet = None, pktFrom: socket.socket = None):
		proto = Protocol.protocolClassFromID(pkt._protocol)
		if proto is None:
			print("S: Invalid protocol!")
			return
		else:
			print("S: Creating instance of protocol")
			protoInst = proto(pkt._step)
			print("S: [1/2] Stepping")
			protoInst.step(pktFrom)
			print("S: [2/2] Stepping")

class Client(Networkable):

	def __init__(self):
		super().__init__(False)

	def onPacketRecieved(self, pkt: Packet = None, pktFrom: socket.socket = None):
		proto = Protocol.protocolClassFromID(pkt._protocol)
		if proto is None:
			print("C: Invalid protocol!")
			return
		else:
			print("C: Creating instance of protocol")
			protoInst = proto(pkt._step)
			print("C: [1/2] Stepping")
			protoInst.step(pktFrom)
			print("C: [2/2] Stepping")

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
		if name is None or not (name in Protocol.allProtocols()): return -1
		return Protocol.allProtocols().index(name) - 1

	def __init__(self, step: int = 0, *args, **kwargs):
		self._step = step

	def isServersTurn(self): raise NotImplementedError

	def step(self, reciever: socket.socket = None): raise NotImplementedError

class Broadcast_IP(Protocol):

	def __init__(self, step: int = 0, exceptedClients: int = 1):
		super().__init__(step)
		self._possibleIPs = []
		self._expectedClients = exceptedClients

	def step(self, sender: socket.socket = None, reciever: socket.socket = None):
		S = self._step
		N = self.__class__.__name__.upper()
		nS = S + 1
		if S == 1:
			sender.sendto(bytes(Packet("BROADCAST_IP", N, nS, reciever).build()._packetString, "utf-8"), ('<broadcast>', Ports.SERVER_BROADCAST))
		elif S == 2:
			Packet("CONFIRM", N, nS, sender).build().send()
		elif S == 3:
			Packet("AGREE", N, nS, sender).build().send()

	def isServersTurn(self):
		return self._step % 2 == 1

class Key_Exchange(Protocol):

	def __init__(self, step: int = 0, clientKey: str = None, serverKey: str = None):
		self.keys = (clientKey, serverKey)
		super().__init__(step)

	def _generateAESFromKeys(self):
		longKey = "".join(self.keys) # Merges both keys together
		pseudoRandomNumber = "".join([ord(c) for c in longKey]) # Get the unicode code point for each character and put them together
		random.seed(pseudoRandomNumber) # Set the random see to be the pseudo random number
		split = [] # Empty split
		split[:] = pseudoRandomNumber # Split the pseudo random number into each number
		ranLength = len(longKey) * 2 # The random length is the length of the keys multiplied by 2
		ran = random.randint(int("1" + ("0" * (ranLength - 1)), int("9" * int(ranLength))), 2) # Generate a new random seed from the pseudo random number
		random.seed(ran) # Set the new seed
		newKey = [] # Empty new key
		newKey[:] = " " * len(longKey) # Create an empty list of empty characters
		characters = string.punctuation + string.digits + longKey + string.ascii_letters # Make a new list of characters
		while newKey.count(" "): # While the new key still has an empty index that can be written to
			newKey[newKey.index(" ")] = characters[random.randint(0, len(longKey) - 1)] # Set the next empty index to be a random character from the character list
		return AES("".join(newKey)) # Create a new AES object using the newly made pseudo random key

	def step(self, reciever: socket.socket = None):
		S = self._step # Step
		N = self.__class__.__name__.upper() # Name of protocol
		nS = S + 1 # Next step
		if S == 1: # Client
			Packet("QUERY_DATA", N, nS, reciever).addData("SERVER_RSA_KEY").build().send()
		elif S == 2: # Server
			# Get server's public rsa key
			Packet("QUERY_RESPONSE", N, nS, reciever).addData("Server's RSA key").build().send()
		elif S == 3: # Client
			# Use server's rsa key to encrypt client rsa key
			Packet("DATA", N, nS, reciever).addData("Their key encrypted with the server's RSA key").build().send()
		elif S == 4: # Server
			# Decrypt client's rsa key using server's private key
			# Use client's rsa key to encrypt a random message
			Packet("DATA", N, nS, reciever).addData("Random string encrypted with the clients RSA key").build().send()
		elif S == 5: # Client
			# Decrypt the random message sent by the server
			# Send back the message
			Packet("CONFIRM", N, nS, reciever).addData("Decrypted random string sent originally by server").build().send()
		elif S == 6: # Server
			# Server checks if they match
			# If True
			Packet("AGREE", N, S, reciever).build().send()
			# Generate new, random, AES key and encrypt it with the client's rsa key
			# Generate a random message and encrypt it with the AES key
			Packet("DATA", N, nS, reciever).addData("Encrypted AES key").addData("Message encrypted with AES").build().send()
			# If False
			#Packet("DISAGREE", N, 1, reciever).build().send()
		elif S == 7: # Client
			# Decrypts the AES key using their private key
			# Decrypts message encrypted with AES
			Packet("CONFIRM", N, nS, reciever).addData("Decrypted message").build().send()
		elif S == 8: # Server
			# Verifies that the messages match
			# If True
			Packet("AGREE", N, nS, reciever).build().send()
			# If False
			#Packet("DISAGREE", N, 6, reciever).build().send()
			#self._step = 6
			#self.step(reciever)
		elif S == 9: # Client
			# Gets the previously sent unique ID for communication
			# DEAD Packet("DATA", N, nS, reciever).addData("The client's unique id").build().send()
			pass
		elif S == 10: # Server
			# Verfy that the unique id sent by the client matches one in the database (local file)
			# If True
			# Client is now trusted
			# DEAD Packet("AGREE", N, S, reciever).build().send()
			# Generate new unique id to be used for next communication
			# DEAD Packet("DATA", N, nS, reciever).addData("Client's new unique id").build().send()
			# If False
			# Decrease number of remaining tries, if tries <= 0: halt communications (Default number of tries = 3)
			# Packet("DISAGREE", N, 9, reciever).build().send()
			pass
		elif S == 11: # Client
			# Client gets id and save it, then sends it back to verify they have the same unique id
			Packet("CONFIRM", N, nS, reciever).addData("The Client's new unique id, checking").build().send()
		elif S == 12: # Server
			# Verify that the new ids match
			# If True
			Packet("AGREE", N, nS, reciever).build().send()
			# Save unique id to database for next communication
			# If False
			# Packet("DISAGREE", N, 11, reciever).addData("Client's new unique id").build().send()
		elif S == 13: # Client
			# Save new key to file
			Packet("CONFIRM", N, nS, reciever).build().send()
		elif S == 14: # Server
			reciever.close() # Close connection

	def isServersTurn(self):
		return self._step % 2 == 0

class Packet:

	Methods = {
		"ERROR":         -1,
		"EMPTY":          0,
		"CONNECT":        1,
		"CONFIRM":        2,
		"AGREE":          3,
		"DISAGREE":       4,
		"DISCONNECT":     5,
		"BROADCAST_IP":   6,
		"QUERY_DATA":     7,
		"QUERY_RESPONSE": 8,
		"DATA":           9
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
		mtd = int(packet[:2])
		protoID = int(packet[2:4])
		step = int(packet[4:6])
		numberOfDataPoints = int(packet[6:8])
		packet = Packet(mtd, Protocol.protocolClassNameFromID(protoID), step, None)
		offset = 0
		for i in range(numberOfDataPoints - 1):
			del i
			dataLength = int(packet[8 + offset: 12 + offset])
			packet.addData(packet[12 + offset: 12 + offset + dataLength])
		return packet

	def __init__(self, method: str = None, protocolName: str = None, step: int = 0, sock: socket.socket = None):
		# Step is the step that the recieving service should do in the protocol
		self._method = method
		self._protocol = Protocol.idFromProtocolName(protocolName)
		self._step = step
		self._packetString = ""
		self._sock = sock
		self._data = []

	def addData(self, data: str = None):
		if data is None or len(data) == 0: return self
		self._data.append(data)
		return self

	def build(self):
		opt = lambda length, value: "0" * (length - len(str(value)))
		data = opt(2, self._method) + opt(2, self._protocol) + opt(2, self._step) + opt(2, len(self._data))
		for dataPoint in self._data:
			data += opt(4, len(dataPoint)) + dataPoint
		self._packetString = data
		return self

	def send(self):
		if self._sock is None or self._packetString is None or len(self._packetString) == 0: return
		self._sock.send(bytes(self._packetString, "utf-8"))
		del self