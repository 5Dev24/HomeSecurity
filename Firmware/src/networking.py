from __future__ import annotations
import socket
from .crypt import AES, RSA
from threading import Thread, Timer, Event
from .error import Error, Codes
import time
import random
import string
import re
import traceback

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
		del self

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
	def getSocket(addr: TAddress):
		for sock in TSocket.allSockets:
			if sock._addr == addr:
				return sock
		return TSocket.createNewSocket(addr)

	@staticmethod
	def createNewSocket(addr: TAddress):
		sock = TSocket(addr)
		TSocket.allSockets.append(sock)
		return sock

	def __init__(self, addr: TAddress = None):
		self._addr = addr
		self._dataHistroy = []
		self._lastDataRecieved = None
		self._recieveEvent = Event()
		self._recievers = 0
		self._callbackID = random.randint(-1 * (2 ** 32), 2 ** 32)

	def __str__(self):
		return "Address: " + str(self._addr) + ", Data History: " + str(self._dataHistroy) + ", Last Data Recieved: " + str(self._lastDataRecieved) + ",\n\
Recieve Event Set: " + str(self._recieveEvent.is_set()) + ", Recievers: " + str(self._recievers) + ",\n\
and Callback ID: " + str(self._callbackID)

	def recieve(self, addr: TAddress = None, data: TData = None):
		if not (type(data) is TData): return
		data = data.get()
		if data is None:
			print("Data was already read before we recieved it, was this a broadcasted message?")
			return
		self._dataHistroy.append([addr, data])
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
				print("Socket: " + str(sock))
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
					print("Theoretical Thread threw an error (1), closing thread\n" + traceback.format_exc())
					break
		else:
			try: self._target(*self._args, **self._kwargs)
			except BaseException:
				print("Theoretical Thread threw an error (2), closing thread\n" + traceback.format_exc())
		self.stop()
		del self._internalThread, self._target, self._args, self._kwargs

	def start(self):
		self._internalThread.start()
		self._running = True

class TNetworkable:

	def __init__(self, isServer: bool = False, fakeRealIP: str = None):
		self._isServer = isServer
		self._ip = fakeRealIP
		self._broadcastSocket = TSocket.createNewSocket(TAddress("<broadcast>", TPorts.SERVER_BROADCAST))
		self._networkingThreads = {}
		self._activeProtocols = {}
		'''
		{
			TAddress: [
				Protocol,
				Protocol
			],
			TAddress: [
				Protocol
			]
		}
		'''

	def isIP(self, ipaddr: str = None):
		if ipaddr is None or type(ipaddr) != str or not len(ipaddr): return False
		return re.match("^\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}", ipaddr)

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
		try: self._activeProtocols[recipient].append(proto)
		except KeyError: self._activeProtocols[recipient] = [proto]
		index = len(self._activeProtocols[recipient]) - 1
		if type(timeout) is int: TThread(target = self._threadTimeout, loop = False, args=(recipient, index, timeout)).start()
		return [proto, index]

	def hasProtocolSpawned(self, recipient: TAddress = None, protocolClass = None):
		for spawnedProtocol in self._activeProtocols[recipient]:
			if spawnedProtocol.__class__.__name__.upper() == protocolClass.__class__.__name__.uper():
				return [True, spawnedProtocol]
		return [False, None]

	def _threadTimeout(self, recipient: TAddress = None, protoIndex: int = 0, timeout: float = 5):
		time.sleep(timeout)
		self._activeProtocols[recipient][protoIndex].destroy()
		self._activeProtocols[recipient][protoIndex] = None

