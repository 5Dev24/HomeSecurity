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
			"optional": { "debug": "boolean" }
		}
	})
	parser.parse(sys.argv[1:])
	parser.execute()

	debug = parser.readVariable("debug")
	builtins.DEBUGGING = debug
	if debug:
		print("Debugging enabled!")

	if parser.readVariable("server"):
		server = Server()
		server.startBroadcasting()
	else:
		Client()

def install():
	pass

if __name__ == "__main__": main()
