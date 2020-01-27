# All exit codes

import sys
from enum import Enum

class ExitingCodes(Enum): pass

class SystemReserved(ExitingCodes): # 2 ^ 1
	SUCESS = 0 # Sucess
	EXIT = 1   # Error was thrown, force closed, no other code was exited

class General(ExitingCodes): # 2 ^ 2
	SUCCESS = 3 # Success
	ERROR = 4   # Failed, Terminated or Error

class Reserved(ExitingCodes): # 2 ^ 3
	WASNT_CODE = 5   # An object that isn't a code was passed
	INVALID_CODE = 5 # An invalid exit code was used in exiting

class Installation(ExitingCodes): # 2 ^ 4
	SUCCESS = 9           # Install was successful
	SAME_ID_AND_TYPE = 10 # Device was already set up under the same id and as the same system type
	SAME_ID = 11          # Device was already set up under the same id
	INVALID_ID = 12       # An invalid device id was specified
	INVALID_SERVER = 13   # An invalid server setting was set

class Parsing(ExitingCodes): # 2 ^ 5
	SUCESS = 17                        # Args were set (without error)
	SUCESS_AFTER_COMMAND = 18          # Command was executed (without error)
	SUCESS_AFTER_ARGS_AND_COMMAND = 19 # Args were set and a command was executed (without error)
	INVALID_TYPE = 20                  # Invalid argument type to a variable
	NO_EXECUTION = 21                  # Nothing was executed by parser
	MISSING_REQUIRED = 22              # Not all required arguments were set
	ERROR_THROWN = 23                  # An error was raised while executing a command
	NO_COMMAND = 24                    # A non-existing command was called
	NO_VARIABLE = 25                   # A value was set to a variable that doesn't exist

class Networking(ExitingCodes): # 2 ^ 6
	pass

def Exit(code: ExitingCodes = None):
	try:
		if code is None or type(code).__bases__[0] != ExitingCodes:
			sys.exit(Reserved.WASNT_CODE)
		code = code.value
		if code is None or type(code) != int or code < 0 or code > 128:
			sys.exit(Reserved.INVALID_CODE)
		print("Terminating with code", code)
		sys.exit(code)
	except IndexError:
		sys.exit(Reserved.WASNT_CODE)