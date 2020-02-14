from os import listdir, access, R_OK, W_OK, F_OK, makedirs, remove
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
	def FromFolder(folder: object = None, fileName: str = ""):
		return File(folder.directory + fileName)

	@staticmethod
	def Exists(folder: object = None, file: str = ""):
		if folder is None: return isfile(abspath(file))
		else: return isfile(abspath(folder.directory + file))

	@staticmethod
	def Delete(folder: object = None, file: str = ""):
		path = file
		if folder is not None: path = folder.directory + path
		path = abspath(path)
		if isfile(path):
			try:
				remove(path)
				return isfile(path)
			except OSError:
				return False
		return False

	@staticmethod
	def Create(folder: object = None, fileName: str = ""):
		if not fileName.endswith(FILE_EXTENSION): fileName += FILE_EXTENSION
		file = (folder.directory if folder is not None else "") + fileName
		f = None
		try:
			f = open(file, "w")
			return File(file)
		except (FileNotFoundError, OSError, PermissionError): return None
		finally:
			if f is not None: f.close()

	@staticmethod
	def GetOrCreate(folder: object = None, fileName: str = ""):
		if not fileName.endswith(FILE_EXTENSION): fileName += FILE_EXTENSION
		if isfile(folder.directory + fileName):
			return File.FromFolder(folder, fileName)
		else:
			return File.Create(folder, fileName)

	@staticmethod
	def read(file: object = None):
		if file is None: return None
		return [line.strip() for line in file.readlines()]

	@staticmethod
	def write(file: object = None, line: str = None):
		if file is None or line is None or type(line) is not str: return False
		if line.count("\n") > 1: return False
		written = file.write(str(line))
		return written == len(line)

	@staticmethod
	def writeln(file: object = None, line: str = None):
		if not line.endswith("\n"): line += "\n"
		return File.write(file, line)

	@staticmethod
	def writelines(file: object = None, lines: list = None):
		if file is None or lines is None or type(lines) is not list: return False
		if not len(lines): return True
		ret = 0
		for i in range(len(lines)):
			line = str(lines[i])
			if i == len(lines) - 1: ret += File.write(file, line)
			else: ret += File.writeln(file, line)
		return ret == len(lines)

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
		except (FileNotFoundError, OSError, PermissionError): return False
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
		if (data is None) or (type(data) is not list): data = list()
		self.data = data

	def write(self, file: File = None):
		assert (self.data is not None) and (type(self.data) is list), "Data was not a list"

		id = str(type(self).ID)[:1]
		checkSum = FileFormat.generateCheckSum(self.data)

		if not len(self.data):
			return file.obj(AccessMode.Overwrite, File.write, (), {"line": f"{id}{checkSum}"})
		else:
			rtn = False
			rtn += file.obj(AccessMode.Overwrite, File.writelines, (), {"lines": [f"{id}{checkSum}\n"] + self.data})
			return rtn == 2

class LogFormat(FileFormat):

	@classmethod
	def internalLoad(cls, header: str = None, lines: list = None):
		from . import logging as _logging

		logs = []
		for line in lines:
			l = _logging.Log.fromString(line)
			if l is not None and type(l) == _logging.Log: logs.append(l)

		return LogFormat(logs)

	ID = 1

	def __init__(self, logs: list = None):
		super().__init__(logs)

class DictionaryFormat(FileFormat):

	@classmethod
	def internalLoad(cls, header: str = None, lines: list = None):
		return cls(Utils.list_to_dictionary(lines))

	ID = 2

	def __init__(self, data: object = None):
		if data is not None:
			if type(data) == dict: super().__init__(Utils.dictionary_to_list(data))
			elif type(data) == list: super().__init__(data)
			else: super().__init__([])
		else: super().__init__([])

	def get_data(self):
		data = self.data
		if data is None or type(data) != list: return None
		data = Utils.list_to_dictionary(data)
		if data is None or type(data) != dict: return None
		return data

