# All exit codes

import sys

class Code(): pass

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
	SUCCESS = 17                        # Args were set (without error)
	SUCCESS_AFTER_COMMAND = 18          # Command was executed (without error)
	SUCCESS_AFTER_ARGS_AND_COMMAND = 19 # Args were set and a command was executed (without error)
	INVALID_TYPE = 20                   # Invalid argument type to a variable
	NO_EXECUTION = 21                   # Nothing was executed by parser
	MISSING_REQUIRED = 22               # Not all required arguments were set
	ERROR_THROWN = 23                   # An error was raised while executing a command
	NO_COMMAND = 24                     # A non-existing command was called
	NO_VARIABLE = 25                    # A value was set to a variable that doesn't exist

class Networking(Code): # 2 ^ 6
	UNABLE_TO_REACH = 33         # An address was unreachable
	FAILED_TO_CREATE_SOCKET = 34 # A socket was unable to be opened
	PATCH_DECODE_FAIL = 35       # A packet wasn't able to be decoded into the regular format

class Threading(Code): # 2 ^ 7
	LOOPING_THREAD_ERROR = 65 # An error was thrown in a looping thread
	SINGLE_THREAD_ERROR = 66  # An error was thrown in a single-call thread
	JOIN_FROM_MAIN = 67       # An attempt was made to join a thread from the main thread

def Exit(code: int = None, info: str = None, log: bool = False):
	if code is None or type(code) != int or code < 0 or code > 128:
		sys.exit(Reserved.INVALID_CODE)

	trace = _build_trace(code)
	if info is not None and type(info) == str and len(info):
		print("Terminating on", trace, "with message", info)
	elif log:
		print("Terminating on", trace, "with no message")
	sys.exit(code)

def LogCode(code: int = None, info: str = None):
	if code is None or type(code) != int or code < 0 or code > 128:
		return
	from src.logging import Log, LogType
	trace = _build_trace(code)
	if info is None or type(info) != str or not len(info):
		info = "No message"
	Log(LogType.Info,  f"{trace}: {info}").save().post()

def _collect_subclasses(parent = None):
	classes = []
	for subclass in parent.__subclasses__():
		yield subclass
		for subsubclass in _collect_subclasses(subclass):
			yield subsubclass

def _build_trace(code: int = -1):
	def _find_code(searchCode: int = -1):
		for subclass in _collect_subclasses(Code):
			for key, value in subclass.__dict__.items():
				if not key.startswith("__") and type(value) == int and value == searchCode:
					return (key, value, subclass)
		return (None,)*3

	def _parent_trace(base = None):
		return ".".join([parent.__name__ for parent in base.__mro__ if parent != Code and parent != object][::-1])

	varName, varValue, varClass = _find_code(code)
	if varName is not None:
		return (_parent_trace(varClass) + "." + varName).lower()
	return "invalid"
