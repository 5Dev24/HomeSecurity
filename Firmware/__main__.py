#!usr/bin/python3

from __future__ import annotations
from src.parsing import ArgumentParser
from src.networking import TServer, TClient
import sys

def main():
	serv = TServer()
	cli = TClient()
	cli.waitForServer()
	serv.startBroadcasting()

if __name__ == "__main__": main()
