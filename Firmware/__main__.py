#!usr/bin/python3

from __future__ import annotations
from src.parsing import ArgumentParser
from src.networking import TServer, TClient
from src.crypt import RSA, CONSTS
from src.testing import rsaTests
import time
import sys

def main():
	rsaTests(300, 30)

	'''
	serv = TServer()
	cli = TClient()
	cli.waitForServer()
	serv.startBroadcasting()
	'''

if __name__ == "__main__": main()
