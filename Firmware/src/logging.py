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
				return Log(string[7:15], string[16:24], t, string[26:])
			except ValueError: return None

	def __init__(self, date: str = "", time: str = "", logType: LogType = LogType.Info, info: str = ""):
		if date is None or type(date) != str or not len(date): date = Date()
		if time is None or type(time) != str or not len(time): time = Time()
		if logType is None or type(logType) != LogType: logType = LogType.Info
		if info is None or type(info) != str: info = "No Log Information Passed To Log"
		self.date = date
		self.time = time
		self.logType = logType
		self.info = info

	def __str__(self):
		return f"[{self.logType}] {self.date} {self.time}: {self.info}"
