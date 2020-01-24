import sys as S

class ArgumentParser:
	"""
	Handles argument parsing
	"""

	def __init__(self, doLog: bool = False, handler: dict = None):
		"""
		Init

		Args:
			doLog (bool): If logging errors should be enabled or not
			handler (dict): The argument handler

		Attributes:
			_doLog (bool): If the parser should log
			_isHandledStorage (tuple): If each part of the handling is handled in the handler
			_vars (dict): The handling variables
			_handler (dict): The handling configuration
			_parsedArgs (list): All of the arguments that have been parsed
		"""
		self._doLog = False if doLog is None else doLog # Should logging of errors be enabled
		self._isHandledStorage = tuple([False]) * 6 # Create private handled storage
		self._vars = { "all": {}, "required": {}, "optional": {} } # Create private table of variables
		self._handler = self._initHandler(handler if type(handler) == dict else {}) # Generate a handler that is valid
		self._parsedArgs = None # Create parsed arguments for execution

	def __str__(self):
		"""
		Converts the object to a string

		Returns:
			str: This classes data in a string format
		"""
		return "Handler: " + str(self._handler) + "\nHandle Storage: " + str(self._isHandledStorage) + "\
			\nParsed Arguments: " + str(self._parsedArgs) + "\nVariables: " + str(self._vars) # Convert all data into strings and label them

	def _initHandler(self, handler: dict = None):
		"""
		Handles the initial handler passed to this class

		Args:
			handler (dict): The initial handler

		Returns:
			dict: The new handler
		"""

		def isValidArgValueType(argValueType: str = ""):
			"""
			Checks for invalid argument types

			Args:
				argValueType (str): The original argument string

			Returns:
				bool: False if an invalid type was found, else True
			"""
			for argType in argValueType.split("|"): # Split argument by |'s
				if not (argType == "string" or argType == "int" or argType == "float" or argType == "boolean"): return False # If it isn't a valid argument type, return False
			return True # Return True if all argument types are valid

		handled = [False] * 6 # A list of which parts were handled by the initial handler
		output = {
				"cmds": { "help": { "invoke": lambda: print(self._autoGenerateHelpMsg()), "description": "Outputs a basic help menu" } },
				"vars": { "required": {}, "optional": {} },
				"none": lambda: print("Use --help to see a list of options")
		} # Default handler with all possible parts created
		if handler is None: return output # If the handler is None then return the default handler
		if "cmds" in handler: # If the cmds key is found
			handled[0] = True # Set that the cmds is handled
		if "vars" in handler: # If the vars key is found
			handled[2] = True # Set that the vars is handled
			if "required" in handler["vars"]: handled[3] = True # If the required key is found within the vars value, then set that it's handled
			if "optional" in handler["vars"]: handled[4] = True # If the optional key is found within the vars value, then set that it's handled
		if "none" in handler: handled[5] = True # If the none key is found, then set that it's handled
		self._isHandledStorage = tuple(handled) # Convert the handled list to a tuple and save it to the handled storage
		if handled[0]: output["cmds"] = handler["cmds"] # If cmds was handled, set output cmds to the handler cmds
		if not handled[1]: output["cmds"]["help"] = { # If help cmd doesn't exist
				"invoke": lambda: print(self._autoGenerateHelpMsg()), # Add default invoke
				"description": "Outputs a basic help menu" # Add default description
			}
		if handled[2]: # If vars was handled
			output["vars"] = handler["vars"] # Set output vars to handler vars
			if handled[3]: # If required arguments was handled
				output["vars"]["required"] = handler["vars"]["required"] # Set output required vars to handler required vars
				for var in handler["vars"]["required"].items(): # Loop over all required arguments as var
					if var[0] in self._vars["all"]: continue # If argument is already in the list of arguments, go to next element
					if (not (type(var[0]) is str)) or (not (type(var[1]) is str)): continue # If the key or value isn't a string, go to next element
					if not isValidArgValueType(var[1]): continue # If the argument type isn't valid, then go to next element
					varObj = [var[1], self._getDefaultValueForA(var[1])[0], "required", False] # Create new list of argument type, defualt value, required type, and if it's been set
					self._vars["all"][var[0]] = varObj # Set the key of the variable's name in vars all dictionary to be the variable's object
					self._vars["required"][var[0]] = varObj # Set the key of the variable's name in vars requried dictionary to be the variable's object (shared object)
			if handled[4]: # If optional arguments was handled
				output["vars"]["optional"] = handler["vars"]["optional"] # Set output optional vars to handler optional vars
				for var in handler["vars"]["optional"].items(): # Loop over all optional arguments as var
					if var[0] in self._vars["all"]: continue # If argument is already in the list of arguments, go to next element
					if (not (type(var[0]) is str)) or (not (type(var[1]) is str)): continue # If the key or value isn't a string, go to next element
					if not isValidArgValueType(var[1]): continue # If the argument type isn't valid, then go to next element
					varObj = [var[1], self._getDefaultValueForA(var[1])[0], "optional", False] # Create new list of argument type, defalt value, and optional type
					self._vars["all"][var[0]] = varObj # Set the key of the variable's name in vars all dictionary to be the variable's object
					self._vars["optional"][var[0]] = varObj # Set the key of the variable's name in vars optional dictionary to be the variable's object (shared object)
		if handled[5]: output["none"] = handler["none"] # If none was handled, set output none to be handler none
		return output # Return output dictionary

	def _resolveTypeString(self, typeString: str = ""):
		"""
		Takes a type string and tries to break it down into all types

		Args:
			typeString (str): The type string for a variable

		Returns:
			str: The generated type string
		"""
		types = typeString # Get the variables type(s)
		if '|' in types: # If types contains any |'s
			if types.count('|') == 1: types = types.split('|')[0] + " or " + types.split('|')[1] # If he number of |'s is 2 then manually generate the type string
			else:
				_types = types.split('|') # Split on |'s in types
				newTypes = "" # New type string
				for i in range(len(_types)): # Loop through 0 to the number of splits
					if i == len(_types) - 2: newTypes += _types[i] + ", or " # If it's the second to last element then add the type and ", or "
					else: newTypes += _types[i] + ", " # Add the type and ", "
				types = newTypes[:len(newTypes) - 2] # Remove the extra ", " from the end of the type string and then override the type string
		return types # Return the resolved type string

	def _autoGenerateHelpMsg(self):
		"""
		Generates the default help message for an argument parser

		Returns:
			str: The default help message
		"""
		out = "" # Output variable
		if len(self._handler["cmds"]) > 0: # If and commands exist
			out += "Commands:"
			for cmdName, cmdData in self._handler["cmds"].items(): # Loop through each command
				if cmdData is not None and type(cmdData) == dict and "description" in cmdData: # Check if data is valid
					desc = cmdData["description"] # Get command description
					out += f"\n\t{cmdName}: {desc}" # Add command info to output
		if len(self._vars["all"]) > 0: # If vars conains any variables
			if not len(out): # If output is empty
				out += S.argv[0] # Get name of program executed
			else:
				out += "\n\n" + S.argv[0] # Get name of program executed
			required = len(self._vars["required"]) > 0 # If there are any required arguments
			optional = len(self._vars["optional"]) > 0 # If there are any optional arguments
			if required: # If there are required arguments
				for arg in self._vars["required"].keys(): # Loop through the names' of the required arguments as arg
					out += " <" + arg + ">" # Add ' <' to the front and a '>' to the end of the name
			if optional: # If there are optional arguments
				for arg in self._vars["optional"].keys(): # Loop through the names' of the optional arguments as arg
					out += " (" + arg + ")" # Add ' (' to the front and a ')' to the end of the name
			if required or optional: out += "\n" # Add a new line charcater if there are required or optional arguments
			if required: # If there are required arguments
				out += "Required Arguments:" # Add a string of required arguments with a new line character
				for arg in self._vars["required"].items(): # Loop through the key, value pair of each required argument as arg
					out += "\n\t" + arg[0] + "\t->\t" + self._resolveTypeString(arg[1][0]) # Add the name and type(s) of the argument to the output
				if optional: out += "\n" # If there are an optional arguemnts, add a new line character
			if optional: # If there are optional arguments
				out += "Optional Arguments:" # Add a string of optional arguments with a new line character
				for arg in self._vars["optional"].items(): # Loop through the key, value pair of each optional argument as arg
					out += "\n\t" + arg[0] + "\t->\t" + self._resolveTypeString(arg[1][0]) # Add the name and type(s) of the argument to the output
		return out # Return generated help message

	def _getDefaultValueForA(self, typeString: str = ""):
		"""
		Used to get the default value of variables

		Args:
			argType (str): The argument type string

		Returns:
			object: The default value or None if a valid argument type wasn't found
		"""
		types = typeString.split('|') # Get all valid argument types for a given argument
		out = []
		for _type in types:
			if _type == "string": out.append("") # If its type is string, return an empty string
			elif _type == "int": out.append(0) # If its type is integer, return a 0
			elif _type == "float": out.append(0.0) # If its type is float, return a 0.0
			elif _type == "boolean": out.append(False) # If its type is boolean, return False
			else: return [None]
		return out # If unable to find type, return None

	def _isValidValueFor(self, mode: int = 0, var: str = "", typeToCheck: object = ""):
		"""
		Checks if a given value is correct for a variable

		Args:
			mode (int): 0 = By type name, 1 = By object type, default 0
			var (str): The variable's name
			typeToCheck (object): The type

		Returns:
			bool: If that the type is a valid type for the variable
		"""
		if var in self._vars["all"]: # If the varialbe is in the list of all variables
			if mode == 0: # If in by type string
				for typePossible in self._vars["all"][var][0].split("|"): # Loop through each one of it's item(s) as typePossible
					if typePossible == typeToCheck: return True # If typePossible is typeToCheck, then return True
			elif mode == 1: # If in by object type
				for typePossible in self._vars["all"][var][0].split("|"): # Loop through each one of it's item(s) as typePossible				
					allTypes = self._getDefaultValueForA(typePossible)
					for _type in allTypes: # Loop through each of the variables' types
						if type(typeToCheck) == type(_type): return True # If typePossible's type is typeToCheck's type, then return True
			else: return False # Invalid mode passed
		return False # Default return False

	def _parse(self, args: list = None):
		"""
		Parses out a list of agruments

		Args:
			args (list): List of arguments, all strings

		Returns:
			list: Parsed arguments ready to be executed
		"""
		def unknownArgumentParse(arg: str = ""):
			"""
			Figures out which type the specific argument is based off of the string

			Args:
				arg (str): The argument to decipher

			Returns:
				list: The type and the value (casted to proper type)
			"""
			argType = "string" # Default to string
			if len(arg) == 0: return None # If an empty string was sent, return a None
			if arg.startswith("-") and not arg.startswith("--"): return ["var", arg[1:].lower()] # If argument starts with only a signle '-', then return that it's a variable and remove the '-'
			elif arg.startswith("--"): return ["cmd", arg[2:].lower()] # If argument starts with two '-', then return that it's a command and remove the '--' from the beginning
			elif arg.lower() in ("true", "false"): return ["boolean", arg.lower() == "true"] # If argument is 'true' or 'false' (not case sensitive), then return it's a boolean and the boolean value
			else:
				try:
					num = None # Default to -1
					if arg.count(".") == 1: # If there is only a single '.' in the string
						num = float(arg) # Case to float
						argType = "float" # Set type to float if no exception was raised
					elif arg.count(".") > 1: return ["string", arg] # If the number of .'s is greater than 1, then return that it's a string and the string
					elif arg.isdigit(): # If the string is made of only digits (0-9)
						num = int(arg) # Case to int
						argType = "int" # Set type to int if no exception was raised
					if not (num is None): arg = num # If the num isn't None, then set arg to num
					else: argType = "string" # If it is None, then default to string type
				except ValueError: pass # If an error is thrown then continue as though it's a string
			return [argType, arg] # Return the argument type and the argument value (casted)

		newArgs = [] # List of new arguments after checking for simple strings
		for arg in args: # Loop through each argument as arg
			if ' ' in arg: newArgs.append("'" + arg + "'") # If there is a space (that means it was a string), then add it to the argument list with quotes around it
			else: newArgs.append(arg) # If it doesn't have a space then just keep it as is
		args = ' '.join(newArgs) # Rejoin all of the arguments with a space as a separator
		inString = False # If a string is currently being read
		string = "" # The current string being read
		prevChar = '' # The previously parsed character
		index = 0 # The current index location
		arg = "" # The currently being generated argument, for unknown parsing
		out = [] # The new list of executable arguments
		while index < len(args): # While the index isn't outside of the argument list
			char = args[index] # The current character
			if char == "'": # If character is a '
				if prevChar != '\\': # If the previous character isn't a '\'
					inString = not inString # Invert the inString value
					if not inString: # If the string has ended
						out.append(["string", string]) # Add the argument type of string and the string to the output list
						string = "" # Reset the string value
				else: string = string[:len(string) - 1] + "'" # If the previous string was a '|' then remove the previous character and add a '"'
			elif inString: string += char # If currently in a string and a '"' isn't the current character then add the character to the string
			elif char == ' ' and not inString: # If a space occured and it isn't a string
				newArg = unknownArgumentParse(arg) # Try to parse this unknown argument
				if not (newArg is None): out.append(newArg) # If something other than a None was returned, then add it to the output list
				arg = "" # Reset argument variable regardless
			else: arg += char # Always add the char to the current argument as a last-case senario
			prevChar = char # Set previous character to be the current character
			index += 1 # Increment the index
		if len(arg) != 0: # If arg isn't empty
			finalArgument = unknownArgumentParse(arg) # Try to parse arg
			if not (finalArgument is None): out.append(finalArgument) # If another other than a None, then add it to the output list
		return out # Return the parsed arguments

	def isHandled(self, toHandle: str = ""):
		"""
		Testings if something is handled

		Args:
			toHandle (str): The thing to check

		Returns:
			bool: If it's handled or not, default False
		"""
		toHandle = toHandle.lower() # Convert handle string to lowercase
		if toHandle == "cmds": return self._isHandledStorage[0] # If it's cmds, return if it's handled
		elif toHandle == "help": return self._isHandledStorage[1] # If it's help, return if it's handled
		elif toHandle == "vars": return self._isHandledStorage[2] # If it's vars, return if it's handled
		elif toHandle == "required vars": return self._isHandledStorage[3] # If it's required vars, return if it's handled
		elif toHandle == "optional vars": return self._isHandledStorage[4] # If it's optional vars, return if it's handled
		elif toHandle == "none": return self._isHandledStorage[5] # If it's none, return if it's handled
		return False # Return False as a default

	def parse(self, args: list = None):
		"""
		Parse a list of arguments and if a command is present then disregard all other arguments

		Args:
			args (list): The list of arguments

		Returns:
			None
		"""
		if not (type(args) is list): return # If the arguments aren't a list, don't do anything
		self._parsedArgs = self._parse(args) # Write the list of arguments to the final list

	def execute(self, ignoreArguemntRequirements: bool = False):
		"""
		Executes the list of parsed arguments
		View source code for understanding of exit codes

		Returns:
			int: Exit code of the execution
		"""
		"""
		Exit Codes:
			2 -> Executed successfully and a found command was executed (Good)
			1 -> Executed successfully and nothing went wrong (Good)
			0 -> Terminated because only a command was run (Good)
		   -1 -> An invalid type was attemped to be used to set a variable's value (Bad)
		   -2 -> Nothing was executed/the parsed arguments did nothing when executed (Bad)
		   -3 -> Not all required arguments were set to values (Bad)
		   -4 -> An error occured when executing a command (Bad)
		   -5 -> An invalid commmand was attempted to be called (Bad)
		   -6 -> Unable to assign a value to an argument that doens't exist (Bad)
		"""
		parsed = lambda index: self._parsedArgs[index] # Gets the parsed argument at an index
		handler = lambda index: self._handler[index] # Gets the handler by an index
		argData = lambda index: parsed(index) # Gets an arguments data
		def getHandlerCmd(cmd: str = ""):
			"""
			Gets a command from the handler

			Args:
				cmd (str): The command

			Returns:
				function: Returns the function to call or None if the command wasn't found
			"""
			cmds = handler("cmds") # Get the dictionary of commands from handler
			if cmd is None: return None # If the command is None, then return None
			if type(cmds) is dict and cmd in cmds: return cmds[cmd] # If cmds is a dictionary and the command is in cmds, then return the function/lambda
			return None # If cmds wasn't a dictionary or cmd wasn't in cmds, then return None

		def doesVariableExist(var: str = ""):
			"""
			Checks if a variable exists by string

			Args:
				var (str): The variable's name

			Returns:
				bool: If the variable exists or not
			"""
			for _var in self._vars["all"].items(): # Loop through all variables list as _var
				if _var[0] == var: return True # If the name of the varaible and the passed name match, then return True
			return False # Variable wasn't found, return False

		def allNotSetVars():
			"""
			Gets a list of all of the required variables that haven't been set

			Returns:
				list: A list of all not set required variables names and execpected type(s)
			"""
			args = [] # List of unset variables
			for var in self._vars["required"].items(): # Loop through all required variables as var
				if var[1][3] == False: # If the variable hasn't been set
					name = var[0] # Get the variables name
					types = self._resolveTypeString(var[1][0]) # Resolve all types
					args.append((name, types)) # Add the type to the list of arguments
			return args # Return the list of variables' names and types

		def areAllRequiredArgsSet():
			"""
			Gets if all of the required arguments were set

			Returns:
				bool: If all of the required arguments were set
			"""
			return len(allNotSetVars()) == 0 # Return True if the number of not set arguments is 0, else False

		pairIndex = 0 # Current index of parsed list
		remaining = lambda: len(self._parsedArgs) - pairIndex # Gets the number of parsed arguments left to be executed
		if remaining() == 0: # If there aren't any generated arguments
			if self._doLog: handler("none")() # Call the none function/lambda
			return -2 # Return -2 as no work will be done
		cmdToExecute = None
		while pairIndex < len(self._parsedArgs): # Loop from 0 to the number of parsed arguments - 1
			argT, argV = argData(pairIndex) # Argument type and value
			if argT == "cmd": # Command argument was found
				cmd = getHandlerCmd(argV)
				if type(cmd) == dict: # It's a cmd
					if pairIndex == 0 and remaining() == 1: # If it's the first index, there is only 1 remaining to be parsed
						try: # Catch errors
							cmd["invoke"]() # Execute handler for command
							return 0
						except: # Error was thrown=
							return -4
					else: # Command was found but it isn't the only token to evalutate
						cmdToExecute = cmd["invoke"] # Set it as a command to execute once all tokens have been executed
						pairIndex += 1 # Skip over 1 index
				elif self._doLog:
					print("Invalid argument \"--" + argV + "\", use --help to see a list of commands") # Print invalid argument message as the command doesn't exist if logging is enabled
					return -5
			elif remaining() >= 2 and argT == "var": # If the remaining parsed is greater than or equal to 2 and the variable of the current index is a variable
				if doesVariableExist(argV):
					tmpT, tmpV = argData(pairIndex + 1)
					if self._isValidValueFor(0, argV, tmpT): # If a proper value being used to set the variable
						self._vars["all"][argV][1] = tmpV # Set the variable's value to be the new value
						self._vars["all"][argV][3] = True # Set that the variable has been changed
						pairIndex += 2 # Skip over 2 indexes
						continue # Goto next element
					else:
						if self._doLog: print("Invalid value type for variable " + argV + ",\nexpected " + self._vars["all"][argV][0] + " but got " + tmpT) # Print that an invalid variable type was used if logging is enabled
						return -1 # Return -1 as the executing stopped because an improper value was attempted to be used to change the variable's value
				else:
					if self._doLog: print("Unknown variable \"", argV, '"', sep="")
					return -6
			elif pairIndex == 0: # If the index is still at 0
				if self._doLog: handler("none")() # Call none function/lambda
				return -2 # Return -2 as nothing was executed
			else:
				break
		if not ignoreArguemntRequirements and not areAllRequiredArgsSet(): # If argument requirements shouldn't be ignored and not all required arguments have been set
			if self._doLog: # If logging is enabled
				print("Not all required value have been set!\nThe following values to be set:") # Print the not all of the required arguments have been set
				for arg in allNotSetVars(): # Loop through all the unset variables' names and type(s)
					print('\t', arg[0], "\t->\t", arg[1], sep = "") # Print out variable's name and type(s)
			return -3 # Return -3 as not all required variables were set
		if cmdToExecute is not None: # There is a command to execute
			try: # Catch errors
				cmdToExecute() # Call command
				return 2 # Command executed successfully
			except: # If error is thrown
				return -4 # An error was thrown
		return 1 # Return 1 as the executing didn't run into any problems

	def readVariable(self, var: str = ""):
		"""
		Reads a value, required or optional

		Args:
			var (str): The variable to read

		Returns:
			obj: The varaibles value
		"""
		if not (var in self._vars["all"]): return None # If the variable isn't in the all variables list, then return None
		else: return self._vars["all"][var][1] # Return the value of the varaible if it exists

	def wasVariableSet(self, var: str = ""):
		"""
		Determines if an optional variable was set or not, or even exists

		View source code for understanding of the determined codes

		Args:
			var (str): Possible variable name

		Returns:
			int: The determined code
		"""
		"""
		Determined Codes:
			1 -> Variable exists and was set to something (Good)
			0 -> Variable exists but wasn't set (Good)
		   -1 -> Variable doesn't exist (Bad)
		"""
		if var in self._vars["all"]: # If the variable is in the list of all variables
			if self._vars["all"][var][3]: return 1 # If the variable has been set, return 1
			else: return 0 # If the variable hasn't been set, return 0
		else: return -1 # If the variable doesn't exist, return -1

	def writeVariable(self, var: str = "", value: object = None):
		"""
		Allows for set setting of a variable by name

		View source code for understanding write codes

		Args:
			var (str): The name of the variable
			value (object): The value to set to the variable to

		Returns:
			int: The write code
		"""
		"""
		Write Codes:
			0 -> Variable exists and was written to sucessfully
		   -1 -> Variable exists but an invalid type was attempt to be used to set it to
		   -2 -> Variable doesn't exist
		"""
		if self.wasVariableSet(var) >= 0: # If the variable exists
			if self._isValidValueFor(1, var, value): # If value is a valid type to set the variable's value to
				self._vars["all"][var][1] = value # Set the variables value
				return 0 # Return 0 as everything worked
			else: return -1 # Return -1 as an invalid type was used
		else: return -2 # Return -2 as the variable doesn't exist
