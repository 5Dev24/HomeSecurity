from enum import Enum
from datetime import datetime
from .file import LogFormat, FileSystem, File

def Now(): return datetime.now()
def Time(): return Now().strftime("%H:%H:%S")
def Date(): return Now().strftime("%d/%m/%Y")

class LogType(Enum):

	Info = 0
	Warn = 1

	@staticmethod
	def fromString(string: str = ""):
		string = string.lower()
		if string == "info": return LogType.Info
		elif string == "warn": return LogType.Warn
		else: return None

	def __str__(self):
		return f"{self.name}"

class Log:

	@staticmethod
	def allLogs():
		pass

	def LogFile():
		return File.getOrCreate(FileSystem, "logs")

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
			logs = Logs()
			logs.data.append(self)
			logs.write(LogFile())

	def post(self): print(self)

	def __str__(self):
		return f"[{self.logType}] {self.date} {self.time}: {self.info}"
