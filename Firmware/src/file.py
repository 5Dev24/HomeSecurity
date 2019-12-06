from os import remove, access as hasPerm, listdir
from os import R_OK, W_OK, X_OK, F_OK
from os.path import abspath
from .crypt import RSA
from Crypto.PublicKey import RSA as _RSA
import re, math

FILE_EXTENSION = ".dat"

class BaseExceptionForFiles(Exception):

	def __init__(self, originClass = None, cause = None, *args, **kwargs):
		self.__source__ = originClass.__name__.upper()
		self.cause = cause
		super().__init__(self, f"Error Origin: {self.__source__}, Cause: {cause}", *args, **kwargs)

	def __str__(self):
		return f"Error Origin: {self.__source__}, Cause: {self.cause}"

class InvalidFormat(BaseExceptionForFiles): pass
class OverwriteError(BaseExceptionForFiles): pass

class File:

	def __init__(self, file: str = None):
		if not file.endswith(FILE_EXTENSION): file += FILE_EXTENSION
		self._file = abspath(file)

	def __str__(self):
		return f"Name: {self.name()}, Absolute Path: {self._file}, Exists: {self.exists()}, Perms: {self.perms()}"

	def name(self):
		return self._file.split("\\")[::-1][0]

	def perms(self):
		_bin = lambda bol: str(bol * 1)
		return _bin(self.canExecute()) + _bin(self.canRead()) + _bin(self.canWrite())

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

class SimpleFile(File):

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
					if element != None: file.write(str(element).replace("\n", "\\n")\
						.replace("\r", "\\r").replace("\t", "\\t").replace("\b", "\\b") + "\n")
					else: return False
				return True
			except Exception: return False
		if type(data) != list: return False
		return super()._fileInstance("w", _write, args = (data,))

	def readList(self):
		def _read(file):
			try: return [l.replace("\n", "").replace("\\n", "\n").replace("\\r", "\r")\
				.replace("\\t", "\t").replace("\\b", "\b") for l in file.readlines()]
			except Exception: return False
		return super()._fileInstance("r", _read)

	def addElement(self, element = None):
		tmp = self.readList()
		if not tmp or tmp is None: tmp = []
		tmp.append(element)
		return self.writeList(tmp)

	def clear(self): return self.writeList([])

class DictFile(File):

	def writeDict(self, data: dict = None):
		def _write(file, data):
			try:
				if type(data) != dict: return False
				for key, val in data.items():
					if key != None and val != None:
						sanKey = str(key).replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t").replace("\b", "\\b")
						sanVal = str(val).replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t").replace("\b", "\\b")
						file.write(str(len(sanKey)) + ":" + str(key) + str(len(sanVal)) + ":" + str(val) + "\n")
					else: return False
				return True
			except Exception: return False
		if type(data) != dict: return False
		return super()._fileInstance("w", _write, args = (data,))

	def readDict(self):
		def _read(file):
			def helper(inputString):
				split = inputString.split(":")
				keyLength = int(split[0])
				return (inputString[len(str(keyLength)) + 1:keyLength + len(str(keyLength)) + 1], keyLength + len(str(keyLength)) + 1)
			try:
				output = {}
				for line in file.readlines():
					if len(re.compile("[\\d:]+").split(line)) < 2: raise InvalidFormat(DictFile, "Invalid Dictionary Format")
					try:
						keyOut = helper(line)
						valueOut = helper(line[keyOut[1]:])
						key = keyOut[0].replace("\n", "").replace("\\n", "\n").replace("\\r", "\r")\
							.replace("\\t", "\t").replace("\\b", "\b")
						val = valueOut[0].replace("\n", "").replace("\\n", "\n").replace("\\r", "\r")\
							.replace("\\t", "\t").replace("\\b", "\b")
						try: output[key] = val
						except KeyError: pass
					except ValueError: pass
				return output
			except Exception: return False
			return False
		return super()._fileInstance("r", _read)

	def addKey(self, key = None, value = None):
		data = self.readDict()
		if key in data: raise OverwriteError(DictFile, f"Cannot add key \"{key}\" as it already exists")
		else:
			data[key] = value
			return self.writeDict(data)

	def overwriteKey(self, key = None, value = None):
		data = self.readDict()
		if key in data:
			data[key] = value
			return self.writeDict(data)
		else: raise KeyError(f"Cannot override key \"{key}\" as it is not in the dictionary")

	def removeKey(self, key = None):
		data = self.readDict()
		if key in data:
			del data[key]
			return self.writeDict(data)
		else: raise KeyError(f"Cannot remove key \"{key}\" as it is not in the dictionary")

	def clear(self): return self.writeDict({})

class Folder:

	def __init__(self, directory: str):
		self.directory = abspath(directory)
		self.files = []
		for file in listdir(self.directory):
			if file.endswith(FILE_EXTENSION):
				self.files.append(file)

class FileSystem:

	def __init__(self):
		self.absolutePath = abspath(".") + "\\"