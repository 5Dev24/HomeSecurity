from os import access as hasPerm
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

	def _write(self, data, mode):
		f = None
		try:
			f = open(self._file, mode)
			f.write(data)
		except: pass
		finally: if f != None: f.close()

	def override(self, data: str = None):
		if data is None or type(data) != str or not self.exists() or not self.canWrite(): return
		f = open(self._file, "w")
		f.write(data)
		f.close()

	def write(self, data: str = None):
		if data is None or type(data) != str or not self.exists() or not self.canWrite(): return
		f = open(self._file, "a")
		f.write(data)
		f.close()