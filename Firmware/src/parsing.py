import sys as S
from .logging import Log, LogType
from .codes import Parsing, Threading
from . import threading as _threading

class ArgumentParser:

	def __init__(self, doLog: bool = False, handler: dict = None):
		self._doLog = False if doLog is None else doLog
		self._isHandledStorage = tuple([False]) * 6
		self._vars = { "all": {}, "required": {}, "optional": {} }
		self._handler = self._initHandler(handler if type(handler) == dict else {})
		self._parsedArgs = None

	def __str__(self):
		return "Handler: " + str(self._handler) + "\nHandle Storage: " + str(self._isHandledStorage) + "\
			\nParsed Arguments: " + str(self._parsedArgs) + "\nVariables: " + str(self._vars)

	def _initHandler(self, handler: dict = None):

		def isValidArgValueType(argValueType: str = ""):
			for argType in argValueType.split("|"):
				if not (argType == "string" or argType == "int" or argType == "float" or argType == "boolean"): return False
			return True

		handled = [False] * 6
		output = {
				"cmds": { "help": { "invoke": lambda: print(self._autoGenerateHelpMsg()), "description": "Outputs a basic help menu" } },
				"vars": { "required": {}, "optional": {} },
				"none": lambda: print("Use --help to see a list of options")
		}

		if handler is None: return output
		if "cmds" in handler: handled[0] = True

		if "vars" in handler:
			handled[2] = True
			if "required" in handler["vars"]: handled[3] = True
			if "optional" in handler["vars"]: handled[4] = True

		if "none" in handler: handled[5] = True
		self._isHandledStorage = tuple(handled)

		if handled[0]: output["cmds"] = handler["cmds"]
		if not handled[1]: output["cmds"]["help"] = {
				"invoke": lambda: print(self._autoGenerateHelpMsg()),
				"description": "Outputs a basic help menu"
			}

		if handled[2]:
			output["vars"] = handler["vars"]
			if handled[3]:
				output["vars"]["required"] = handler["vars"]["required"]
				for var in handler["vars"]["required"].items():
					if var[0] in self._vars["all"]: continue
					if (not (type(var[0]) is str)) or (not (type(var[1]) is str)): continue
					if not isValidArgValueType(var[1]): continue
					varObj = [var[1], self._getDefaultValueForA(var[1])[0], "required", False]
					self._vars["all"][var[0]] = varObj
					self._vars["required"][var[0]] = varObj
			if handled[4]:
				output["vars"]["optional"] = handler["vars"]["optional"]
				for var in handler["vars"]["optional"].items():
					if var[0] in self._vars["all"]: continue
					if (not (type(var[0]) is str)) or (not (type(var[1]) is str)): continue
					if not isValidArgValueType(var[1]): continue
					varObj = [var[1], self._getDefaultValueForA(var[1])[0], "optional", False]
					self._vars["all"][var[0]] = varObj
					self._vars["optional"][var[0]] = varObj

		if handled[5]: output["none"] = handler["none"]

		return output

	def _resolveTypeString(self, typeString: str = ""):
		types = typeString
		if '|' in types:
			if types.count('|') == 1: types = types.split('|')[0] + " or " + types.split('|')[1]
			else:
				_types = types.split('|')
				newTypes = ""
				for i in range(len(_types)):
					if i == len(_types) - 2: newTypes += _types[i] + ", or "
					else: newTypes += _types[i] + ", "
				types = newTypes[:len(newTypes) - 2]

		return types

	def _autoGenerateHelpMsg(self):
		out = ""
		if len(self._handler["cmds"]) > 0:
			out += "Commands:"
			for cmdName, cmdData in self._handler["cmds"].items():
				if cmdData is not None and type(cmdData) == dict and "description" in cmdData:
					desc = cmdData["description"]
					out += f"\n\t{cmdName}: {desc}"

		if len(self._vars["all"]) > 0:
			if not len(out):
				out += S.argv[0]
			else:
				out += "\n\n" + S.argv[0]
			required = len(self._vars["required"]) > 0
			optional = len(self._vars["optional"]) > 0

			if required:
				for arg in self._vars["required"].keys():
					out += " <" + arg + ">"

			if optional:
				for arg in self._vars["optional"].keys():
					out += " (" + arg + ")"

			if required or optional: out += "\n"
			if required:
				out += "Required Arguments:"
				for arg in self._vars["required"].items():
					out += "\n\t" + arg[0] + "\t->\t" + self._resolveTypeString(arg[1][0])
				if optional: out += "\n"

			if optional:
				out += "Optional Arguments:"
				for arg in self._vars["optional"].items():
					out += "\n\t" + arg[0] + "\t->\t" + self._resolveTypeString(arg[1][0])

		return out

	def _getDefaultValueForA(self, typeString: str = ""):
		types = typeString.split('|')
		out = []
		for _type in types:
			if _type == "string": out.append("")
			elif _type == "int": out.append(0)
			elif _type == "float": out.append(0.0)
			elif _type == "boolean": out.append(False)
			else: return [None]

		return out

	def _isValidValueFor(self, mode: int = 0, var: str = "", typeToCheck: object = ""):
		if var in self._vars["all"]:
			if mode == 0:
				for typePossible in self._vars["all"][var][0].split("|"):
					if typePossible == typeToCheck: return True
			elif mode == 1:
				for typePossible in self._vars["all"][var][0].split("|"):
					allTypes = self._getDefaultValueForA(typePossible)
					for _type in allTypes:
						if type(typeToCheck) == type(_type): return True
			else: return False
		return False

	def _parse(self, args: list = None):

		def unknownArgumentParse(arg: str = ""):
			argType = "string"
			if len(arg) == 0: return None
			if arg.startswith("-") and not arg.startswith("--"): return ["var", arg[1:].lower()]
			elif arg.startswith("--"): return ["cmd", arg[2:].lower()]
			elif arg.lower() in ("true", "false"): return ["boolean", arg.lower() == "true"]
			else:
				try:
					num = None
					if arg.count(".") == 1:
						num = float(arg)
						argType = "float"
					elif arg.count(".") > 1: return ["string", arg]
					elif arg.isdigit():
						num = int(arg)
						argType = "int"
					if not (num is None): arg = num
					else: argType = "string"
				except ValueError: pass
			return [argType, arg]

		newArgs = []
		for arg in args:
			if ' ' in arg: newArgs.append("'" + arg + "'")
			else: newArgs.append(arg)
		args = ' '.join(newArgs)
		inString = False
		string = ""
		prevChar = ''
		index = 0
		arg = ""
		out = []

		while index < len(args):
			char = args[index]
			if char == "'":
				if prevChar != '\\':
					inString = not inString
					if not inString:
						out.append(["string", string])
						string = ""
				else: string = string[:len(string) - 1] + "'"
			elif inString: string += char
			elif char == ' ' and not inString:
				newArg = unknownArgumentParse(arg)
				if not (newArg is None): out.append(newArg)
				arg = ""
			else: arg += char
			prevChar = char
			index += 1

		if len(arg) != 0:
			finalArgument = unknownArgumentParse(arg)
			if not (finalArgument is None): out.append(finalArgument)

		return out

	def isHandled(self, toHandle: str = ""):
		toHandle = toHandle.lower()
		if toHandle == "cmds": return self._isHandledStorage[0]
		elif toHandle == "help": return self._isHandledStorage[1]
		elif toHandle == "vars": return self._isHandledStorage[2]
		elif toHandle == "required vars": return self._isHandledStorage[3]
		elif toHandle == "optional vars": return self._isHandledStorage[4]
		elif toHandle == "none": return self._isHandledStorage[5]
		return False

	def parse(self, args: list = None):
		if not (type(args) is list): return
		self._parsedArgs = self._parse(args)

	def execute(self, ignoreArguemntRequirements: bool = False):
		parsed = lambda index: self._parsedArgs[index]
		handler = lambda index: self._handler[index]
		argData = lambda index: parsed(index)

		def getHandlerCmd(cmd: str = ""):
			cmds = handler("cmds")
			if cmd is None: return None
			if type(cmds) is dict and cmd in cmds: return cmds[cmd]
			return None

		def doesVariableExist(var: str = ""):
			for _var in self._vars["all"].items():
				if _var[0] == var: return True
			return False

		def allNotSetVars():
			args = []
			for var in self._vars["required"].items():
				if var[1][3] == False:
					name = var[0]
					types = self._resolveTypeString(var[1][0])
					args.append((name, types))
			return args

		def areAllRequiredArgsSet():
			return len(allNotSetVars()) == 0

		pairIndex = 0
		remaining = lambda: len(self._parsedArgs) - pairIndex
		if remaining() == 0:
			if self._doLog: handler("none")()
			return Parsing.NO_EXECUTION
		cmdToExecute = None

		while pairIndex < len(self._parsedArgs):
			argT, argV = argData(pairIndex)
			if argT == "cmd":
				cmd = getHandlerCmd(argV)
				if type(cmd) == dict:
					if pairIndex == 0 and remaining() == 1:
						try:
							cmd["invoke"]()
							return Parsing.SUCCESS_AFTER_COMMAND
						except Exception as e:
							if type(e) != _threading.SimpleClose:
								return Parsing.ERROR_THROWN
							else:
								return Threading.FORCE_CLOSE
					else:
						cmdToExecute = cmd["invoke"]
						pairIndex += 1
				elif self._doLog:
					Log(LogType.Warn, "Invalid command \"--" + argV + "\", use --help to see a list of commands", False).post()
					return Parsing.NO_COMMAND

			elif remaining() >= 2 and argT == "var":
				if doesVariableExist(argV):
					tmpT, tmpV = argData(pairIndex + 1)
					if self._isValidValueFor(0, argV, tmpT):
						self._vars["all"][argV][1] = tmpV
						self._vars["all"][argV][3] = True
						pairIndex += 2
						continue
					else:
						if self._doLog:
							Log(LogType.Warn, "Invalid value type for variable " + argV + ",\nexpected " + self._vars["all"][argV][0] + " but got " + tmpT, False).post()
						return Parsing.INVALID_TYPE
				else:
					if self._doLog:
						Log(LogType.Warn, "Unknown variable \"" + argV + '"', False).post()
					return Parsing.NO_VARIABLE

			elif pairIndex == 0:
				if self._doLog: handler("none")()
				return Parsing.NO_EXECUTION
			else:
				break

		if not ignoreArguemntRequirements and not areAllRequiredArgsSet():
			if self._doLog:
				Log(LogType.Warn, "Not all required variables have been set!\nThe following values need to be set:" + "".join(["\n\t" + arg[0] + "\t->\t" + arg[1] for arg in allNotSetVars()]), False).post()
			return Parsing.MISSING_REQUIRED

		if cmdToExecute is not None:
			try:
				cmdToExecute()
				return Parsing.SUCCESS_AFTER_ARGS_AND_COMMAND
			except Exception as e:
				if type(e) != _threading.SimpleClose:
					return Parsing.ERROR_THROWN
				else:
					return Threading.FORCE_CLOSE

		return Parsing.SUCCESS

	def readVariable(self, var: str = ""):
		if not (var in self._vars["all"]): return None
		else: return self._vars["all"][var][1]

	def wasVariableSet(self, var: str = ""):
		"""
		Determined Codes:
			1 -> Variable exists and was set to something (Good)
			0 -> Variable exists but wasn't set (Good)
		   -1 -> Variable doesn't exist (Bad)
		"""
		if var in self._vars["all"]:
			if self._vars["all"][var][3]: return 1
			else: return 0
		else: return -1

	def writeVariable(self, var: str = "", value: object = None):
		"""
		Write Codes:
			0 -> Variable exists and was written to successfully
		   -1 -> Variable exists but an invalid type was attempt to be used to set it to
		   -2 -> Variable doesn't exist
		"""
		if self.wasVariableSet(var) >= 0:
			if self._isValidValueFor(1, var, value):
				self._vars["all"][var][1] = value
				return 0
			else: return -1
		else: return -2
