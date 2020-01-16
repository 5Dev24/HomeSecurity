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

	if code < 0: # If executing the parser returns a bad exit code
		print("Bad parse code", code) # Display the a bad parse code appeared
		return # Exit

	print("Starting!")

	#if parser.readVariable("server"):
	#	server = Server()
	#	server.startBroadcasting()
	#else:
	#	Client()

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
	Log(LogType.Data, "Device ID is " + deviceID + " and Install Type is " + ("Server" if serverInstall else "Client") + "Install").post()

parser = None

if __name__ == "__main__":
	parser = ArgumentParser(True, {
		"cmds": {
			"install" : lambda: install()
		},
		"vars" : {
			"required": { "server": "boolean" },
			"optional": { "debug": "boolean", "id": "string" }
		}
	})
	main()
