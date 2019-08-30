from __future__ import annotations
from parsing import ArgumentParser
import sys

def main():
	args = sys.argv[1:]
	argParser = ArgumentParser({
		"cmds": {
			"help": lambda: print("help message test")
		},
		"func": {
			"test": lambda x: print("argument passed: \"", x, '"', sep = '')
		}
	})
	argParser.parse(args)
	argParser.execute()

if __name__ == "__main__": main()