from enum import Enum
from threading import Event
from inspect import signature
from re import compile
from . import codes as _codes

class Type(Enum):
	NONE    = 0
	STRING  = 1
	BOOLEAN = 2
	NUMBER = 3

	@staticmethod
	def GetObjectsType(value: object = None):
		if value is None: return Type.NONE
		value_type = type(value)

		if value_type == str: return Type.STRING
		elif value_type == bool: return Type.BOOLEAN
		elif value_type == int or value_type == float: return Type.NUMBER
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

class BaseArgument(tuple):

	def __new__(cls, name: str = "", types: list = None):
		if type(types) != list and type(types) != tuple: types = (types,)
		return tuple.__new__(cls, (name, types))

	@property
	def name(self):
		return tuple.__getitem__(self, 0)

	@property
	def values(self):
		return tuple.__getitem__(self, 1)

class Argument(tuple):

	def __new__(cls, name: str = "", value: Value = None):
		if type(value) is not Value:
			value = Value(value)
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
		self.name = name.lower()

		sig = signature(callback, follow_wrapped=True)
		params = sig.parameters

		assert len(arguments) == len(params), "Function didn't match number of arguments"

		self.callback = callback


		if arguments is not None and len(arguments) > 0:
			if type(arguments) != list and type(arguments) != tuple: arguments = (arguments,)
			self.arguments = {}

			arguments = sorted(arguments, key=lambda arg: arg.name)
			for arg in arguments:
				self.arguments[arg.name] = arg

			self.set_event = Event()
		else:
			self.arguments = {}
			self.set_event = Event()
			self.set_event.set()

	def invoke(self): self()

	def __call__(self):
		if self.arguments_set:
			args = []
			for val in self.arguments.values():
				args.append(val.value.value)
			self.callback(*args)
		else:
			print("Cannot invoke as not all arguments have been set!")

	def set_arguments(self, args: list):
		if self.arguments_set or len(args) != len(self.arguments): return

		mapped_args = self.mapped_arguments(*args)
		if mapped_args is None: return

		out_map = {}

		for arg in mapped_args.values():
			if type(arg) is BaseArgument: return

		for (name, passed) in mapped_args.items():
			out_map[name] = passed

		self.arguments = out_map
		self.set_event.set()

	def mapped_arguments(self, *args: list):
		if self.arguments_set or args is None or (type(args) != tuple and type(args) != list): return None
		if len(args) != len(self.arguments): return None

		owned_args = self.arguments

		for arg in args:
			if arg.name in owned_args.keys():
				owned_arg = owned_args[arg.name]

				if type(owned_arg) is BaseArgument:
					if arg.value_type in owned_arg.values:
						owned_args[arg.name] = arg

					else:
						print("Arg \"", owned_arg.name, "\" didn't accept type " + Type.asString(arg.value_type), sep="")
						return None

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

class TokenOperation(Enum):

	NONE     = 0
	ARGUMENT = 1
	VALUE    = 2
	COMMAND  = 3

class Token:

	def __init__(self, raw: str = "", operation: TokenOperation = TokenOperation.NONE, **data):
		self.raw = raw
		self.op = operation
		self.data = data if data is not None else {}

	def get(self, name: str = ""):
		if name in self.data:
			return self.data[name]

		raise AttributeError(f"{name} isn't a part of this token")

class Handler:

	def __init__(self):
		self.commands = {}
		self.default = None
		self._tokens = []

	def set_default_command(self, cmd: Command = None):
		if cmd is None: return False

		if len(cmd.arguments) != 0: return False

		self.default = cmd
		self.add_command(cmd, True)
		return True

	def add_command(self, cmd: Command = None, override: bool = False):
		if cmd is None: return False

		name = cmd.name.lower()
		if (name in self.commands and override) or (not name in self.commands):
			self.commands[name] = cmd
			return True
		return False

	def lex(self, args: tuple = tuple()):
		def _is_num(value: str = ""):
			integer_pattern = compile(r"\d+")
			float_pattern_1 = compile(r"\d+\.\d+")
			float_pattern_2 = compile(r"\.\d+")

			return integer_pattern.fullmatch(value) or float_pattern_1.fullmatch(value) or float_pattern_2.fullmatch(value)

		if args is None or (type(args) != tuple and type(args) != list): return

		for arg in args:
			arg = str(arg)
			if arg.startswith("--"):
				self._tokens.append(Token(arg, TokenOperation.COMMAND, name=arg[2:]))

			elif arg.startswith("-"):
				self._tokens.append(Token(arg, TokenOperation.ARGUMENT, name=arg[1:]))

			else:
				val = arg
				lowered = arg.lower()

				if lowered in ("true", "false"):
					val = lowered == "true"
				elif _is_num(arg):
					val = float(arg)

				self._tokens.append(Token(arg, TokenOperation.VALUE, value=Value(val)))

	def parse(self):
		if self.default is None:
			return _codes.Arguments.NO_DEFAULT

		if not len(self._tokens):
			self.default.invoke()
			return _codes.Arguments.ONLY_DEFAULT_INVOKED

		current_index = 0
		current = lambda: self._tokens[current_index] if current_index < len(self._tokens) else None
		next = lambda: self._tokens[current_index + 1] if current_index + 1 < len(self._tokens) else None

		arguments = []
		cmd_to_invoke = None

		while current_index < len(self._tokens):
			token = current()
			if token is None: break

			token_op = token.op

			if token_op is TokenOperation.COMMAND:
				cmd_name = token.get("name").lower()
				if cmd_name in self.commands:
					cmd_to_invoke = self.commands[cmd_name]
					current_index += 1
				else:
					return _codes.Arguments.COMMAND_DOESNT_EXIST

			elif token_op is TokenOperation.ARGUMENT:
				var_name = token.get("name").lower()
				arg = None
				next_token = next()
				if next_token is not None:
					next_op = next_token.op
					if next_op is TokenOperation.VALUE:
						arg = Argument(var_name, next_token.get("value"))
						current_index += 2

				if arg is None:
					arg = Argument(var_name, Value(True))
					current_index += 1

				arguments.append(arg)

			elif token_op is TokenOperation.VALUE:
				return _codes.Arguments.VALUE_WITH_NO_VARIABLE

		if cmd_to_invoke is None:
			cmd_to_invoke = self.default

		cmd_to_invoke.set_arguments(arguments)
		cmd_to_invoke.invoke()