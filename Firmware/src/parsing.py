from enum import Enum

class Type(Enum):
	NONE    = 0
	STRING  = 1
	BOOLEAN = 2
	INTEGER = 3
	FLOAT   = 4

	@staticmethod
	def GetObjectsType(value: object = None):
		if value is None: return Type.NONE
		value_type = type(value)

		if value_type == str: return Type.STRING
		elif value_type == bool: return Type.BOOLEAN
		elif value_type == int: return Type.INTEGER
		elif value_type == float: return Type.FLOAT
		else: return Type.NONE

class ArgumentParser:
	pass

class Variable:

	def __init__(self, name: str = "", validTypes: list = list()):
		if type(validTypes) == Type: validTypes = [validTypes,]
		self.name = name
		self.value = Value(None)
		self.validTypes = validTypes

	def can_set(self, value: Value = None):
		return value.value_type in self.validTypes

	def set_value(self, value: Value = None):
		if self.can_set(value):
			self.value = value

# Credit to Sven Marnach
# https://stackoverflow.com/a/4828108
class Value(tuple):

	def __new__(cls, value: object = None):
		return tuple.__new__(cls, (value, Type.GetObjectsType(value)))

	@property
	def value(self):
		return tuple.__getitem__(self, 0)

	@property
	def value_type(self):
		return tuple.__getitem__(self, 1)

	def __getitem__(self, item): raise TypeError

class Command:

	def __init__(self, name: str = "", callback = None):
		self.name = name
		self.callback = callback

	def __call__(self):
		self.callback()
