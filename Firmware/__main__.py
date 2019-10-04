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
	print("Server Callback: ", serv._broadcastSocket._callbackID, ",\nClient Callback: ", cli._broadcastSocket._callbackID, sep = "")
	input("Press enter to start server broadcasting")
	print("Starting Server IP Broadcasting")
	serv.startBroadcasting()

if __name__ == "__main__": main()
