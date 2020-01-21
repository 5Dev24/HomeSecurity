#!usr/bin/python3

import sys, builtins
from src.parsing import ArgumentParser
from src.networking import Server, Client

def main():
	parser.parse(sys.argv[1:])
	code = parser.execute()

	debug = parser.readVariable("debug")
	builtins.DEBUGGING = debug
	if debug:
		print("Debugging enabled!")

	if code < 0: return # Exit

	if code == 0:
		isServer = parser.readVariable("server")
		print("Starting as a", "server" if isServer else "client")

		builtins.ISSERVER = isServer
		if isServer:
			Server().startBroadcasting()
		else:
			Client()

def install():
	print("Installing")
	deviceID = parser.readVariable("id")
	serverInstall = parser.readVariable("server")

	if len(deviceID) < 10:
		print("Invalid device ID")
		return
	if type(serverInstall) is not bool:
		print("Invalid server argument")
		return

	from src.logging import Log, LogType
	Log(LogType.Install, "Device ID is " + deviceID + " and Install Type is " + ("Server" if serverInstall else "Client") + " Install").post()

def logs():
	from src.logging import Log
	print("Dumping 100 logs")
	for l in Log.AllLogs()[-100:]:
		l.post()

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
			"optional": { "debug": "boolean", "id": "string" }
		}
	})
	main()
