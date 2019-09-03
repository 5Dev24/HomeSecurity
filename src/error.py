import sys
import time

def close(pause: bool = False, msg: str = None):
	"""
	Exists the program with a code of 0, prints a message and that it exited with code 0, and could pause before closing

	:param pause bool: To pause before closing or not
	:param msg str: The message to print

	:returns void: Doesn't as program closes
	"""
	if msg is None: msg = "No message supplied" # If no message was given, set to a default one
	print(msg + "\nTermination with exit code 0") # Print message and that the program terminated with exit code 0
	if pause: input("\nPress [ENTER] to close this program") # If a pause is wanted, pause and wait for [ENTER] to be pressed
	sys.exit(0) # Exit program with exit code 0

def kill(msg: str = None):
	"""
	Kills a program with a code of 1, prints out an error message but may not be seen as there is no pausing, terminal needed

	:param msg str: The message to print

	:returns void: Doesn't as program closes
	"""
	if msg is None: msg = "No message supplied" # If no message was given, set to a default one
	print(msg + "\nTerminating with exit code 1") # Print message and that the program terminated with exit code 1
	sys.exit(1) # Exit program with exit code 1

class Codes:
	"""
	Methods for handling errors

	KILL = Close program and state that an error occured
	CLOSE = Close program but state that it was fine to close
	CONTINUE = Continue running program but log error
	"""

	KILL = -1 # Kill program
	EXIT = 0 # Close program
	CONTINUE = 1 # Continue running programming

class Error:
	"""
	Error handing for all errors in this program
	"""

	def __init__(self, originalError: BaseException = None, method: int = None, additionalInfo: str = None):
		"""
		Init

		:param originalError BaseException: The exception thrown
		:param method int: The method for handling the error
		:param additionalInfo str: Additional information about the error
		"""
		if additionalInfo is None: additionalInfo = "" # If additional info is none, make it an empty string
		self._info = additionalInfo
		if method < Codes.KILL: method = Codes.KILL # Make sure method is within range
		elif method > Codes.CONTINUE: method = Codes.CONTINUE # Make sure method is withing range
		self._method = method
		if originalError is None or not (BaseException in originalError.__class__.__mro__): # The exception was None or wasn't an exception
			Error(TypeError(), self._method, "An Excepton wasn't passed to error handler constructor\n\t\t\t" + self._info).handle() # Close the program, don't pause, and say what happened
		else:
			try:
				self._orgError = [
					originalError.__class__.__mro__[0],
					originalError,
					originalError.strerror
				]
			except AttributeError:
				self._orgError = [
					originalError.__class__.__mro__[0],
					originalError
				]

	def handle(self):
		out = "Error Details:\n\tError Class: " + self._orgError[0].__name__ + ("\n\tError Msg: " + self._orgError[2] if len(self._orgError) > 2 else "") + "\n\tAdditional Information: \n\t\t" + self._info
		if self._method == -1: kill(out)
		elif self._method == 0: close(False, out)
		else: print("An error has occured but the program can sustain this error\n", out, sep = '')