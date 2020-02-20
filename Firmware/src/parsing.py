from enum import Enum
from threading import Event
from inspect import signature

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

	@staticmethod
	def asString(value: object = None):
		return value._name_.lower()

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

	def __repr__(self):
		if self.value_type == Type.STRING:
			return '"' + self.value + '"'
		return str(self.value)

	def __str__(self):
		return str(self.value) + " is a " + Type.asString(self.value_type)

class Variable:

	def __init__(self, name: str = "", *valid_types: list):
		self.name = name
		self.valid_types = valid_types
		self.value = Value(None)
		self.set_event = Event()

	def can_set(self, value: Value = None):
		return value.value_type in self.valid_types

	def set_value(self, value: Value = None):
		if self.can_set(value):
			self.value = value
			self.set_event.set()
			return True
		return False

	@property
	def value_set(self):
		return self.set_event.is_set()

	def __str__(self):
		types = Util.iter_to_sentence([Type.asString(t) for t in self.valid_types])
		val = "Variable named " + self.name + " which accepts types " + types
		val += " which has" + ("n't" if not self.value_set else "") + " been set to " + repr(self.value)
		return val

class Argument(tuple):

	def __new__(cls, name: str = "", value: Value = None):
		return tuple.__new__(cls, (name, value))

	@property
	def name(self):
		return tuple.__getitem__(self, 0)

	@property
	def value_object(self):
		return tuple.__getitem__(self, 1)

	@property
	def value(self):
		return self.value_object.value

	@property
	def value_type(self):
		return self.value_object.value_type

class Command:

	def __init__(self, name: str = "", callback = None, *arguments: list):
		self.name = name

		sig = signature(callback, follow_wrapped=True)
		params = sig.parameters

		assert len(arguments) == len(params), "Function didn't match number of arguments"

		self.callback = callback

		if type(arguments) != list and type(arguments) != tuple: arguments = (arguments,)
		self.arguments = {}

		arguments = sorted(arguments, key=lambda arg: arg.name)
		for arg in arguments:
			self.arguments[arg.name] = arg

		self.set_event = Event()

	def invoke(self):
		self()

	def __call__(self):
		if self.arguments_set:
			args = []
			for val in self.arguments.values():
				args.append(val.value.value)
			self.callback(*args)
		else:
			print("Cannot invoke as not all arguments have been set!")

	def set_arguments(self, args: list = None):
		if self.arguments_set or len(args) != len(self.arguments): return

		mapped_args = self.mapped_arguments(args)
		if mapped_args is None: return

		out_map = {}

		for arg in mapped_args.values():
			if not arg.value_set: return

		for (name, passed) in mapped_args.items():
			out_map[name] = passed

		self.arguments = out_map
		self.set_event.set()

	def mapped_arguments(self, args: list = None):
		if self.arguments_set or args is None or type(args) != list: return None
		if len(args) != len(self.arguments): return None

		owned_args = self.arguments

		for arg in args:
			if arg.name in owned_args.keys():
				owned_arg = owned_args[arg.name]

				if not owned_arg.value_set:
					owned_arg.set_value(arg.value_object)
					if not owned_arg.value_set:
						print("Arg \"", owned_arg.name, "\" didn't accept type " + Type.asString(arg.value_type), sep="")
						return None

					else:
						owned_args[arg.name] = owned_arg

				else:
					print("Arg \"", owned_arg.name, "\" has already been set" , sep = "")
					return None

			else:
				print("Arg \"", arg.name, "\" doesn't exist", sep="")
				return None

		return owned_args

	@property
	def arguments_set(self):
		return self.set_event.is_set()

	def __str__(self):
		val =  "Command named " + self.name + " which takes " + str(len(self.arguments)) + " arguments that have" + ("n't" if not self.arguments_set else "") + " been set"
		for arg in self.arguments.values():
			val += f"\n\t{arg}"
		return val

class Util:

	@staticmethod
	def iter_to_sentence(_iter: list = list()):
		length = len(_iter)
		_iter = [str(val) for val in _iter]
		if length == 0: return ""
		elif length == 1: return _iter[0]
		elif length == 2: return _iter[0] + " and " + _iter[1]
		else:
			last = _iter[-1]
			out = ""
			for ele in _iter[:-1]:
				out += ele + ", "
			return out + "and " + last

class Parser:
	pass
