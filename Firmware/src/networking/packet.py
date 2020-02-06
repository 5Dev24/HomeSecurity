import base64, binascii
from bluetooth import BluetoothSocket
from .. import codes as _codes
from . import protocol as _protocol

class Packet:

	@staticmethod
	def fromString(packet: str = None):
		if packet is None or type(packet) != str or len(packet) < 8: return None
		try:
			mtd = int(packet[:2])
			proto = int(packet[2:4])
			step = int(packet[4:6])
			numberOfDataPoints = int(packet[6:8])
			packetInstance = Packet(mtd, proto, step)
			offset = 0
			for i in range(numberOfDataPoints):
				dataLength = int(packet[8 + offset: 12 + offset]) + 1
				rawData = packet[12 + offset: 12 + offset + dataLength]
				data = base64.b64decode(rawData)
				try:
					decodedUTF8 = data.decode("utf-8")
					packetInstance.addData(decodedUTF8)
				except UnicodeDecodeError:
					packetInstance.addData(data)
				offset += 4 + dataLength
			packetInstance.build()
			return packetInstance
		except (ValueError, IndexError, binascii.Error):
			_codes.LogCode(_codes.Networking.PACKET_DECODE_FAIL, f"Packet: \"{packet}\"")
			return None

	@staticmethod
	def isValidPacket(packet: str = None):
		return Packet.fromString(packet) is not None

	def __init__(self, method: int = 0, protocol: int = 0, step: int = 0):
		if type(method) is _protocol.Method: method = method.value

		self._method = method
		self._protocol = protocol
		self._step = step
		self._packetString = ""
		self._data = []

	def addData(self, data: object = None):
		if data is None or len(data) == 0: return self
		self._data.append(data)
		return self

	def getDataAt(self, index: int = 0):
		try: return self._data[index]
		except IndexError: return None

	def build(self):
		opt = lambda length, value: "0" * (length - len(str(value))) + str(value)
		data = opt(2, self._method) + opt(2, self._protocol) + opt(2, self._step) + opt(2, len(self._data))

		for dataPoint in self._data:
			if type(dataPoint) is not bytes: dataPoint = str(dataPoint)
			if type(dataPoint) is str: dataPoint = dataPoint.encode("utf-8")

			encodedData = base64.b64encode(dataPoint).decode("utf-8")
			data += opt(4, len(encodedData) - 1) + encodedData

		self._packetString = data
		return self

	def send(self, socket: BluetoothSocket = None):
		if self._packetString is None or len(self._packetString) == 0: return
		self.build()
		socket.send(self._packetString)
		return self
