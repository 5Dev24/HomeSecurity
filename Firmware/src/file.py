from os import remove, access as hasPerm
from os import R_OK, W_OK, X_OK, F_OK
from os.path import abspath
from .crypt import RSA
from Crypto.PublicKey import RSA as _RSA
import re, math

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
		return self.writeList(tmp)

	def clear(self): return self.writeList([])

class BaseExceptionForFiles(Exception):

	def __init__(self, originClass = None, cause = None, *args, **kwargs):
		self.__source__ = originClass.__name__.upper()
		self.cause = cause
		super().__init__(self, f"Error Origin: {self.__source__}, Cause: {cause}", *args, **kwargs)

	def __str__(self):
		return f"Error Origin: {self.__source__}, Cause: {self.cause}"

class InvalidFormat(BaseExceptionForFiles): pass
class OverwriteError(BaseExceptionForFiles): pass
class NoKeySaveError(BaseExceptionForFiles): pass
class KeysNotFoundError(BaseExceptionForFiles): pass

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

class RSAFile(DictFile):

	@staticmethod
	def new(file: str = None, isClient: bool = False):
		instance = RSAFile(file)
		rsa = RSA(isClient, None)
		instance.keys = (rsa.privKey(), rsa.pubKey())
		return instance

	@staticmethod
	def newOrFrom(file: str = None, isClient: bool = False):
		instance = RSAFile(file)
		try:
			instance.crypto
			return instance
		except KeysNotFoundError:
			rsa = RSA(isClient, None)
			instance.keys = (rsa.privKey(), rsa.pubKey())
			return instance

	def __init__(self, file: str = None):
		super().__init__(file)

	@property
	def crypto(self):
		keys = self.keys
		key = RSA.addExtraDetailToKey(self._cryptoSplit(keys[1], 64), True)
		if len(keys[0]): key = RSA.addExtraDetailToKey(self._cryptoSplit(keys[0], 64), False)
		if not len(key): raise KeysNotFoundError(RSAFile, "No keys were found in the rsa file (2)")
		return RSA.new(False, bytes(key, "utf-8"))

	def _cryptoSplit(self, key: str = None, length: int = 1):
		return "\n".join([key[length * i:length * (i + 1)] for i in range(math.ceil(len(key) / length))])

	@property
	def keys(self):
		data = self.readDict()
		if (type(data) != dict or (not ("Public" in data)) and (not ("Private") in data)): raise KeysNotFoundError(RSAFile, "No keys were found in the rsa file (1)")
		return (data["Private"], data["Public"])

	@keys.setter
	def keys(self, values: object = None):
		if type(values) == list or type(values) == tuple:
			if len(values) > 0 and len(values) < 3:
				self.writeDict({ "Private": values[0], "Public": values[1] })
		elif type(values) == dict:
			if len(values) > 0 and len(values) < 3:
				if "Public" in values:
					if not ("Private" in values): values = {"Private": ""}.update(values)
					self.writeDict({ "Private": values["Private"], "Public": values["Public"] })
		else: raise NoKeySaveError(RSAFile, f"Unable to save key(s) of the type {type(values).__name__}")
