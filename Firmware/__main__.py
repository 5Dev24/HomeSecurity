#!usr/bin/python3

import sys, builtins
from src.parsing import ArgumentParser
from src.networking import Server, Client

def main():
	parser = ArgumentParser(False, {
		"cmds": {
			"install" : lambda: install()
		},
		"vars" : {
			"required": { "server": "boolean" },
			"optional": { "debug": "boolean", "id": "string" }
		}
	})
	parser.parse(sys.argv[1:])
	parser.execute()

	debug = parser.readVariable("debug")
	builtins.DEBUGGING = debug
	if debug:
		print("Debugging enabled!")

	deviceID = parser.readVariable("id")
	print("Device ID:", deviceID)

	#if parser.readVariable("server"):
	#	server = Server()
	#	server.startBroadcasting()
	#else:
	#	Client()

def install():
	print("Install called")

if __name__ == "__main__": main()
