from __future__ import annotations
import socket
from .crypt import AES, RSA
from threading import Thread, Timer
from .error import Error, Codes
import time
import random
import string

class Ports:

	SERVER_SEND_RECIEVE =           40000
	SERVER_ENCRYPTED_SEND_RECIEVE = 40002
	SERVER_BROADCAST =              40004
	CLIENT_SEND_RECIEVE =           40006
	CLIENT_ENCRYPTED_SEND_RECIEVE = 40008

	@staticmethod
	def fastSocket(addr: str = "", port: int = 0):
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.connect((addr, port))
		return s

class Networkable:

	def __init__(self, isServer: bool = False):
		self._broadcastSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self._broadcastSocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
		self._directSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self._directSocket.bind(("", Ports.SERVER_SEND_RECIEVE if isServer else Ports.CLIENT_SEND_RECIEVE))
		self._directSocket.send("".encode('utf-8'))
		self._isServer = isServer
		self._threads = {}

	def sendDataOn(self, data: str = None, sock: socket.socket = None): sock.send(data.encode("utf-8"))

	def broadcastData(self, data: str = None):
		self._broadcastSocket.sendto(data.encode("utf-8"), ("<broadcast>", Ports.SERVER_BROADCAST))

	def listenOn(self, name: str = None, sock: socket.socket = None):
		listenThread = Thread(target = self._listenThread, args=[name, sock])
		listenThread.start()
		self._threads[name] = [True, listenThread]

	def broadcastOn(self, name: str = None):
		broadcastThread = Thread(target = self._broadcastThread, args=[name])
		broadcastThread.start()
		self._threads[name] = [True, broadcastThread]

	def _broadcastThread(self, name: str = None):
		while name in self._threads and self._threads[name][0]:
			self.broadcastData(socket.gethostbyname(socket.gethostname()))
			time.sleep(5)
		self.closeThread(name)

	def _listenThread(self, name: str = None, sock: socket.socket = None):
		sock.listen(5)
		while name in self._threads and self._threads[name][0]:
			data, addr = sock.recv(2**16)
			data = data.decode("utf-8")
			if not len(data): continue
			print("Recieved data from ", addr, ", it was \"", data, '"', sep = '')
		self.closeThread(name)

	def closeThread(self, name: str = None):
		if name in self._threads:
			self._threads[name][0] = False
			self._threads[name][1]._stop()
			del self._threads[name]

class Server(Networkable):

	def __init__(self):
		super.__init__(True)

class Client(Networkable):

	def __init__(self):
		super.__init__(False)

class Protocol:

	@staticmethod
	def allProtocols(): return [_class.__name__.upper() for _class in Protocol.__subclasses__()]

	@staticmethod
	def protocolClassFromID(id: int = 0):
		protos = Protocol.allProtocols()
		if id < 0 or id > len(protos): return None
		return protos[id]

	@staticmethod
	def idFromProtocolName(name: str = None):
		if name is None or not (name in Protocol.allProtocols()): return -1
		return Protocol.allProtocols().index(name) - 1

	def __init__(self, expectedPacketIDs: tuple = None, step: int = 0):
		self._expectedPacketIDs = () if expectedPacketIDs is None else expectedPacketIDs
		self._step = step

	def isServersTurn(self): raise NotImplementedError

	def step(self, toSendTo: socket.socket = None): raise NotImplementedError

	def incommingPacket(self, packet: str = None): raise NotImplementedError

