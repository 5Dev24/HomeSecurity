from enum import Enum
from datetime import datetime
from .file import LogFormat, FileSystem, File
from colorama import init, Fore, Back, Style

def Now(): return datetime.now()
def Time(): return Now().strftime("%H:%H:%S")
def Date(): return Now().strftime("%d/%m/%Y")

class LogType(Enum):

	# Error Text Foreground, Message Text Foreground, Background of all Text
	Info = (Fore.GREEN, Fore.WHITE, Back.BLACK)
	Data = (Fore.CYAN, Fore.LIGHTBLACK_EX, Back.BLACK)
	Warn = (Fore.LIGHTRED_EX, Fore.YELLOW, Back.BLACK)

	@staticmethod
	def fromString(string: str = ""):
		string = string.lower()
		if string == "info": return LogType.Info
		elif string == "data": return LogType.Data
		elif string == "warn": return LogType.Warn
		else: return None

	def __str__(self):
		return f"{self.name}"

class Log:

	@staticmethod
	def AllLogs():
		return Log.Logs().data

	@staticmethod
	def LogFile():
		return File.getOrCreate(FileSystem, "logs")

	@staticmethod
	def Logs():
		logs = LogFormat.loadFrom(Log.LogFile())
		if logs is None or type(logs) != LogFormat: logs = LogFormat()
		return logs

	@staticmethod
	def fromString(string: str = ""):
		if string is None or type(string) != str or len(string) < 26: return None
		else:
			try:
				t = LogType.fromString(string[1:5])
				l = Log(t, string[28:], False)
				l.date = string[7:17]
				l.time = string[18:26]
				return l
			except ValueError: return None

	def __init__(self, logType: LogType = LogType.Info, info: str = "", save: bool = True):
		if logType is None or type(logType) != LogType: logType = LogType.Info
		if info is None or type(info) != str: info = "No Log Information Passed To Log"
		self.logType = logType
		self.info = info
		self.date = Date()
		self.time = Time()
		if save:
			logs = Log.Logs()
			logs.data.append(self)
			logs.write(Log.LogFile())

	def post(self):
		print(self.colored())
		return self

	def colored(self):
		colors = self.logType.value[:]
		return f"{colors[2]}{Fore.WHITE}{Style.BRIGHT}[{colors[0]}{self.logType.name}{Fore.WHITE}] \
{self.date} {self.time}{Fore.CYAN}: {colors[1]}{self.info}{Style.RESET_ALL}"

	def __str__(self):
		return f"[{self.logType.name}] {self.date} {self.time}: {self.info}"

if __name__ != "__main__":
	init()