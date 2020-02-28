#!usr/bin/python3

import sys, builtins, re, atexit, random
import src.arguments as _arguments, src.codes as _codes, src.threading as _threading, src.logging as _logging, src.file as _file
from hashlib import sha256

atexit.register(_logging.Finalize)

handler = None

def main(debugging: bool = False):
	builtins.DEBUGGING = debugging
	print("Debugging:", debugging)
	if debugging:
		_logging.Log(_logging.LogType.Debug, "Device has entered debugging mode!").post()

	if handler and handler._good[2]:

		deviceData = _readDeviceInfo()
		if deviceData[0]:
			devcMAC, devcServer, devcID = deviceData[1:]
			_logging.Log(_logging.LogType.Info, "Device MAC is %s, device is a %s, and device id is %s" % (devcMAC, "server" if devcServer else "client", devcID)).post()
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
		_codes.Exit(handler._code[2], "Unable to start", True)
	try:
		if debugging:
			_logging.Log(_logging.LogType.Debug, "Holding main thread", False).post()
		_threading.HoldMain()
	finally:
		if len(_threading.SimpleThread.__threads__) == 0:
			_codes.Exit(_codes.General.SUCCESS, "All threads stopped", True)
		else:
			_codes.Exit(_codes.Reserved.FORCE_TERMINATE, "Force terminate", True)

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

def install(server: bool = True, mac: str = "", force: bool = True):
	_logging.Log(_logging.LogType.Info, "Starting Install", False).post()

	mac = re.sub(r"[:.-]", "", mac)

	if len(mac) != 12:
		_codes.Exit(_codes.Installation.INVALID_MAC, f"ID \"{mac}\" was attempted to be used")

	deviceData = _readDeviceInfo()
	shouldInstall = False

	if deviceData[0] and not force:
		deviceMac, devcServer = deviceData[1:3]

		if deviceMac == mac and devcServer == server:
			_logging.Log(_logging.LogType.Install, "Device appears to have already been setup previously as %s as a %s. Add \"-force true\" to overwrite install (this will wipe all data)!" % (deviceMac, "server" if devcServer else "client"), False).post()
			_logging.Log(_logging.LogType.Install, "Device was already setup as %s as a %s" % (deviceMac, "server" if devcServer else "client"))
			_codes.Exit(_codes.Installation.SAME_MAC_AND_TYPE)

		elif deviceMac == mac:
			_logging.Log(_logging.LogType.Install, "Device was already setup as " + deviceMac).post()
			_codes.Exit(_codes.Installation.SAME_MAC)

		else: shouldInstall = True
	else: shouldInstall = True

	if shouldInstall or force:
		_file.File.Delete(_file.FileSystem, "deviceinfo.dat")
		deviceInfoFile = _file.File.Create(_file.FileSystem, "deviceinfo.dat")
		deviceInfoFormat = _file.DeviceInfoFormat()

		deviceInfoFormat.set_mac(mac)
		deviceInfoFormat.set_server(server)
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

if __name__ == "__main__":
	handler = _arguments.Handler()

	debugging = _arguments.BaseArgument("debug", _arguments.Type.BOOLEAN, False)

	default_cmd = _arguments.Command("main", main, debugging)
	logs_cmd = _arguments.Command("logs", logs)

	is_server = _arguments.BaseArgument("server", _arguments.Type.BOOLEAN)
	mac_address = _arguments.BaseArgument("mac", _arguments.Type.STRING)
	force = _arguments.BaseArgument("force", _arguments.Type.BOOLEAN, False)

	install_cmd = _arguments.Command("install", install, is_server, mac_address, force)

	handler.add_commands(logs_cmd, install_cmd)

	handler.set_default_command(default_cmd)

	handler.lex(sys.argv[1:])
	if handler._good[0]:
		handler.parse()
		if handler._good[1]:
			handler.execute()
			if not handler._good[2]:
				_codes.Exit(handler._code[2], None, True)
		else:
			_codes.Exit(handler._code[1], None, True)
	else:
		_codes.Exit(handler._code[0], None, True)