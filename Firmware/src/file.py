from os import listdir, access, R_OK, W_OK, F_OK, makedirs
from os.path import abspath, isfile, isdir, join, sep, dirname
from hashlib import sha256
from enum import Enum
from copy import deepcopy

FILE_EXTENSION = ".dat"

class AccessMode(Enum):

	Read = (0, 0)
	Overwrite = (1, 1)
	Append = (2, 1)

	@staticmethod
	def toMode(mode: object = None):
		if mode == AccessMode.Read: return "r"
		elif mode == AccessMode.Overwrite: return "w+"
		elif mode == AccessMode.Append: return "a"
		else: return "r"

class File:

	@staticmethod
	def fromFolder(folder: object = None, fileName: str = ""):
		return File(folder.directory + fileName)

	@staticmethod
	def create(folder: object = None, fileName: str = ""):
		if not fileName.endswith(FILE_EXTENSION): fileName += FILE_EXTENSION
		file = folder.directory + fileName
		f = None
		try:
			f = open(file, "w+")
			return File(file)
		except: return None
		finally:
			if f is not None: f.close()

	@staticmethod
	def getOrCreate(folder: object = None, fileName: str = ""):
		if not fileName.endswith(FILE_EXTENSION): fileName += FILE_EXTENSION
		if isfile(folder.directory + fileName):
			return File.fromFolder(folder, fileName)
		else:
			return File.create(folder, fileName)

	@staticmethod
	def read(file: object = None):
		if file is None: return None
		return [line.strip() for line in file.readlines()]

	@staticmethod
	def write(file: object = None, line: str = None):
		if file is None or line is None or type(line) is not str: return False
		if line.count("\n") > 1: return False
		written = file.write(line)
		return written == len(line)

	@staticmethod
	def writeln(file: object = None, line: str = None):
		if not line.endswith("\n"): line += "\n"
		return File.write(file, line)

	@staticmethod
	def writelines(file: object = None, lines: list = None):
		if file is None or lines is None or type(lines) is not list: return False
		if not len(lines): return True
		ret = False
		for i in range(len(lines)):
			line = str(lines[i])
			if i == len(lines) - 1: ret += File.write(file, line)
			else: ret += File.writeln(file, line)
		return not not ret

	def __init__(self, file: str = ""):
		if not file.endswith(FILE_EXTENSION): file += FILE_EXTENSION
		self.file = abspath(file)
		assert isfile(self.file), "File didn't lead to a file"

	@property
	def name(self):
		return self.file.split(sep)[::-1][0]

	@property
	def src(self):
		return dirname(self.file)

	@property
	def stats(self):
		return (access(self.file, F_OK), access(self.file, R_OK), access(self.file, W_OK))

	def obj(self, mode: AccessMode = AccessMode.Read, func = None, args=(), kwargs={}):
		f = None
		if not self.stats[0]: return False
		if type(mode) is not AccessMode: return False
		if mode.value[1] < 0 or mode.value[1] > 1: return False
		if func is None: return False
		try:
			if self.stats[mode.value[1] + 1]:
				f = open(self.file, AccessMode.toMode(mode))
				return func(f, *args, **kwargs)
			else: return False
		except: return False
		finally:
			if f is not None: f.close()

	def __str__(self):
		return self.file

	def __repr__(self):
		return self.__str__()

