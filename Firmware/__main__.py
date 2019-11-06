#!usr/bin/python3

from src.networking import TServer, TClient

def main():
	server = TServer()
	client = TClient()
	client.waitForServer()
	server.startBroadcasting()

if __name__ == "__main__": main()
