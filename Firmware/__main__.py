#!usr/bin/python3

import sys, builtins
from src.parsing import ArgumentParser
from src.networking import TServer, TClient

def main():
	parser = ArgumentParser(False, { "vars" : { "optional": { "debug": "boolean" } } })
	parser.parse(sys.argv[1:])
	parser.execute()

	debug = parser.readVariable("debug")
	builtins.DEBUGGING = debug
	if debug:
		print("Debugging enabled!")

	for i in range(int(input("How many clients? "))): TClient()
	server = TServer()
	server.startBroadcasting()

if __name__ == "__main__": main()
