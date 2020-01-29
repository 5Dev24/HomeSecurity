import base64, binascii
from ..codes import LogCode, Networking
from . import protocol as _protocol

class Packet:
	"""
	Used to be sent as data for steps in a protocol
	"""

	@staticmethod
	def fromString(packet: str = None):
		"""
		Tries to generate a packet from a string

		Args:
			packet (str): The raw packet

		Returns:
			Packet: The built packet, None if packet was an invalid format or decoded improperly
		"""
		if packet is None or type(packet) != str or len(packet) < 8: return None # IF packet is None or doesn't meet minimum packet length
		try: # Catch errors from casting or base 64 decoding
			mtd = int(packet[:2]) # Get the method
			proto = int(packet[2:4]) # Get the protocol
			step = int(packet[4:6]) # Get the step
			numberOfDataPoints = int(packet[6:8]) # Get the number of data points in the packet
			packetInstance = Packet(mtd, proto, step) # Create a packet object with this data
			offset = 0 # Current data read offset
			for i in range(numberOfDataPoints): # Loop x times where x is the number of data points
				del i # Remove unused i
				dataLength = int(packet[8 + offset: 12 + offset]) + 1 # Find the length of the data
				rawData = packet[12 + offset: 12 + offset + dataLength] # Read for that length of the data
				data = base64.b64decode(rawData) # Decode the data from base64
				try: # Catch error for decoding as utf-8
					decodedUTF8 = data.decode("utf-8") # Try to decode the data as utf-8 data
					packetInstance.addData(decodedUTF8) # Add data to packet
				except UnicodeDecodeError: # If error occurs
					packetInstance.addData(data) # Add raw data decoded data as it couldn't be decoded with utf-8
				offset += 4 + dataLength # Increase offset
			packetInstance.build() # Build the packet as it currently is
			return packetInstance # Return the built packet
		except (ValueError, IndexError, binascii.Error): # Error was thrown
			LogCode(Networking.PATCH_DECODE_FAIL, f"Packet: \"{packet}\"")
			return None # Return none as a part of the packet building process failed

	@staticmethod
	def isValidPacket(packet: str = None):
		"""
		Checks if a packet from a string was built successfully

		Args:
			packet (str): The raw packet

		Returns:
			bool: Whether or not the packet was built successfully
		"""
		return Packet.fromString(packet) is not None # Generate a packet and see if it returned something other than none

	def __init__(self, method: int = 0, protocol: int = 0, step: int = 0):
		"""
		Init

		Args:
			method (int): The method for the packet
			protocol (int): The protocol for the packet
			step (int): Current step of the protocol

		Attributes:
			_method (int): The method
			_protocol (int): The protocol
			_step (int): The step
			_packetString (str): The built packet
			_data (list): All data points added to the packet
		"""
		if type(method) is _protocol.Method: method = method.value # If method is a Method, get the integer representation
		self._method = method # Save method
		self._protocol = protocol # Save protocol
		self._step = step # Save step
		self._packetString = "" # Create empty packet string
		self._data = [] # Create empty list of data points

	def __str__(self):
		"""
		Converts the object to a string

		Returns:
			str: All of the data about the packet
		"""
		return f"Method: {self._method}, Protocol: {self._protocol}, Step: {self._step}, Data: {self._data}, Current Packet String: {self._packetString}" # All data in a string

	def addData(self, data: object = None):
		"""
		Adds data to the packet to for it to be built with

		Args:
			data (object): The data to add, string is preferred

		Returns:
			Packet: The packet
		"""
		if data is None or len(data) == 0: return self # If data is none or length is 0, return self
		self._data.append(data) # Add data to list of data points
		return self # Return self

	def build(self):
		"""
		Builds the packet into a string form and saves it to the _packetString to be sent

		Building must be done in order to get a string version of the packet else it will be nothing, empty

		Returns:
			Packet: The packet
		"""
		opt = lambda length, value: "0" * (length - len(str(value))) + str(value) # Quickly appends zeros so the string is a length
		data = opt(2, self._method) + opt(2, self._protocol) + opt(2, self._step) + opt(2, len(self._data)) # Adds the base data for the packet, all the required data
		for dataPoint in self._data: # Loop through each data point as dataPoint
			if type(dataPoint) is not bytes: dataPoint = str(dataPoint) # Check type to prevent objects that are not strings from being encoded
			if type(dataPoint) is str: dataPoint = dataPoint.encode("utf-8") # If the dataPoint is a string, convert it to a bytearray
			encodedData = base64.b64encode(dataPoint).decode("utf-8") # Use base64 to encode it and then decode it into a utf-8 string
			data += opt(4, len(encodedData) - 1) + encodedData # Add data to the built packet
		self._packetString = data # Packet string
		return self # Return self

	def getDataAt(self, index: int = 0):
		"""
		Reads data at an index

		Args:
			index (int): The index to read

		Returns:
			object: The object that that index and none if the index doesn't exist
		"""
		try: return self._data[index] # Try to return data at an index
		except IndexError: return None # Return none as data requested was at an invalid index

	def send(self, reciever: str = None):
		"""
		Sends the packet's string to an address

		Args:
			reciever (str): The address to send the data to

		Returns:
			Packet: The packet
		"""
		if self._packetString is None or len(self._packetString) == 0: return # If socket is none, packet string is none, or the length of the packet is 0, then return none
		# Send data
		return self # Return self

	def finalize(self, reciever: str = None):
		"""
		Calls both build then send, works as a shortcut

		Args:
			reciever (str): The address to send the data to

		Returns:
			Packet: The packet
		"""
		return self.build().send(reciever) # Builds the packet, sends the packet, then returns self
