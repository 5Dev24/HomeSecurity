from .crypt import RSA, CONSTS
from .networking import TThread
import time, sys

GLOBAL_CURRENT_RSA_TEST = -1
GLOBAL_TOTAL_RSA_TESTS = -1
GLOBAL_TOTAL_TIME_TAKEN_RSA = -1

def rsaTests(tests: int = 1, threads: int = 0):
	global GLOBAL_CURRENT_RSA_TEST, GLOBAL_TOTAL_RSA_TESTS, GLOBAL_TOTAL_TIME_TAKEN_RSA

	if GLOBAL_CURRENT_RSA_TEST != -1 or GLOBAL_TOTAL_RSA_TESTS != -1 or GLOBAL_TOTAL_TIME_TAKEN_RSA != -1: return

	print("Settings")
	print("Client key:", CONSTS["CLIENT_RSA"])
	print("Server key:", CONSTS["SERVER_RSA"])
	print("Prime:", CONSTS["RSA_PRIME"])
	print("Threads:", threads)
	print("Total Tests:", tests)
	print("Starting RSA Tests")

	GLOBAL_TOTAL_TIME_TAKEN_RSA = 0
	GLOBAL_CURRENT_RSA_TEST = 1
	GLOBAL_TOTAL_RSA_TESTS = tests
	threadsInstances = []

	if threads < 1: threads = 1

	for i in range(threads):
		T = TThread(rsaTestingThread, False, (), {"threadid": i})
		T.start()
		threadsInstances.append(T)

	while GLOBAL_CURRENT_RSA_TEST < GLOBAL_TOTAL_RSA_TESTS + 2: continue

	TempText.clear()

	print("Done With RSA Tests")
	print("Average Time: {:4.2f}".format(GLOBAL_TOTAL_TIME_TAKEN_RSA / tests))

def rsaTestingThread(threadid: int = 0):
	global GLOBAL_CURRENT_RSA_TEST, GLOBAL_TOTAL_RSA_TESTS, GLOBAL_TOTAL_TIME_TAKEN_RSA
	while GLOBAL_CURRENT_RSA_TEST <= GLOBAL_TOTAL_RSA_TESTS:
		start = time.time()
		RSA(False)
		took = time.time() - start
		if GLOBAL_CURRENT_RSA_TEST <= GLOBAL_TOTAL_RSA_TESTS:
			GLOBAL_TOTAL_TIME_TAKEN_RSA += took
			TempText.print("Thread ID: #{:d} Test #{:d}: {:5.2f} seconds".format(threadid, GLOBAL_CURRENT_RSA_TEST, took))
			GLOBAL_CURRENT_RSA_TEST += 1
		else: break

class TempText:

	@staticmethod
	def print(line: str = ""): print(line, end = "\r")

	@staticmethod
	def clear(): TempText.print(" " * 64)
