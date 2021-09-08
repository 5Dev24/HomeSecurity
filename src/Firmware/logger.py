import sys
from queue import Queue
from datetime import datetime
from typing import List, NamedTuple
from colorama import Fore, Back, Style, init

import io_handles

class LogTypes:

	# For introspection/autocomplete/linters
	Info    = "info"
	Install = "install"
	Warn    = "warn"
	Error   = "error"
	Debug   = "debug"
	Exit    = "exit"
	Safe    = "safe"

	logtypes = {
#		name:      type,          message,     backgorund
		"info":    (Fore.GREEN,   Fore.WHITE,  Back.RESET),
		"install": (Fore.CYAN,    Fore.WHITE,  Back.RESET),
		"warn":    (Fore.RED,     Fore.YELLOW, Back.RESET),
		"error":   (Fore.RED,     Fore.RED,    Back.RESET),
		"debug":   (Fore.MAGENTA, Fore.WHITE,  Back.RESET),
		"exit":    (Fore.YELLOW,  Fore.YELLOW, Back.RESET),
		"safe":    (Fore.GREEN,   Fore.GREEN,  Back.RESET)
	}

	types = tuple(logtypes.keys())

	@staticmethod
	def is_valid_type(logtype: str):
		return isinstance(logtype, str) and logtype.lower() in LogTypes.logtypes

	@staticmethod
	def get_colors(logtype: str):
		if LogTypes.is_valid_type(logtype):
			return LogTypes.logtypes[logtype.lower()]

class TimestampData:

	def __init__(self, date: str, time: str):
		self.date = date
		self.time = time

class Timestamp:

	def __new__(cls, date = None, time = None):
		if date is None or time is None:
			now = datetime.now()

		if date is None:
			date = now.strftime("%d/%m/%Y")
		if time is None:
			time = now.strftime("%H:%M:%S")

		return TimestampData(date, time)

class LogData(NamedTuple):
	logtype: str
	unsafe_message: str
	message: str
	timestamp: TimestampData

	def __str__(self):
		try:
			colors = LogTypes.logtypes[self.logtype.lower()]
			return f"{colors[2]}{Fore.WHITE}{Style.BRIGHT}{self.timestamp.date} :: {self.timestamp.time} [{colors[0]}{self.logtype.title()}{Fore.WHITE}] {Style.RESET_ALL}{colors[2]}{colors[1]}{self.unsafe_message}{Style.RESET_ALL}"
		except KeyError:
			return f"{self.timestamp.date} :: {self.timestamp.time} [{self.logtype.title()}] {self.unsafe_message}"

	def __repr__(self):
		return f"{self.timestamp.date} :: {self.timestamp.time} [{self.logtype.title()}] {self.message}"

class Log:

	def __new__(cls, logtype: str, message: str, save: bool = True, print: bool = False) -> LogData:
		if not LogTypes.is_valid_type(logtype):
			logtype = LogTypes.Info
		
		if message is None or not isinstance(message, str):
			message = "No message provided"

		if logtype.lower() == "debug":
			save = False

		message = message.rstrip()

		logdata = LogData(logtype, message, repr(message)[1:-1], Timestamp())

		if save:
			Logger.get_logger().save(logdata)

		if print:
			Logger.get_logger().print(logdata)

		return logdata

class Logger:

	__instance = None

	@classmethod
	def get_logger(cls) -> "Logger":
		if cls.__instance is None:
			init(True)
			cls.__instance = cls.__new__(cls)
			self = cls.__instance

			self.__dead = False

			self.log_file = io_handles.EasyFile(io_handles.FileUtil.root() + "/logs/log.homesec", True)
			self.log_data = io_handles.LogFileFormat().from_file(self.log_file)

			self.__save_queue  = Queue()
			self.__print_queue = Queue()
			self.__save_thread = thread.EasyThread(self.__save, True)
			self.__print_thread = thread.EasyThread(self.__print, True)
			self.__save_thread.start()
			self.__print_thread.start()

		if cls.__instance.__dead:
			dead = type("Dead Logger", (object,), {})
			dead.log_file = dead.log_data = dead.__save_queue = dead.__print_queue = dead.__save_thread = dead.__print_thread = dead.__dead = None
			dead.save = dead.print = dead.finalize = dead.get = dead.__save = dead.__print = lambda *args, **kwargs: None
			return dead

		return cls.__instance

	def __init__(self):
		# For typing
		self.log_file: io_handles.EasyFile
		self.log_data: io_handles.LogFileData

		self.__dead: bool
		self.__save_queue: Queue[LogData]
		self.__print_queue: Queue[LogData]
		self.__save_thread: thread.EasyThread
		self.__print_thread: thread.EasyThread

		raise RuntimeError("Get logger from Logger.get_logger()")

	def save(self, log: LogData) -> None:
		if not self.__dead:
			if isinstance(log, LogData):
				self.__save_queue.put_nowait(log)

	def print(self, log: LogData) -> None:
		if not self.__dead:
			if isinstance(log, LogData):
				self.__print_queue.put_nowait(log)

	def finalize(self) -> None:
		if self.__dead: return
		self.__dead = True

		if self.__save_thread is not None:
			if not self.__save_queue.empty():
				self.__save(True)

			self.__save_thread.kill()
			self.__save_queue = None

		if self.__print_thread is not None:
			if not self.__print_queue.empty():
				self.__print(True)

			self.__print_thread.kill()
			self.__print_queue = None

	def get(self, count: int) -> List[LogData]:
		if isinstance(count, int):
			return self.log_data.get_tail(count)

	def __save(self, final: bool = False) -> None:
		if final:
			while not self.__save_queue.empty():
				self.log_data.add_log(self.__save_queue.get())

			io_handles.LogFileFormat().save_to(self.log_file, self.log_data)
			return

		self.log_data.add_log(self.__save_queue.get())
		io_handles.LogFileFormat().save_to(self.log_file, self.log_data)
		"""
		if not self.__save_queue.empty():
			while not self.__save_queue.empty():
				self.log_data.add_log(self.__save_queue.get())

			io_handles.LogFileFormat().save_to(self.log_file, self.log_data)
		"""

	def __print(self, final: bool = False) -> None:
		if final:
			while not self.__print_queue.empty():
				message = self.__print_queue.get()
				if sys.stdout.writable and not sys.stdout.closed:
					sys.stdout.write(f"{message}\n")

			sys.stdout.flush()
			return

		message = self.__print_queue.get()
		if sys.stdout.writable and not sys.stdout.closed:
			sys.stdout.write(f"{message}\n")
			sys.stdout.flush()

		"""
		if not self.__print_queue.empty():
			flush = False
			while not self.__print_queue.empty():
				message = self.__print_queue.get()
				if sys.stdout.writable and not sys.stdout.closed:
					flush = True
					sys.stdout.write(f"{message}\n")

			if flush:
				sys.stdout.flush()
		"""

import thread, io_handles