from enum import Enum
from threading import Event

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

	def __str__(self):
		return self.name.lower()

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

	def __str__(self):
		return str(self.value) + " is a " + str(self.value_type)

class VariableBase:

	def __init__(self, name: str = "", validTypes: list = list()):
		if type(validTypes) == Type: validTypes = [validTypes,]
		self.name = name
		self.validTypes = validTypes

	def can_set(self, value: Value = None):
		return value.value_type in self.validTypes

	def __str__(self):
		return "Base named " + self.name + " which excepts types " + 

class Variable(VariableBase):

	def __init__(self, name: str = "", validTypes: list = list()):
		super().__init__(name, validTypes)
		self.value = Value(None)
		self.set_event = Event()

	def set_value(self, value: Value = None):
		if self.can_set(value):
			self.value = value
			self.set_event.set()
			return True
		return False

	@property
	def value_set(self):
		return self.set_event.is_set()

class Command:

	def __init__(self, name: str = "", callback = None, arguments: tuple = None):
		self.name = name
		self.callback = callback

		if type(arguments) != list and type(arguments) != tuple: arguments = (arguments,)
		self.arguments = {}

		arguments = sorted(arguments, key=lambda arg: arg.name)
		for arg in arguments:
			self.arguments[arg.name] = arg

		self.set_event = Event()

	def __call__(self):
		if self.arguments_set:
			self.callback()
		else:
			print("Cannot invoke as not all arguments have been set!")

	def set_arguments(self, args: list = None):
		if self.arguments_set or len(args) != len(self.arguments): return

		mapped_args = self.mapped_arguments(args)
		if mapped_args is None: return

		out_map = {}

		for (owned, passed) in mapped_args.items():
			out_map[owned.name] = passed

		self.arguments = out_map
		self.set_event.set()

	def mapped_arguments(self, args: list = None):
		if self.arguments_set or args is None or type(args) != list: return None
		if len(args) != len(self.arguments): return None

		out_args = {}
		owned_args = self.arguments[:]

		for arg in args:
			if arg.name in owned_args.keys():
				owned_arg = owned_args[arg.name]

				if owned_arg.can_set(arg.value):
					out_args[arg.name] = arg

				else:
					print("Arg \"", arg.name, "\" cannot accept type \"", arg.value_type, '"', sep = "")
					return None

			else:
				print("Arg \"", arg.name, "\" doesn't exist", sep="")
				return None

		return out_args

	@property
	def arguments_set(self):
		return self.set_event.is_set()

class Util:

	@staticmethod
	def iter_to_sentence(_iter: list: list()):
		length = len(_iter)
		_iter = [str(val) for val in _iter]
		if length == 0: return ""
		elif length == 1: return _iter[0]
		elif length == 2: return _iter[0] + " and " + _iter[1]
		else:
			pass

class Parser:
	pass
