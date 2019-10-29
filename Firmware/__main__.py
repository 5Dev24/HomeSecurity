#!usr/bin/python3

from __future__ import annotations
from src.parsing import ArgumentParser
from src.networking import TServer, TClient
from src.crypt import RSA, CONSTS
import time
import sys

def main():
	rsaTests(10)
	'''
	serv = TServer()
	cli = TClient()
	cli.waitForServer()
	serv.startBroadcasting()
	'''

def rsaTests(tests: int = 1):
	test = 1
	totalTime = 0
	print("RSA Settings")
	print("Client key:", CONSTS["CLIENT_RSA"])
	print("Server key:", CONSTS["SERVER_RSA"])
	print("Prime:", CONSTS["RSA_PRIME"])
	print("Starting RSA Tests")
	while test <= tests:
		start = time.time()
		RSA(False)
		took = time.time() - start
		totalTime += took
		print("Test #", test, ": {:5.2f} seconds".format(took), sep="")
		test += 1
	print("Done With RSA Tests")
	print("Average Time: {:5.2f}".format(totalTime / tests))

if __name__ == "__main__": main()
