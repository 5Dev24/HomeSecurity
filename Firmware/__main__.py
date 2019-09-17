#!usr/bin/python3

from __future__ import annotations
from src.parsing import ArgumentParser
from src.networking import Server, Client
import sys

def main():
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


if __name__ == "__main__": main()
