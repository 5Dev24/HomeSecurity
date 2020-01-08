from enum import Enum
from datetime import datetime

def Now(): return datetime.now()
def Time(): return Now().strftime("%H:%H:%S")
def Date(): return Now().strftime("%d/%m/%Y")

class LogType(Enum):

	Info = 0
	Warn = 1

	def __str__(self):
		return f"{self.name}"

class Log:

	@staticmethod
	def fromString(string: str = ""):
		if string is None or type(string) != str or len(string) < 26: return None
		else:
			try:
				t = LogType(string[1:5])
				l = Log(t, string[26:])
				l.date = string[7:15]
				l.time = string[16:24]
				return Log(t, string[26:])
			except ValueError: return None

	def __init__(self, logType: LogType = LogType.Info, info: str = ""):
		if logType is None or type(logType) != LogType: logType = LogType.Info
		if info is None or type(info) != str: info = "No Log Information Passed To Log"
		self.logType = logType
		self.info = info
		self.date = Date()
		self.time = Time()

	def post(self): print(self)

	def __str__(self):
		return f"[{self.logType}] {self.date} {self.time}: {self.info}"
