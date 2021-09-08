import sys, inspect
from enum import Enum
from typing import Optional, Tuple, Union, Dict
import traceback

class FailureCode(): pass

class SystemCode(FailureCode, Enum): # [0, 1]
	Success = (0, "Program will terminate successfully")
	Exit    = (1, "Program is terminating and a problem arose")

class General(FailureCode, Enum): # [2, 3]
	Success = (2, "HomeSec completed its operations successfully")
	Error   = (3, "HomeSec failed in some way")

class Failure(FailureCode, Enum): # [4, 7]
	Invalid_Code  = (4, "A failure code was invalid, didn't exist or wasn't an integer")
	Invalid_Trace = (5, "An invalid trace was given for a failure")

class Installation(FailureCode, Enum): # [8, 15]
	Success               = (8, "Installation was successful")
	Missing_Perms_File    = (9, "Not enough permissions to edit or delete a file")
	Missing_Perms_Modify  = (10, "Not enough permissions to modify a service")
	Missing_Perms_Package = (11, "Not enough permissions to install or update packages")
	Missing_Perms_Service = (12, "Not enough permissions to create or restart a service")
	Failure               = (13, "Installation failed in an unexpected way")
	No_History            = (14, "When trying to read data from config made by installating, data was missing")
	Previous_Install      = (15, "There was a pre-existing install and --force wasn't specified, use force to override prior installation")

class Networking(FailureCode, Enum): # [16, 31]
	Connection_Dropped = (16, "Connection was closed unexpectedly")
	Missing_Perms      = (17, "Insufficient permission to open a socket")
	Bytes_Decode       = (18, "Failed to decode bytes from a socket")

class Protocol(FailureCode, Enum): # [32, 63]
	Step             = (32, "A protocol step was done out of order or requested next step isn't possible")
	Response         = (33, "Received response didn't follow protocol")
	Invalid_Step     = (34, "Step is out of bounds and doesn't exist")
	Security_Violate = (35, "Device is misbehaving and is trying to access data it has no reason to request")

class Threading(FailureCode, Enum): # [64, 127]
	Halt_Joined      = (64, "A thread tried to halt itself as main")
	Main_Died        = (65, "The main thread died")
	Killed           = (66, "A thread was forcefully killed")
	Exception_Raised = (67, "A thread raised an exception while executing")

def generate_ranges_and_map() -> Tuple[Tuple[Tuple[int, int]], Dict[int, str]]:
	ranges = []
	map = {}

	classes = inspect.getmembers(sys.modules[__name__], inspect.isclass)

	for a_class in classes:
		if type(a_class) == tuple and FailureCode in a_class[1].__bases__:
			values = a_class[1].__members__.values()
			min_value = None
			max_value = None
			for value in values:
				num_value = value.value[0]
				if min_value is None or num_value < min_value:
					min_value = num_value
				if max_value is None or num_value > max_value:
					max_value = num_value
				
				map[num_value] = value.value[1]
			
			ranges.append((min_value, max_value))

	return tuple(ranges), map

ranges, map = generate_ranges_and_map()

def code_within_ranges(code: int) -> bool:
	for range in ranges:
		if code >= range[0] and code <= range[1]:
			return True

	return False

def __finalize(code: FailureCode, info: str, log: Optional[bool], trace: Optional[Union[str, BaseException]], trace2: Optional[Union[str, BaseException]], codetype: str):
	name = code.name.replace("_", " ")
	if trace:
		if isinstance(trace, BaseException):
			trace = "\n".join(traceback.format_exception(type(trace), trace, None))

		if not isinstance(trace, str):
			sys.exit(Failure.Invalid_Trace.value[0])

		if isinstance(trace2, BaseException):
			trace += "\n".join(traceback.format_exception(type(trace2), trace2, None))
		elif isinstance(trace2, str):
			trace += f"\n{trace2}"

		if info:
			logger.Log(codetype, f"{name}\n{info}\n{trace}", print = log)
		else:
			logger.Log(codetype, f"{name}\n{trace}", print = log)
	else:
		if info:
			logger.Log(codetype, f"{name}\n{info}", print = log)
		else:
			logger.Log(codetype, f"{name}", print = log)

def die(code: FailureCode, info: str, log: Optional[bool] = True, trace: Optional[Union[str, BaseException]] = None, trace2: Optional[Union[str, BaseException]] = None) -> None:
	if not isinstance(code, FailureCode) or not code_within_ranges(code.value[0]):
		sys.exit(Failure.Invalid_Code.value[0])

	if code.value[0] in (0, 2):
		__finalize(code, info, log, trace, trace2, "safe")
	else:
		__finalize(code, info, log, trace, trace2, "error")

	sessions.SessionManager.get_manager().shutdown()
	logger.Logger.get_logger().finalize()
	thread.EasyThread.kill_threads()
	sys.exit(code.value[0])

def notice(code: FailureCode, info: str, log: Optional[bool] = True, trace: Optional[Union[str, BaseException]] = None, trace2: Optional[Union[str, BaseException]] = None) -> None:
	if not isinstance(code, FailureCode) or not code_within_ranges(code.value[0]):
		notice(Failure.Invalid_Code)
		return

	__finalize(code, info, log, trace, trace2, "warn")

import logger, thread
from networking import sessions