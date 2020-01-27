#!usr/bin/python3

import sys, builtins, re
from src.parsing import ArgumentParser
from src.networking import Server, Client
from codes import General, Installation, Parsing, Exit

def main():
	parser.parse(sys.argv[1:])
	code = parser.execute()

	debug = parser.readVariable("debug")
	builtins.DEBUGGING = debug
	if debug:
		print("Debugging enabled!")

	if code.value > 2:
		Exit(code)

	if code == 1:
		from src.logging import Log, LogType

		deviceData = _readDeviceInfo()
		if deviceData[0]:
			devcID, devcServer = deviceData[1:]
			Log(LogType.Info, "Device id is %s and device is a %s" % (devcID, "server" if devcServer else "client")).post()
			builtins.ISSERVER = devcServer
			if devcServer:
				Server().startBroadcasting()
			else:
				Client()
		else:
			Log(LogType.Warn, "Device hasn't been setup yet, please do so with \"--install\"").post()
			Exit(Installation.HASNT_BEEN)

def _readDeviceInfo():
	from src.file import DeviceInfoFormat, FileSystem, File
	exists = File.Exists(FileSystem, "deviceinfo.dat")
	if exists:
		deviceInfoFile = File.GetOrCreate(FileSystem, "deviceinfo.dat")
		deviceInfoFormat = DeviceInfoFormat.loadFrom(deviceInfoFile)
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
		Exit(Installation.INVALID_ID)

	if type(serverInstall) is not bool:
		print("Invalid server argument")
		Exit(Installation.INVALID_SERVER)

	from src.logging import Log, LogType

	deviceData = _readDeviceInfo()
	shouldInstall = False
	if deviceID[0] and not force:
		devcID, devcServer = deviceData[1:]
		if devcID == deviceID and devcServer == serverInstall:
			Log(LogType.Install, "Device appears to have already been setup previously as %s as a %s. Add \"-force true\" to overwrite install (this will wipe all data)!" % (devcID, "server" if devcServer else "client")).post()
			Exit(Installation.SAME_ID_AND_TYPE)
		elif devcID == deviceID:
			Log(LogType.Install, "Device was already setup as " + devcID).post()
			Exit(Installation.SAME_ID)
		else: shouldInstall = True
	else: shouldInstall = True
	if shouldInstall or force:
		from src.file import DeviceInfoFormat, FileSystem, File
		File.Delete(FileSystem, "deviceinfo.dat")
		deviceInfoFile = File.Create(FileSystem, "deviceinfo.dat")
		deviceInfoFormat = DeviceInfoFormat({"id": deviceID, "server": str(serverInstall)})
		deviceInfoFormat.write(deviceInfoFile)
		Log(LogType.Install, "Device information has been saved").post()
		Exit(Installation.SUCCESS)

def logs():
	from src.logging import Log
	print("Dumping 100 logs\nStart Logs")
	for l in Log.AllLogs()[-100:]:
		l.post()
	print("End Logs")
	Exit(General.SUCCESS)

parser = None

if __name__ == "__main__":
	parser = ArgumentParser(True, {
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