class TServer(TNetworkable):

	def __init__(self):
		super().__init__(True, "192.168.6.60")

	def startBroadcasting(self):
		super().spawnThread("Broadcasting", self._broadcastOutThread, False).start()

	def _broadcastOutThread(self):
		while True:
			print("Server 0: Broadcasting IP Address")
			proto, index = super().spawnProtocol(self._broadcastSocket._addr, 5, Broadcast_IP, args= (0, 1))
			proto.step(self._broadcastSocket, self._broadcastSocket._addr)
			time.sleep(3)

	def _broadcastInThread(self):
		while True:
			print("Server 2: Listening For Broadcast Responses")
			addr, data = self._broadcastSocket.recieveData()
			if data is None or not len(data):
				print("Server 2: No data or invalid data was gotten from recieveData function")
				continue
			sock = TSocket.getSocket(addr)
			if Packet.isValidPacket(data):
				print("Server 2: Got a valid packet back")
				packet = Packet.fromString(data)
			else:
				print("Server 2: Got an invalid packet back")
				sock.sendDataProtected(self._broadcastSocket, "!")

	def _communicationThread(self, thrdName: str = None, addr: TAddress = None):
		senderSock = TSocket.getSocket(addr)
		while True:
			addr, data = senderSock.recieveData()
			if data is None or not len(data):
				print("Server 1: No data or invalid data was gotten from recieveData function")
				continue
			print("Server 1: Got Data: \"" + data + "\" from \"" + str(addr) + '"')
			super().closeThread(thrdName)
			break

class TClient(TNetworkable):

	def __init__(self):
		super().__init__(False, "192.168.6.62")

	def waitForServer(self):
		T = TThread(self._waitingForServerThread)
		T.start()
		try: self._networkingThreads["ServerListening"].stop()
		except KeyError: pass
		self._networkingThreads["ServerListening"] = T

	def _waitingForServerThread(self):
		while True:
			print("Client 0: Waiting!")
			addr, data = self._broadcastSocket.recieveData()
			if data is None or not len(data):
				print("Client 0: No data or invalid data was gotten from recieveData function")
				continue
			print("Client 0: Got Data: \"" + data + "\" from \"" + str(addr) + '"')
			if super().isIP(data):
				print("Client 0: Got servers ip address, its " + data)
				print("Client 0: Sending response to tell server that I exist and that I got the IP Address")
				super().closeThread("ServerListening")
				break

class Destroyable:

	def __init__(self):
		self._destroying = False

	# Source: https://stackoverflow.com/a/2704528
	def __getattribute__(self, name: str = None):
		try: attribute = object.__getattribute__(self, name)
		except RecursionError: return object.__getattribute__(self, name)
		destroying = False
		try: destroying = self._destroying
		except AttributeError: pass
		if destroying: return lambda: () if hasattr(attribute, "__call__") else None
		else:
			if hasattr(attribute, "__call__"):
				def handle(*args, **kwargs):
					return attribute(*args, **kwargs)
				return handle
			else: return attribute

	def destroy(self):
		self._destroying = True

class Protocol(Destroyable):

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

	def step(self, sender: TSocket = None, reciever: TAddress = None):
		S = self._step
		N = self.__class__.__name__.upper()
		nS = S + 1
		print(str(sender._addr) + ": Doing step " + str(S) + ", sending to " + str(reciever))
		if S == 1:
			Packet("BROADCAST_IP", N, nS, sender, reciever).build().send()
		elif S == 2:
			Packet("CONFIRM", N, nS, sender, reciever).build().send()
		elif S == 3:
			Packet("AGREE", N, nS, sender, reciever).build().send()
		else: super(Broadcast_IP, self).destroy()

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

class Packet(Destroyable):

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
		try:
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
		except ValueError: return None

	@staticmethod
	def isValidPacket(packet: str = None):
		return Packet.fromString(packet) != None

	def __init__(self, method: str = None, protocolName: str = None, step: int = 0, sender: TSocket = None, reciever: TAddress = None):
		# Step is the step that the recieving service should do in the protocol
		self._method = method
		self._protocol = Protocol.idFromProtocolName(protocolName)
		self._step = step
		self._packetString = ""
		self._sender = sender
		self._reciever = reciever
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
		self._sender.sendDataProtected(self._reciever, self._packetString)
		del self
