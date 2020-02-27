# All exit codes

import sys
from . import logging as _logging, threading as _threading

class Code(): pass # Parent to get all subclasses from

class SystemReserved(Code): # 2 ^ 1
	SUCESS = 0 # Sucess
	EXIT   = 1 # Error was thrown, force closed, no other code was exited

class General(Code): # 2 ^ 2
	SUCCESS = 3 # Success
	ERROR   = 4 # Failed, Terminated or Error

class Reserved(Code): # 2 ^ 3
	WASNT_CODE      = 5 # An object that isn't a code was passed
	INVALID_CODE    = 6 # An invalid exit code was used in exiting
	FORCE_TERMINATE = 7 # Something caused the main thread to stop waiting on all other threads to exit

class Installation(Code): # 2 ^ 4
	SUCCESS           = 9  # Install was successful
	SAME_MAC_AND_TYPE = 10 # Device was already set up under the same id and as the same system type
	SAME_MAC          = 11 # Device was already set up under the same id
	INVALID_MAC       = 12 # An invalid device id was specified
	HASNT_BEEN        = 13 # This device hasn't been installed yet

class Arguments(Code): # 2 ^ 5
	LEX_SUCCESS            = 17 # Lexing Success
	PARSER_SUCCESS         = 18 # Parsing Success
	EXECUTE_SUCCESS        = 19 # Executing Success
	COMMAND_DOESNT_EXIST   = 20 # Unable to find a command
	NO_DEFAULT             = 21 # No default command exists
	ONLY_DEFAULT_INVOKED   = 22 # Only the default command was called
	VALUE_WITH_NO_VARIABLE = 23 # A value was found that didn't have a variable for it to be set to
	ERROR_IN_COMMAND       = 24 # An error was thrown during the execution of the command
	LEFT_OPEN_STRING       = 25 # A string was started but never ended
	NO_GOOD_LEX            = 26 # The current tokens are not good to use, the lexer failed in some way
	NO_GOOD_PARSE          = 27 # The current arguments/command to invoek are not good to use, parser failed in some way
	BAD_ARGUMENTS          = 28 # The arguments made by the parser don't fit the command

class Networking(Code): # 2 ^ 6
	UNABLE_TO_REACH         = 33 # An address was unreachable
	FAILED_TO_CREATE_SOCKET = 34 # A socket was unable to be opened
	PACKET_DECODE_FAIL      = 35 # A packet wasn't able to be decoded into the regular format

class Threading(Code): # 2 ^ 7
	LOOPING_THREAD_ERROR = 65 # An error was thrown in a looping thread
	SINGLE_THREAD_ERROR  = 66 # An error was thrown in a single-call thread
	JOIN_FROM_MAIN       = 67 # An attempt was made to join a thread from the main thread
	FORCE_CLOSE          = 68 # SimpleClose was thrown so function should just return this because of the error was caught by mistake
	MAIN_DEAD            = 69 # The main thread was killed or ended thus all other non-daemon threads need to be killed

def Exit(code: int = None, info: str = None, log: bool = False):
	if code is None or type(code) != int or code < 0 or code > 128:
		sys.exit(Reserved.INVALID_CODE)

	if log:
		trace = _build_trace(code)
		msg = " with no message"
		if info is not None and type(info) == str and len(info):
			msg = " with message: " + info
		msg = "Terminating on " + trace + msg
		_logging.Log(_logging.LogType.Exit, msg).post()

	_threading.SimpleThread.ReleaseThreads()
	sys.exit(code)

def LogCode(code: int = None, info: str = None):
	if code is None or type(code) != int or code < 0 or code > 128:
		return
	trace = _build_trace(code)
	if info is None or type(info) != str or not len(info):
		info = "No message"
	_logging.Log(_logging.LogType.Info,  f"{trace}: {info}").post()

def _collect_subclasses(parent = None):
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
		return (_parent_trace(varClass) + "." + varName + "-" + str(varValue)).lower()
	return "invalid"