class Broadcast_IP(Protocol):

	def __init__(self, step: int = 0, exceptedClients: int = 1):
		super().__init__(step)
		self._possibleIPs = []

	def stop(self, toStop: int = 0): self._stop[toStop] = 1

	def step(self, toSendTo: socket.socket = None):
		S = self._step
		N = self.__class__.__name__.upper()
		nS = S + 1
		pass

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

	def step(self, toSendTo: socket.socket = None):
		S = self._step # Step
		N = self.__class__.__name__.upper() # Name of protocol
		nS = S + 1 # Next step
		if S == 1: # Client
			Packet("QUERY_DATA", N, nS, toSendTo).addData("SERVER_RSA_KEY").build().send()
		elif S == 2: # Server
			# Get server's public rsa key
			Packet("QUERY_RESPONSE", N, nS, toSendTo).addData("Server's RSA key").build().send()
		elif S == 3: # Client
			# Use server's rsa key to encrypt client rsa key
			Packet("DATA", N, nS, toSendTo).addData("Their key encrypted with the server's RSA key").build().send()
		elif S == 4: # Server
			# Decrypt client's rsa key using server's private key
			# Use client's rsa key to encrypt a random message
			Packet("DATA", N, nS, toSendTo).addData("Random string encrypted with the clients RSA key").build().send()
		elif S == 5: # Client
			# Decrypt the random message sent by the server
			# Send back the message
			Packet("CONFIRM", N, nS, toSendTo).addData("Decrypted random string sent originally by server").build().send()
		elif S == 6: # Server
			# Server checks if they match
			# If True
			Packet("AGREE", N, S, toSendTo).build().send()
			# Generate new, random, AES key and encrypt it with the client's rsa key
			# Generate a random message and encrypt it with the AES key
			Packet("DATA", N, nS, toSendTo).addData("Encrypted AES key").addData("Message encrypted with AES").build().send()
			# If False
			#Packet("DISAGREE", N, 1, toSendTo).build().send()
		elif S == 7: # Client
			# Decrypts the AES key using their private key
			# Decrypts message encrypted with AES
			Packet("CONFIRM", N, nS, toSendTo).addData("Decrypted message").build().send()
		elif S == 8: # Server
			# Verifies that the messages match
			# If True
			Packet("AGREE", N, nS, toSendTo).build().send()
			# If False
			#Packet("DISAGREE", N, 6, toSendTo).build().send()
			#self._step = 6
			#self.step(toSendTo)
		elif S == 9: # Client
			# Gets the previously sent unique ID for communication
			# DEAD Packet("DATA", N, nS, toSendTo).addData("The client's unique id").build().send()
			pass
		elif S == 10: # Server
			# Verfy that the unique id sent by the client matches one in the database (local file)
			# If True
			# Client is now trusted
			# DEAD Packet("AGREE", N, S, toSendTo).build().send()
			# Generate new unique id to be used for next communication
			# DEAD Packet("DATA", N, nS, toSendTo).addData("Client's new unique id").build().send()
			# If False
			# Decrease number of remaining tries, if tries <= 0: halt communications (Default number of tries = 3)
			# Packet("DISAGREE", N, 9, toSendTo).build().send()
			pass
		elif S == 11: # Client
			# Client gets id and save it, then sends it back to verify they have the same unique id
			Packet("CONFIRM", N, nS, toSendTo).addData("The Client's new unique id, checking").build().send()
		elif S == 12: # Server
			# Verify that the new ids match
			# If True
			Packet("AGREE", N, nS, toSendTo).build().send()
			# Save unique id to database for next communication
			# If False
			# Packet("DISAGREE", N, 11, toSendTo).addData("Client's new unique id").build().send()
		elif S == 13: # Client
			# Save new key to file
			Packet("CONFIRM", N, nS, toSendTo).build().send()
		elif S == 14: # Server
			toSendTo.close() # Close connection

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
		packet = Packet(mtd, Protocol.protocolClassFromID(protoID), step, None)
		offset = 0
		for i in range(numberOfDataPoints - 1):
			del i
			dataLength = int(packet[8 + offset: 12 + offset])
			packet.addData(packet[12 + offset: 12 + offset + dataLength])
		return packet

	def __init__(self, method: str = None, protocolName: str = None, step: int = 0, sock: socket.socket = None):
		# Step is the step that the recieving service should do in the protocol
		self._method = method
		self._protocol = protocolName
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
		data = opt(2, self._method) + opt(2, Protocol.idFromProtocolName(self._protocol)) + opt(2, self._step) + opt(2, len(self._data))
		for dataPoint in self._data:
			data += opt(4, len(dataPoint)) + dataPoint
		self._packetString = data
		return self

	def send(self):
		if self._sock is None or self._packetString is None or len(self._packetString) == 0: return
		self._sock.send(bytes(self._packetString, "utf-8"))
		self._sock.close()
		self._sock = None
		del self

"""
AA BB CC DD | EEEE (F) | GGGG (H) | IIII (J)

No space would actually be pressent, it's just easier to read

All numbers and in decimal, possibility for base64 or hex to store data length in case of large amounts of data needing to be sent

Packet could be cut at any of the |'s 

A = packet code, starts at 1
B = protocol, starts at 1
C = step in protocol, starts at 1
D = how many pieces of data are present, default to 0, maxd is 100 but that should never occur
E, G, I = length of the next piece of data,
	note that a piece of data cannot exceed length 10000 as the
	value goes from 1 to 10000 instead of 0 to 9999 because no
	piece of data would be 0 in length
F, H, J = the data itself

"""

"""
C = Communication: work done over the internet
L = Locally: work done on the machine, locally

Key Exchange/Client Verification <- Name is interchangable
This method prevents against client side impersenation but not server, so maybe client also have a server id?

01. (C) Client requests public rsa key from server
02. (C) Server response with the rsa key
03. (L) Client encrypts their public rsa key with the server's rsa key
04. (C) Client sends back their encrypted public rsa
05. (L) Server decrypts client's encrypted public rsa key
06. (L) Server encrypts a random message with the client's public rsa key
07. (C) Server sends the encrypted message
08. (L) Client decrypts the message
09. (C) Client sends back the decrypted message
10. (L) Server verifies that the messages match, if not: restart from step 1
> Server has client public key
11. (L) Server generates new random AES key and encrypts the AES key with the client's rsa public key
12. (L) Server generates random message and encrypts it with AES using the newly generated key
13. (C) Server sends encrypted AES key and encrypted message
14. (L) Client decrypts AES key and then uses the AES to decrypt the message
15. (C) Client sends back the decrypted message
16. (L) Server verifies messages match, if not: restart from step 11
> Crypto has been sync'd
17. (L) Both generate a new AES key from the client + server key, see Algorithm 1
18. (C) Both send a random message that uses the new AES key to encrypt it
19. (L) Both decrypt and verify
20. (C) Either can object to further communication and restart at 17, else they have been verified
> Client is now trusted
21. (L) Server generates new unique id for next communication
22. (C) Server sends new id
23. (C) Client sends back id to confirm
24. (L) Server confirms or denies, if it denies, restart from step 19
25. (L) Server saves new id
26. (C) Server says id matches and is good
27. (L) Client saves id
> ID for next communication saved
"""

"""
Initial Setup (Installation/Adding New Device(s))

The number of current and new devices to add is known

1. (C) Broadcasts IP until it gets responses from the number of current devices + new devices
2. (C) All client respond that they got the IP
3. (L) For each unique device, the server generates a new client id, for old clients: follow Key Excahnge and get new ids
4. (C) Server sends new client id
5. (L) Client saves new client id
6. (C) Client sends new server id
7. (L) Server saves new server id
-> Now door naming setting up work occur
8. Done
"""

"""
Initial Stepup (No New Devices)

The number of current devices is known

1. (C) Broadcasts IP until it gets responses from the number of current devices
2. (P) Follow Client Verification to verify client
3. Done
"""
