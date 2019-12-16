from os import listdir, access, R_OK, W_OK, F_OK
from os.path import abspath, isfile, isdir, join, sep
from enum import Enum

FILE_EXTENSION = ".dat"

class AccessMode(Enum):

	Read = 0
	Overwrite = 1
	Append = 1

	@staticmethod
	def toMode(mode: object = None):
		if mode == AccessMode.Read: return "r"
		elif mode == AccessMode.Overwrite: return "w"
		elif mode == AccessMode.Append: return "a"
		else: return "r"

class File:

	@staticmethod
	def fromFolder(folder: object = None, fileName: str = ""):
		return File(folder.directory + fileName)

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
		for line in lines:
			ret += File.writeln(file, line)
		return not not ret

	def __init__(self, file: str = ""):
		self.file = abspath(file)
		assert isfile(self.file), "File didn't lead to a file"

	@property
	def name(self):
		return self.file.split(sep)[::-1][0]

	@property
	def src(self):
		parts = self.file.split(sep)[:-1]
		if len(parts) == 0: return sep
		return sep.join(parts)

	@property
	def stats(self):
		return (access(self.file, F_OK), access(self.file, R_OK), access(self.file, W_OK))

	def obj(self, mode: AccessMode = AccessMode.Read, func = None, args=(), kwargs={}):
		f = None
		if not self.stats[0]: return False
		if type(mode) is not AccessMode: return False
		if mode.value < 0 or mode.value > 1: return False
		if func is None: return False
		try:
			if self.stats[mode.value + 1]:
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

class Folder:

	@staticmethod
	def fromFolder(folder: object = None, directory: str = ""):
		return Folder(folder.directory + directory)

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
		except PermissionError:
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
		return self.__str__()

FileSystem = Folder(f".{sep}..{sep}data")
