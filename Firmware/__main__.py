#!usr/bin/python3

from __future__ import annotations
from src.parsing import ArgumentParser
from src.networking import TServer, TClient
import sys

def main():
	print("Creating Instance Of Server")
	serv = TServer()
	print("Creating Instance Of Client")
	cli = TClient()
	print("Start Client Waiting For Server IP")
	cli.waitForServer()
	input("Press enter to start server broadcasting")
	print("Starting Server IP Broadcasting")
	serv.startBroadcasting()
	'''
	Non Theorectical Solution

	parser = ArgumentParser(False, { "vars": { "required": { "server": "boolean" } } })
	parser.parse(sys.argv[1:])
	response = parser.execute()
	print("Response:", response)
	if response == 1:
		if parser.readVariable("server"):
			ser = Server(1)
			ser.beginBroadcast()
		else:
			cli = Client()
	'''


if __name__ == "__main__": main()