class FileFormat:

	@staticmethod
	def generateCheckSum(data: list = None):
		if data is None or type(data) is not list: return None
		return sha256("".join([str(d) for d in data]).encode("utf-8")).digest().hex()

	@staticmethod
	def intialLoad(callingClass = None, lines: list = None):
		try:
			firstLine = lines[0]
			id = int(firstLine[:1])
			checkSum = firstLine[1:65]
			data = lines[1:]

			# Verify that callingClass is a subclass and that id matches on file to the class
			if not issubclass(callingClass, FileFormat): return None
			if callingClass.ID != id: return None

			# Verify checksum
			newCheckSum = FileFormat.generateCheckSum(data)
			if checkSum != newCheckSum: return None

			return callingClass.internalLoad(firstLine, lines[1:])
		except ValueError: return None

	@classmethod
	def loadFrom(cls, file: File = None):
		lines = file.obj(AccessMode.Read, File.read, (), {})
		if lines is None or not len(lines): return None
		return FileFormat.intialLoad(cls, lines)

	@classmethod
	def internalLoad(cls, header: str = None, lines: list = None):
		return FileFormat(lines)

	ID = 0

	def __init__(self, data: list = None):
		if data is None or type(data) is not list: data = list()
		self.data = data

	def write(self, file: File = None):
		assert self.data is not None and type(self.data) != list, "Data was not a list"
		id = str(type(self).ID)[:1]
		checkSum = FileFormat.generateCheckSum(self.data)
		if not len(self.data):
			file.obj(AccessMode.Overwrite, File.write, (), {"line": f"{id}{checkSum}"})
		else:
			file.obj(AccessMode.Overwrite, File.writeln, (), {"line": f"{id}{checkSum}"})
			file.obj(AccessMode.Append, File.writelines, (), {"lines": self.data})

class LogFormat(FileFormat):

	@classmethod
	def internalLoad(cls, header: str = None, lines: list = None):
		logs = []
		from .logging import Log
		for line in lines:
			l = Log.fromString(line)
			if l is not None and type(l) == Log:
				logs.append(l)
		return LogFormat(logs)

	ID = 1

	def __init__(self, logs: list = None):
		super().__init__(logs)

class Folder:

	@staticmethod
	def fromFolder(folder: object = None, directory: str = ""):
		return Folder(folder.directory + directory)

	@staticmethod
	def create(parent: object = None, folder: str = ""):
		path = folder
		if parent is not None and type(parent) is Folder: path = parent.directory + folder
		if not isdir(path): makedirs(path)
		return Folder(path)

	@staticmethod
	def getOrCreate(parent: object = None, folder: str = ""):
		if isdir(folder): return Folder(folder)
		else: return Folder.create(parent, folder)

	def __init__(self, directory: str = ""):
		self.directory = abspath(directory) + sep
		assert isdir(self.directory), "Directory didn't lead to a folder"

	@property
	def name(self):
		return self.directory.split(sep)[::-1][1 if self.directory.endswith(sep) else 0]

	@property
	def src(self):
		parts = self.directory.split(sep)[:-2]
		if len(parts) == 0: return sep
		return sep.join(parts)

	@property
	def files(self):
		try:
			tmpFiles = listdir(self.directory)
			return [f for f in tmpFiles if f.endswith(FILE_EXTENSION) and isfile(join(self.directory, f))]
		except PermissionError:
			return list()

	@property
	def directories(self):
		try:
			tmpDirs = listdir(self.directory)
			return [d for d in tmpDirs if isdir(join(self.directory, d))]
		except (PermissionError, OSError):
			return list()

	@property
	def map(self):
		return self.search()

	def search(self):
		output = {}
		for direct in self.directories:
			dir = Folder.fromFolder(self, direct)
			search = dir.search()
			if search is not None:
				output[dir.name] = search
		if len(self.files) == 0 and len(output.keys()) == 0: return None
		for file in self.files:
			output[file] = File.fromFolder(self, file)
		return output

	def __str__(self):
		def traverse(name: str = "", term: dict = None, depth: int = 0):
			out = "\n" + "\t" * depth + name + sep
			for key, val in term.items():
				if type(val) is dict: out += traverse(key, val, depth+1)
				if type(val) is File:
					out += "\n" + "\t" * (depth + 1) + key
			return out
		return traverse(self.name, self.map).strip()

	def __repr__(self):
		return self.directory

FileSystemPath = dirname(__file__) + f"{sep}..{sep}data"
FileSystem = Folder.getOrCreate(None, FileSystemPath)