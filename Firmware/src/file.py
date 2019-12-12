from os import listdir
from os.path import abspath, isfile, isdir, join

FILE_EXTENSION = ".dat"

class Folder:

	def __init__(self, directory: str = "", isAbsPath: bool = False):
		if isAbsPath: self.directory = abspath(directory) + "\\"
		else: self.directory = abspath(ROOT.directory + directory) + "\\"

	@property
	def name(self):
		return self.directory.split("\\")[::-1][1]

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
		return self._search()[0]

	def _search(self, base: str = ""):
		found = len(self.files)
		output = {}
		for direct in self.directories:
			dir = Folder(join(self.directory, direct), True)
			search = dir._search(self.name)
			if search[1] > 0:
				output[dir.name] = search[0]
				found += search[1]
		for file in self.files:
			output[file] = None # None will be preplaced with a File object once everything for Folders is set up
		return (output, found)

	def __str__(self):
		def search(name: str = "", term: dict = None, depth: int = 0):
			out = "\n" + "\t" * depth + name + "\\"
			for key, val in term.items():
				if type(val) is dict: out += search(key, val, depth+1)
				if val is None:
					out += "\n" + "\t" * (depth + 1) + key
			return out

		return search(self.name, self.map).strip()

	def __repr__(self):
		return self.__str__()

ROOT = Folder("..\\data", True)