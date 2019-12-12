from os import listdir
from os.path import abspath, isfile, isdir, join

FILE_EXTENSION = ""

class Folder:

	def __init__(self, directory: str = "", isAbsPath: bool = False):
		if isAbsPath: self.directory = abspath(directory) + "\\"
		else: self.directory = abspath(ROOT.directory + directory) + "\\"

	@property
	def files(self):
		try:
			tmpFiles = listdir(self.directory)
			return [f for f in tmpFiles if isfile(join(self.directory, f)) and f.endswith(FILE_EXTENSION)]
		except PermissionError:
			return list()

	@property
	def directories(self):
		try:
			tmpDirs = listdir(self.directory)
			return [d for d in tmpDirs if isdir(join(self.directory, d))]
		except PermissionError:
			return list()

	def printout(self, recursive: bool = False, depthStop: int = 3):
		def search(parent: str = "", dir: str = "", depth: int = 0):
			fold = Folder(join(parent, dir), True)
			files = fold.files
			dirs = fold.directories
			foundfiles = len(files)
			if depth == 0:
				out = join(parent, dir) + "\\"
			else:
				out = "\t" * (depth) + dir + "\\"
			if len(dirs) > 0:
				for direct in dirs:
					if depth < depthStop:
						searchReturn = search(join(parent, dir), direct, depth + 1)
						if searchReturn[1] > 0:
							out += "\n" + searchReturn[0]
							foundfiles += searchReturn[1]
					else:
						out += "\n" + "\t" * (depth) + dir + "\\"
			if len(files) > 0:
				for file in files:
					out += "\n" + "\t" * (depth + 1) + file
			return (out, foundfiles)

		if recursive: depthStop = 0
		return search(abspath(self.directory + "\\.."), self.directory.split("\\")[::-1][1])[0]

	def __repr__(self):
		return self.printout()

ROOT = Folder(".", True)