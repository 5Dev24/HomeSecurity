# All exit codes

import sys
from enum import Enum, EnumMeta

class Code(Enum): pass

class SystemReserved(Code): # 2 ^ 1
	SUCESS = 0 # Sucess
	EXIT = 1   # Error was thrown, force closed, no other code was exited

class General(Code): # 2 ^ 2
	SUCCESS = 3 # Success
	ERROR = 4   # Failed, Terminated or Error

class Reserved(Code): # 2 ^ 3
	WASNT_CODE = 5   # An object that isn't a code was passed
	INVALID_CODE = 6 # An invalid exit code was used in exiting

class Installation(Code): # 2 ^ 4
	SUCCESS = 9           # Install was successful
	SAME_ID_AND_TYPE = 10 # Device was already set up under the same id and as the same system type
	SAME_ID = 11          # Device was already set up under the same id
	INVALID_ID = 12       # An invalid device id was specified
	INVALID_SERVER = 13   # An invalid server setting was set
	HASNT_BEEN = 14       # This device hasn't been installed yet

class Parsing(Code): # 2 ^ 5
	SUCESS = 17                        # Args were set (without error)
	SUCESS_AFTER_COMMAND = 18          # Command was executed (without error)
	SUCESS_AFTER_ARGS_AND_COMMAND = 19 # Args were set and a command was executed (without error)
	INVALID_TYPE = 20                  # Invalid argument type to a variable
	NO_EXECUTION = 21                  # Nothing was executed by parser
	MISSING_REQUIRED = 22              # Not all required arguments were set
	ERROR_THROWN = 23                  # An error was raised while executing a command
	NO_COMMAND = 24                    # A non-existing command was called
	NO_VARIABLE = 25                   # A value was set to a variable that doesn't exist

class Networking(Code): # 2 ^ 6
	UNABLE_TO_REACH = 33         # An address was unreachable
	FAILED_TO_CREATE_SOCKET = 34 # A socket was unable to be opened

class Threading(Code): # 2 ^ 7
	LOOPING_THREAD_ERROR = 65 # An error was thrown in a looping thread
	SINGLE_THREAD_ERROR = 66  # An error was thrown in a single-call thread
	JOIN_FROM_MAIN = 67       # An attempt was made to join a thread from the main thread

def Exit(code: Code = None, info: str = None):
	if code is None or not len(type(code).__bases__) or type(code).__bases__[0] != Code:
		sys.exit(Reserved.WASNT_CODE)
	code = code.value
	if code is None or type(code) != int or code < 0 or code > 128:
		sys.exit(Reserved.INVALID_CODE)
	if info is not None and type(info) == str and len(info):
		print("Terminating with code", code, "with message", info)
	else:
		print("Terminating with code", code)
	sys.exit(code)

def LogCode(code: Code = None, info: str = None):
	Code.__getattribute__
	if code is None or not len(type(code).__bases__) or type(code).__bases__[0] != Code:
		return
	code = code.value
	if code is None or type(code) != int or code < 0 or code > 128:
		return
	from src.logging import Log, LogType
	if info is not None and type(info) == str and len(info):
		Log(LogType.Info, f"Code {code}: {info}")
	else:
		Log(LogType.Info, f"Code {code} was noted")

def _build_trace(code: Code = None):
	bases = [code.__class__.__name__]
	tmp = code.__class__
	print(code.__class__.__bases__)
	depth = 5
	while tmp != EnumMeta and depth > 0:
		print("Tmp", tmp)
		print("Found", tmp.__class__.__name__, "Going to", code.__class__.__bases__)
		bases.append(tmp.__class__.__name__)
		tmp = code.__class__.__bases__[0]
		depth -= 1
	codes = code.__class__.__dict__
	print("Codes", codes)
	bases.append(codes._value2member_map_[code.value].__name__)

	print(".".join(bases), sep="")