#!usr/bin/python3

from src.networking import TServer, TClient

def main():
	server = TServer()
	clientA = TClient()
	clientB = TClient()
	clientA.waitForServer()
	clientB.waitForServer()
	server.startBroadcasting()

if __name__ == "__main__": main()
