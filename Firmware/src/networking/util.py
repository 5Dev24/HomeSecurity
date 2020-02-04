from uuid import getnode
import string

Characters = string.punctuation + string.digits + string.ascii_letters
"""
All of the punctuation, digits, and letters of english
"""

class Ports:
	"""
	Ports used for sending data
	"""

	SEND_RECEIVE = 23001 # Normal sending and receiving data
	"""
	Port used for sending and receiving data for regular protocols that don't need to be done over broadcasting
	"""

	SERVER_BROADCAST = 23002 # For send and receiveing data from a broadcast
	"""
	Port used for only sending and receiving data for the Broadcast_IP protocol to find clients
	"""

def DeviceID():
	return hex(getnode())[2:].upper()

def HumanDeviceID():
	id = DeviceID()
	return ":".join([id[i:i+2] for i in range(0, len(id), 2)]).upper()

def CleanedDeviceID():
	return "".join([c for c in DeviceID() if c.lower() in "0123456789abcdef"]).upper()