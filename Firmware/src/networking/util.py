from uuid import getnode
from bluetooth import find_service, advertise_service, stop_advertising, BluetoothSocket, SERIAL_PORT_CLASS, SERIAL_PORT_PROFILE
from .. import logging as _logging, threading as _threading
import string

Characters = string.punctuation + string.digits + string.ascii_letters
"""
All of the punctuation, digits, and letters of english
"""

def DeviceID():
	return hex(getnode())[2:].upper()

def HumanDeviceID():
	id = DeviceID()
	return ":".join([id[i:i+2] for i in range(0, len(id), 2)]).upper()

def CleanedDeviceID():
	return "".join([c for c in DeviceID() if c.lower() in "0123456789abcdef"]).upper()

def FindValidDevices(clients: bool = True):
	services_found = []
	try:
		services_found = find_service()
	except Exception as e:
		if type(e) != _threading.SimpleClose and type(e) != _threading.MainClose:
			_logging.Log(_logging.LogType.Debug, type(e).__name__ + " raised").post()
		else: raise e
		return {}

	services = {}
	for service in services_found:
		if service["name"] is None or service["host"] is None or service["port"] is None: continue
		if service["name"].startswith("ISM-" + ("Client" if clients else "Server") + "-"):
			services[str(service["host"]) + "~" + str(service["port"])] = service["name"][11:]
	return services

def AdvertiseService(server: bool = True, socket: BluetoothSocket = None, identifier: str = None):
	advertise_service(socket, "ISM-" + ("Server" if server else "Client") + "-" + str(identifier), service_classes=[SERIAL_PORT_CLASS], profiles=[SERIAL_PORT_PROFILE])

def StopAdvertising(socket: BluetoothSocket = None):
	stop_advertising(socket)