class SessionFormat(FileFormat):

	@classmethod
	def internalLoad(cls, header: str = None, lines: list = None):
		from networking import networkables as _networkables

		sessions = []
		for line in lines:
			s = _networkables.Session.fromString(line)
			if s is not None and type(s) == _networkables.Session: sessions.append(s)

		return SessionFormat(sessions)

	ID = 3

	@property
	def sessions(self):
		return self.data[:]

	def add_session(self, session = None):
		from networking import networkables as _networkables
		if type(session) == _networkables.Session:
			self.data.append(session)

class DeviceInfoFormat(DictionaryFormat): # Like a config but set values

	ID = 4

	@property
	def mac(self):
		return self._get("mac")

	@property
	def server(self):
		return self._get("server")

	@property
	def id(self):
		return self._get("server")

	def set_mac(self, value: str = ""):
		self._set("mac", value)

	def set_server(self, value: bool = False):
		self._set("server", value)

	def set_id(self, value: str = ""):
		self._set("id", value)

	def _get(self, name):
		data = super().get_data()
		if data is not None and name in data: return data[name]
		return None

	def _set(self, name, value):
		data = super().get_data()
		if data is not None:
			data[name] = value
			self.data = Utils.dictionary_to_list(data)
		else:
			self.data = Utils.dictionary_to_list({name:value})

class ConfigFormat(DictionaryFormat):

	ID = 5

	def __getattribute__(self, name):
		data = object.__getattribute__(self, "data")
		if data is None: data = []

		if name == "data": return data
		data = Utils.list_to_dictionary(data)
		if name in data:
			return data[name]

		try:
			return object.__getattribute__(self, name)
		except AttributeError as e:
			if len(e.args) > 0:
				e.args = (f"Config didn't contain \"{name}\"",) + e.args[1:]
			raise

	def __setattr__(self, name, value):
		if name == "data" or (str(name).startswith("__") and str(name).endswith("__")):
			object.__setattr__(self, name, value)
			return

		data = Utils.list_to_dictionary(object.__getattribute__(self, "data"))
		data[name] = value
		object.__setattr__(self, "data", Utils.dictionary_to_list(data))

class Utils:

	@staticmethod
	def dictionary_to_list(dictionary: dict = None):
		if dictionary is None or type(dictionary) != dict: return None
		out = []
		for key, value in dictionary.items():
			if type(value) in (int, str, float, bool):
				out.append(f"{key}:{value}")
		return out

	@staticmethod
	def list_to_dictionary(_list: list = None):
		if _list is None or type(_list) != list: return None
		out = {}
		for element in _list:
			if type(element) == str and element.count(":") >= 1:
				element_split = element.split(":")
				element_name = element_split[0]
				element_value = ":".join(element_split[1:])

				try:
					element_value = bool(element_value)
					out[element_name] = element_value
					continue
				except ValueError: pass

				try:
					element_value = int(element_value)
					out[element_name] = element_value
					continue
				except ValueError: pass

				try:
					element_value = float(element_value)
					out[element_name] = element_value
					continue
				except ValueError: pass

				out[element_name] = element_value
		return out

class Folder:

	@staticmethod
	def FromFolder(folder: object = None, directory: str = ""):
		return Folder(folder.directory + directory)

	@staticmethod
	def Create(parent: object = None, folder: str = ""):
		path = folder
		if parent is not None: path = parent.directory + path
		if not isdir(abspath(path)): makedirs(abspath(path))
		return Folder(path)

	@staticmethod
	def Exists(parent: object = None, folder: str = ""):
		if parent is None: return isdir(abspath(folder + sep))
		else: return isdir(abspath(parent.directory + folder + sep))

	@staticmethod
	def GetOrCreate(parent: object = None, folder: str = ""):
		if Folder.Exists(parent, folder): return Folder((parent.directory if parent is not None else "") + folder)
		else: return Folder.Create(parent, folder)

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
			dir = Folder.FromFolder(self, direct)
			search = dir.search()
			if search is not None:
				output[dir.name] = search
		if len(self.files) == 0 and len(output.keys()) == 0: return None
		for file in self.files:
			output[file] = File.FromFolder(self, file)
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
FileSystem = Folder.GetOrCreate(None, FileSystemPath)