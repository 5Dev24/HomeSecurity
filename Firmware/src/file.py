from os import remove, access as hasPerm
from os import R_OK, W_OK, X_OK, F_OK

class FileType:

	CRYPTO_KEY = 0
	LIST = 1
	DICTIONARY = 2
	UNKNOWN = 3

class File:

	def __init__(self, filetype: int = FileType.UNKNOWN, file: str = None):
		self._type = filetype
		self._file = file

	def exists(self): return hasPerm(self._file, F_OK)
	def canWrite(self): return hasPerm(self._file, W_OK)
	def canRead(self): return hasPerm(self._file, R_OK)
	def canExecute(self): return hasPerm(self._file, X_OK)

	def __file(self, mode, func = None, args = (), kwargs = {}):
		f = None
		try:
			f = open(self._file, mode)
			return func(f, *args, **kwargs)
		except: return False
		finally:
			if f != None: f.close()

	def _write(self, data, mode):
		def __write(f, data):
			f.write(data)
		return self.__file(mode, __write, args = (data))

	def override(self, data: str = None):
		if data is None or type(data) != str or not self.exists() or not self.canWrite(): return
		return self._write(data, "w")

	def write(self, data: str = None):
		if data is None or type(data) != str or not self.exists() or not self.canWrite(): return
		return self._write(data, "a")

	def readAll(self):
		if not self.exists() or not self.canRead(): return None
		def __read(f):
			return f.readlines()
		return self.__file("r", __read)

	def readLine(self, line: int = 0):
		if not self.exists() or not self.canRead(): return None
		allLines = self.readAll()
		if allLines is list and line < len(allLines): return allLines[line - 1]
		else: return None

	def delete(self):
		if not self.exists(): return False
		remove(self._file)
		return not self.exists()