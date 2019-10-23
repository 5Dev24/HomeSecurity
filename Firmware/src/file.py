from os import remove, access as hasPerm
from os import R_OK, W_OK, X_OK, F_OK
from os.path import abspath

class File:

	def __init__(self, file: str = None):
		self._file = abspath(file)

	def __str__(self):
		return f"Name: {self.name()}, Absolute Path: {self._file}, Exists: {self.exists()}, Perms: {self.perms()}"

	def name(self):
		return self._file.split("\\")[::-1][0]

	def perms(self):
		permAsBin = lambda bol: "1" if bol else "0"
		return int(permAsBin(self.canExecute()) + permAsBin(self.canRead()) + permAsBin(self.canWrite()), 2)

	def exists(self): return hasPerm(self._file, F_OK)
	def canWrite(self): return hasPerm(self._file, W_OK)
	def canRead(self): return hasPerm(self._file, R_OK)
	def canExecute(self): return hasPerm(self._file, X_OK)

	def _fileInstance(self, mode, func = None, args = (), kwargs = {}):
		f = None
		try:
			f = open(self._file, mode)
			if func is None: return False
			else: return func(f, *args, **kwargs)
		except: return False
		finally:
			if f != None: f.close()

	def _write(self, data, mode):
		def __write(f, data):
			try: f.write(data)
			except: return False
			return True
		return self._fileInstance(mode, __write, args = (data,))

	def delete(self):
		if not self.exists(): return False
		remove(self._file)
		return not self.exists()

	def create(self):
		if not self.exists(): self._fileInstance("w+", None)
		return self.exists()

class DefaultFile(File):

	def overwrite(self, data: str = None):
		if data is None or type(data) != str or not super().exists() or not super().canWrite(): return
		return super()._write(data, "w")

	def write(self, data: str = None):
		if data is None or type(data) != str or not super().exists() or not super().canWrite(): return
		return super()._write(data, "a")

	def overwriteln(self, data: str = None):
		return self.overwrite(data + "\n")

	def writeln(self, data: str = None):
		return self.write(data + "\n")

	def readAllLines(self):
		if not super().exists() or not super().canRead(): return None
		def __read(f):
			return [l.replace("\n", "") for l in f.readlines()]
		return super()._fileInstance("r", __read)

	def readLine(self, line: int = 0):
		if not super().exists() or not super().canRead(): return None
		allLines = self.readAllLines()
		if type(allLines) is list and line <= len(allLines) and line > 0: return allLines[line - 1]
		else: return None

class ListFile(File):

	def writeList(self, data: list = None):
		def _write(file, data):
			try:
				if type(data) != list: return False
				for element in data:
					if element != None: file.write(str(element).replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t").replace("\b", "\\b") + "\n")
					else: return False
				return True
			except Exception: return False
		if type(data) != list: return False
		return super()._fileInstance("w", _write, args = (data,))

	def readList(self):
		def _read(file):
			try: return [l.replace("\n", "").replace("\\n", "\n").replace("\\r", "\r").replace("\\t", "\t").replace("\\b", "\b") for l in file.readlines()]
			except Exception: return False
		return super()._fileInstance("r", _read)

	def addElement(self, element = None):
		tmp = self.readList()
		if not tmp or tmp is None: tmp = []
		tmp.append(element)
		self.writeList(tmp)

	def clear(self):
		self.writeList([])

class Dictionary(File):

	def writeDictionary(self, data: dict = None): pass
	def readDictionary(self): pass
	def addKey(self, key = None, value = None): pass
	def overwriteKey(self, key = None, value = None): pass
	def removeKey(self, key = None): pass
