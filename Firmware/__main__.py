#!usr/bin/python3

import sys, builtins, re, atexit
import src.parsing as _parsing
import src.codes as _codes
import src.networking.networkables as _networkables
import src.networking.threading as _threading
import src.logging as _logging
import src.file as _file

atexit.register(_logging.Finalize)

def main():
	parser.parse(sys.argv[1:])
	code = parser.execute()

	debug = parser.readVariable("debug")
	builtins.DEBUGGING = debug
	if debug:
		print("Debugging enabled!")

	if code == _codes.Parsing.SUCCESS:

		deviceData = _readDeviceInfo()
		if deviceData[0]:
			devcID, devcServer = deviceData[1:]
			_logging.Log(_logging.LogType.Info, "Device id is %s and device is a %s" % (devcID, "server" if devcServer else "client")).post()
			builtins.ISSERVER = devcServer

			if devcServer:
				_networkables.Server().startBroadcasting()
			else:
				_networkables.Client()
			_logging.Log(_logging.LogType.Info, "Device has been started").post()
		else:
			_logging.Log(_logging.LogType.Warn, "Device hasn't been setup yet, please do so with \"--install\"").post()
			_codes.Exit(_codes.Installation.HASNT_BEEN)
	else:
		_codes.Exit(code, "Unable to start")
	try:
		_threading.HoldMain()
	except: # Any error occured in holding (most likely a KeyboardInterrupt)
		if len(_threading.SimpleThread.__threads__) == 0:
			_codes.Exit(_codes.General.SUCCESS, "All threads stopped")
		else:
			_codes.Exit(_codes.Reserved.FORCE_TERMINATE, "Force terminate")

def _readDeviceInfo():
	exists = _file.File.Exists(_file.FileSystem, "deviceinfo.dat")
	if exists:
		deviceInfoFile = _file.File.GetOrCreate(_file.FileSystem, "deviceinfo.dat")
		deviceInfoFormat = _file.DeviceInfoFormat.loadFrom(deviceInfoFile)
		devcID = deviceInfoFormat.get("id")
		devcServer = deviceInfoFormat.get("server")
		if devcServer is not None: devcServer = devcServer.lower() == "true"
		if devcID is None or devcServer is None:
			return (False,)
		else:
			return (True, devcID, devcServer)
	else:
		return (False,)

def install():
	print("Installing")
	deviceID = parser.readVariable("id")
	serverInstall = parser.readVariable("server")
	force = parser.readVariable("force")
	if force is None: force = False

	deviceID = re.sub(r"[:.-]", "", deviceID)

	if len(deviceID) != 12:
		print("Invalid device ID")
		_codes.Exit(_codes.Installation.INVALID_ID)

	if type(serverInstall) is not bool:
		print("Invalid server argument")
		_codes.Exit(_codes.Installation.INVALID_SERVER)

	deviceData = _readDeviceInfo()
	shouldInstall = False
	if deviceData[0] and not force:
		devcID, devcServer = deviceData[1:]
		if devcID == deviceID and devcServer == serverInstall:
			_logging.Log(_logging.LogType.Install, "Device appears to have already been setup previously as %s as a %s. Add \"-force true\" to overwrite install (this will wipe all data)!" % (devcID, "server" if devcServer else "client")).post()
			_codes.Exit(_codes.Installation.SAME_ID_AND_TYPE)
		elif devcID == deviceID:
			_logging.Log(_logging.LogType.Install, "Device was already setup as " + devcID).post()
			_codes.Exit(_codes.Installation.SAME_ID)
		else: shouldInstall = True
	else: shouldInstall = True
	if shouldInstall or force:
		_file.File.Delete(_file.FileSystem, "deviceinfo.dat")
		deviceInfoFile = _file.File.Create(_file.FileSystem, "deviceinfo.dat")
		deviceInfoFormat = _file.DeviceInfoFormat({"id": deviceID, "server": str(serverInstall)})
		deviceInfoFormat.write(deviceInfoFile)
		_logging.Log(_logging.LogType.Install, "Device information has been saved").post()
		_codes.Exit(_codes.Installation.SUCCESS)

def logs():
	print("Dumping 100 logs\nStart Logs")
	for l in _logging.Log.AllLogs()[-100:]:
		l.post()
	print("End Logs")
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
			"required": { "server": "boolean" },
			"optional": { "debug": "boolean", "id": "string", "force": "boolean" }
		}
	})

	main()
