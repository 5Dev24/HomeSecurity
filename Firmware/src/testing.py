from .crypt import RSA, CONSTS
from .networking import TThread
import time, sys, math

GLOBAL_TOTAL_TIME_TAKEN_RSA = -1
GLOBAL_TOTAL_TESTS_DONE = -1

def rsaTests(tests: int = 1, threads: int = 0):
	global GLOBAL_TOTAL_TIME_TAKEN_RSA, GLOBAL_TOTAL_TESTS_DONE
	if GLOBAL_TOTAL_TIME_TAKEN_RSA != -1 or GLOBAL_TOTAL_TESTS_DONE != -1: return

	print("Settings")
	print("Client key:", CONSTS["CLIENT_RSA"])
	print("Server key:", CONSTS["SERVER_RSA"])
	print("Prime:", CONSTS["RSA_PRIME"])
	print("Threads:", threads)
	print("Total Tests:", tests)
	print("Starting RSA Tests")

	GLOBAL_TOTAL_TIME_TAKEN_RSA = 0
	GLOBAL_TOTAL_TESTS_DONE = 0
	threadsInstances = []

	if threads < 1: threads = 1

	for i in range(threads):
		T = TThread(rsaTestingThread, False, (), {"threadid": i, "testsToRun": math.floor(tests / threads) + (tests - tests % threads) if i == threads -1 else 0})
		T.start()
		threadsInstances.append(T)

	while GLOBAL_TOTAL_TESTS_DONE < tests: continue

	TempText.clear()

	print("Done With RSA Tests")
	print("Average Time: {:4.2f}".format(GLOBAL_TOTAL_TIME_TAKEN_RSA / tests))

def rsaTestingThread(threadid: int = 0, testsToRun: int = 0):
	global GLOBAL_TOTAL_TIME_TAKEN_RSA, GLOBAL_TOTAL_TESTS_DONE
	for test in range(testsToRun):
		start = time.time()
		RSA(False)
		took = time.time() - start
		GLOBAL_TOTAL_TIME_TAKEN_RSA += took
		GLOBAL_TOTAL_TESTS_DONE += 1
		TempText.print("Thread ID: #{:03d} Test #{:03d}: {:08.4f} seconds".format(threadid + 1, test + 1, took))

class TempText:

	PreviousLineLength = 0

	@staticmethod
	def print(line: str = ""):
		TempText.PreviousLineLength = len(line)
		print(line, end = "\r")

	@staticmethod
	def clear(): TempText.print(" " * TempText.PreviousLineLength)
