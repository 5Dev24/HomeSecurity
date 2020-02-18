#!usr/bin/python3

import sys, builtins, re, atexit, random
import src.parsing as _parsing, src.codes as _codes, src.threading as _threading, src.logging as _logging, src.file as _file
from hashlib import sha256

atexit.register(_logging.Finalize)

def main():
	parser.parse(sys.argv[1:])
	code = parser.execute()

	debug = parser.readVariable("debug")
	builtins.DEBUGGING = debug
	if debug:
		_logging.Log(_logging.LogType.Debug, "Device has entered debugging mode!").post()

	if code == _codes.Parsing.SUCCESS or code == _codes.Parsing.NO_EXECUTION:

		deviceData = _readDeviceInfo()
		if deviceData[0]:
			devcMAC, devcServer, devcID = deviceData[1:]
			_logging.Log(_logging.LogType.Info, "Device MAC is %s, device is a %s, and device id is %s" % (devcMAC, "server" if devcServer else "client", devcID)).post()
			builtins.ISSERVER = devcServer
			import src.networking.networkables as _networkables

			net = None
			if devcServer:
				net = _networkables.Server()
			else:
				net = _networkables.Client()
			_logging.Log(_logging.LogType.Info, "Device has been started, connecting").post()
			_threading.SimpleThread(net.connect, False, (devcID,), {}).start()
		else:
			_logging.Log(_logging.LogType.Warn, "Device hasn't been setup yet, please do so with \"--install\"").post()
			_codes.Exit(_codes.Installation.HASNT_BEEN)
	else:
		_codes.Exit(code, "Unable to start")
	try:
		if debug:
			_logging.Log(_logging.LogType.Debug, "Holding main thread", False).post()
		_threading.HoldMain()
	finally:
		if len(_threading.SimpleThread.__threads__) == 0:
			_codes.Exit(_codes.General.SUCCESS, "All threads stopped")
		else:
			_codes.Exit(_codes.Reserved.FORCE_TERMINATE, "Force terminate")

def _readDeviceInfo():
	exists = _file.File.Exists(_file.FileSystem, "deviceinfo.dat")
	if exists:
		deviceInfoFile = _file.File.GetOrCreate(_file.FileSystem, "deviceinfo.dat")
		deviceInfoFormat = _file.DeviceInfoFormat.loadFrom(deviceInfoFile)

		devcMAC = deviceInfoFormat.mac
		devcServer = deviceInfoFormat.server
		devcID = deviceInfoFormat.id

		if type(devcServer) != bool and devcServer is not None: devcServer = devcServer.lower() == "true"
		if devcMAC is None or devcServer is None or devcID is None:
			return (False,)
		else:
			return (True, devcMAC, devcServer, devcID)
	else:
		return (False,)

def _randomID():
	ran = random.Random(random.randint(-(2 ** 64), 2 ** 64))
	seed = sha256(str(ran.randint(-(2 ** 64), 2 ** 64)).encode("utf-8")).digest().hex()
	shuffle = [c for c in seed]
	ran.shuffle(shuffle)
	return "".join([random.choice(shuffle) for i in range(16)])

def install():
	_logging.Log(_logging.LogType.Info, "Starting Install", False).post()
	deviceMac = parser.readVariable("mac")
	serverInstall = parser.readVariable("server")

	force = parser.readVariable("force")
	if force is None: force = False

	deviceMac = re.sub(r"[:.-]", "", deviceMac)

	if len(deviceMac) != 12:
		_codes.Exit(_codes.Installation.INVALID_MAC, f"ID \"{deviceMac}\" was attempted to be used")

	if type(serverInstall) is not bool:
		_codes.Exit(_codes.Installation.INVALID_SERVER)

	deviceData = _readDeviceInfo()
	shouldInstall = False

	if deviceData[0] and not force:
		deviceMac, devcServer = deviceData[1:3]

		if deviceMac == deviceMac and devcServer == serverInstall:
			_logging.Log(_logging.LogType.Install, "Device appears to have already been setup previously as %s as a %s. Add \"-force true\" to overwrite install (this will wipe all data)!" % (deviceMac, "server" if devcServer else "client"), False).post()
			_logging.Log(_logging.LogType.Install, "Device was already setup as %s as a %s" % (deviceMac, "server" if devcServer else "client"))
			_codes.Exit(_codes.Installation.SAME_MAC_AND_TYPE)

		elif deviceMac == deviceMac:
			_logging.Log(_logging.LogType.Install, "Device was already setup as " + deviceMac).post()
			_codes.Exit(_codes.Installation.SAME_MAC)

		else: shouldInstall = True
	else: shouldInstall = True

	if shouldInstall or force:
		_file.File.Delete(_file.FileSystem, "deviceinfo.dat")
		deviceInfoFile = _file.File.Create(_file.FileSystem, "deviceinfo.dat")
		deviceInfoFormat = _file.DeviceInfoFormat()

		deviceInfoFormat.set_mac(deviceMac)
		deviceInfoFormat.set_server(serverInstall)
		deviceInfoFormat.set_id(_randomID())

		deviceInfoFormat.write(deviceInfoFile)
		_logging.Log(_logging.LogType.Install, "Device information has been saved").post()
		_codes.Exit(_codes.Installation.SUCCESS)

def logs():
	_logging.Log(_logging.LogType.Debug, "Dumping 100 logs\nStart Logs").post()
	for l in _logging.Log.AllLogs()[-100:]:
		l.post()
	_logging.Log(_logging.LogType.Debug, "End Logs").post()
	_codes.Exit(_codes.General.SUCCESS)

parser = None

if __name__ == "__main__":
	parser = _parsing.ArgumentParser(True, {
		"cmds": {
			"install" : {
				"invoke": install,
				"description": "Does firmware side intalling, but doesn't do the entire install"
			},
			"logs": {
				"invoke": logs,
				"description": "Displays the last 100 logs"
			}
		},
		"vars" : {
			"optional": { "debug": "boolean", "server": "boolean", "mac": "string", "force": "boolean" }
		},
		"none": lambda: None
	})

	main()
