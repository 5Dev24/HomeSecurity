'''
serv --help
serv -port 80 -pswd 4532
serv --h
'''

class ArgumentParser:

	def __init__(self, handler: list = None):
		self._handler = handler if not (handler is None) and handler is dict else {}
		self._parsedArgs = None

	def _initParse(self, args: list = None):
		def unknownArgumentParse(arg: str = ""):
			argType = "argument"
			if len(arg) == 0: return None
			if arg.startswith("-") and not arg.startswith("--"): argType = "func"
			elif arg.startswith("--"): return ["cmd", arg[2:]]
			try:
				num = -1
				if '.' in arg:
					num = float(arg)
					argType = "float"
				else:
					num = int(arg)
					argType = "int"
				if not (num is None): arg = num
				else: argType = "argument"
			except ValueError: pass
			return [argType, arg]

		newArgs = []
		for arg in args:
			if ' ' in arg: newArgs.append('"' + arg + '"')
			else: newArgs.append(arg)
		args = ' '.join(args)
		inString = False
		string = ""
		prevChar = ''
		index = 0
		arg = ""
		out = []
		while index < len(args):
			if args[index] == '"':
				if prevChar != '\\':
					inString = not inString
					if not inString:
						out.append(["string", string])
						string = ""
				else: string = string[:len(string) - 1] + '"'
			elif inString: string += args[index]
			elif args[index] == ' ' and not inString:
				newArg = unknownArgumentParse(arg)
				if not (newArg is None): out.append(newArg)
				arg = ""
			else: arg += args[index]
			prevChar = args[index]
			index += 1
		finalArgument = unknownArgumentParse(arg)
		if not (finalArgument is None): out.append(finalArgument)
		return out

	def parse(self, args: list = None):
		if args is None: return {}
		args = self._initParse(args)
		onlyCmd = False
		for arg in args:
			if arg[0] == "cmd": onlyCmd = True
		if onlyCmd: self._parsedArgs = [["cmd", args[0][1]]]
		self._parsedArgs = args
		print(self._parsedArgs)

	def execute(self):
		parsed = lambda index: self._parsedArgs[index]
		handler = lambda index: self._handler[index]
		val01 = lambda index: parsed(index)[0]
		val02 = lambda index: parsed(index)[1]
		val11 = lambda index1, index2: handler(index1)[index2][0]
		val12 = lambda index1, index2: handler(index1)[index2][1]
		def withinList(_list: list = None, _str: str = ""):
			for item in _list:
				if item is str and item.lower() == _str: return True
			return False
		def getHandlerCmd(cmd: str = ""):
			for kvp in self._handler.values():
				cmds = None
				if (kvp.key is list and withinList(kvp.key, "cmds")) or (kvp.key is str and kvp.key.lower() == "cmds"): cmds = self._handler[kvp.key]
				else: continue
				if cmds is None: continue
				print(cmds is dict)
				print(cmd[2:])
				print(cmd[2:] in cmds.keys)
				print(cmds[cmd[2:]])
				if cmds is dict and cmd[2:] in cmds.keys and cmds[cmd[2:]] != None: return cmds[cmd[2:]]
				return None
			return None
		pairIndex = 0
		remaining = lambda: len(self._parsedArgs) - pairIndex
		while pairIndex < len(self._parsedArgs):
			if pairIndex == 0 and not (getHandlerCmd(val01(pairIndex)) is None):
				getHandlerCmd(val01(pairIndex))()
				break
			else: break
