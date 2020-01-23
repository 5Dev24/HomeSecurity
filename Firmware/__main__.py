#!usr/bin/python3

import sys, builtins
from src.parsing import ArgumentParser
from src.networking import Server, Client, CleanDeviceID

def main():
	parser.parse(sys.argv[1:])
	code = parser.execute()

	debug = parser.readVariable("debug")
	builtins.DEBUGGING = debug
	if debug:
		print("Debugging enabled!")

	if code < 0:
		if debug:
			print("Device failed to start, parse code", code)
		return # Exit

	if code == 0:
		from src.logging import Log, LogType

		deviceData = _readDeviceInfo()
		if deviceData[0]:
			decvID, decvServer = deviceData[1:]
			Log(LogType.Info, "Device id is %s and device is a %s" % (decvID, "server" if decvServer else "client")).post()
			builtins.ISSERVER = decvServer
			if decvServer:
				Server().startBroadcasting()
			else:
				Client()
		else:
			Log(LogType.Warn, "Device hasn't been setup yet, please do so with \"--install\"").post()

def _readDeviceInfo():
	from src.file import DeviceInfoFormat, FileSystem, File
	exists = File.Exists(FileSystem, "deviceinfo.dat")
	if exists:
		deviceInfoFile = File.GetOrCreate(FileSystem, "deviceinfo.dat")
		deviceInfoFormat = DeviceInfoFormat.loadFrom(deviceInfoFile)
		devcID = deviceInfoFormat.get("id")
		decvServer = deviceInfoFormat.get("server")
		if decvServer is not None: decvServer = decvServer.lower() == "true"
		if devcID is None or decvServer is None:
			return (False,)
		else:
			return (True, CleanDeviceID(decvID), decvServer)
	else:
		return (False,)

def install():
	print("Installing")
	deviceID = parser.readVariable("id")
	serverInstall = parser.readVariable("server")
	force = parser.readVariable("force")
	if force is None: force = False

	if len(deviceID) != 17 or len(deviceID) != 15 or len(deviceID) != 12:
		print("Invalid device ID")
		return

	deviceID = CleanDeviceID(deviceID)

	if type(serverInstall) is not bool:
		print("Invalid server argument")
		return

	from src.logging import Log, LogType
	Log(LogType.Install, "Device ID is " + deviceID + " and Install Type is " + ("Server" if serverInstall else "Client") + " Install").post()

	deviceData = _readDeviceInfo()
	shouldInstall = False
	if deviceID[0] == True:
		devcID, devcServer = deviceData[1:]
		if devcID == deviceID and devcServer == serverInstall:
			Log(LogType.Install, "Device appears to have already been setup previously as %s as a %s. Add \"-force true\" to overwrite install (this will wipe all data)!" % (devcID, "server" if devcServer else "client")).post()
		elif devcID == deviceID:
			Log(LogType.Install, "Device was already setup as " + devcID).post()
		elif devcServer == serverInstall:
			Log(LogType.Install, "Device was already setup as a " + ("server" if devcServer else "client")).post()
		else: shouldInstall = True
	else: shouldInstall = True
	if shouldInstall:
		from src.file import DeviceInfoFormat, FileSystem, File
		File.Delete(FileSystem, "deviceinfo.dat")
		deviceInfoFile = File.Create(FileSystem, "deviceinfo.dat")
		deviceInfoFormat = DeviceInfoFormat({"id": deviceID, "server": str(serverInstall)})
		deviceInfoFormat.write(deviceInfoFile)
		Log(LogType.Install, "Device information has been saved").post()

def logs():
	from src.logging import Log
	print("Dumping 100 logs\nStart Logs")
	for l in Log.AllLogs()[-100:]:
		l.post()
	print("End Logs")

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
