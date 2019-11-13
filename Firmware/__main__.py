#!usr/bin/python3

from src.networking import TServer, TClient

def main():
	spawnXClients(int(input()))
	server = TServer()
	server.startBroadcasting()

def spawnXClients(x: int = 0):
	for i in range(x):
		client = TClient()
		client.waitForServer()

if __name__ == "__main__": main()
