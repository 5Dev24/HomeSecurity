from os import listdir
from os.path import abspath, isfile, isdir, join

FILE_EXTENSION = ".dat"

class File:

	@staticmethod
	def fromFolder(folder: object = None, fileName: str = ""):
		return File(folder.directory + fileName)

	def __init__(self, file: str = ""):
		self.file = abspath(file)
		assert isfile(self.file), "File didn't lead to a file"

	@property
	def name(self):
		return self.file.split("\\")[::-1][0]

class Folder:

	@staticmethod
	def fromFolder(folder: object = None, directory: str = ""):
		return Folder(folder.directory + directory)

	def __init__(self, directory: str = ""):
		self.directory = abspath(directory) + "\\"
		assert isdir(self.directory), "Directory didn't lead to a folder"

	@property
	def name(self):
		return self.directory.split("\\")[::-1][1 if self.directory.endswith("\\") else 0]

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
		return self.search()[0]

	def search(self):
		found = len(self.files)
		output = {}
		for direct in self.directories:
			dir = Folder.fromFolder(self, direct)
			search = dir.search()
			if search[1] > 0:
				output[dir.name] = search[0]
				found += search[1]
		for file in self.files:
			output[file] = File.fromFolder(self, file)
		return (output, found)

	def __str__(self):
		def traverse(name: str = "", term: dict = None, depth: int = 0):
			out = "\n" + "\t" * depth + name + "\\"
			for key, val in term.items():
				if type(val) is dict: out += traverse(key, val, depth+1)
				if type(val) is File:
					out += "\n" + "\t" * (depth + 1) + key
			return out
		return traverse(self.name, self.map).strip()

	def __repr__(self):
		return self.__str__()

ROOT = Folder(".\\..\\data")