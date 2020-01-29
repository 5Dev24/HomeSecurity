import traceback
from threading import Thread, current_thread, main_thread
from ..codes import LogCode, Threading

class SimpleThread:
	"""
	My own implementation of threading made simple

	Still uses a Thread object for underlying threading but has better control

	Adds for looping threads to continuously call the target function
	"""

	def __init__(self, target = None, loop: bool = False, args = tuple(), kwargs = {}):
		"""
		Init

		Args:
			target (function): The function that will be called by the thread
			loop (bool): Should the function be continuously called
			args (tuple): Arguments to pass to the function
			kwargs (dict): Keyword arguments to pass to the function

		Attributes:
			_internalThread (Thread): The internal thread using to call the target thread
			_target (function): Function to call in internal thread
			_args (tuple, optional): Arguments to pass to target, default: empty tuple
			_kwargs (dict): Keyword arguments to pass to target, default: empty dictionary
			_loop (bool): If the thread should loop
			_running (bool): If the thread is running currently
		"""
		self._internalThread = Thread(target=self._internal) # Create internal thread, does actual threading
		self._target = target # Save target
		self._args = args # Save args
		self._kwargs = {} if kwargs is None else kwargs # If kwargs is None then added empty kwargs, else save kwargs
		self._loop = loop # Save whether function should loop
		self._running = False # Thread isn't running yet

	def stop(self):
		"""
		Stop the thread (change internal variable)

		Returns:
			SimpleThread: self
		"""
		self._running = False # Set that thread isn't running
		return self # Return self

	def _internal(self):
		"""
		Internal threading method to call target function

		Returns:
			None
		"""
		try: # Try-except to always delete isntance of the internal thread, args, and kwargs
			if self._loop: # If thread should loop
				while self._running: # While the thread is running
					try: self._target(*self._args, **self._kwargs) # Try to call the function with the args and kwargs
					except Exception: # Catch all exceptions (except exiting exceptions)
						LogCode(Threading.LOOPING_THREAD_ERROR, f"Traceback:\n{traceback.format_exc()}")
						break # Break from loop
			else: # If thread shouldn't loop
				try: self._target(*self._args, **self._kwargs) # Call function with args and kwargs
				except Exception: LogCode(Threading.SINGLE_THREAD_ERROR, f"Traceback:\n{traceback.format_exc()}")
		finally: # Always execute
			self.stop() # Mark thread as stopped
			del self._internalThread, self._args, self._kwargs # Destroy instances of the internal thread, args, and kwargs

	def start(self):
		"""
		Start the internal thread

		Returns:
			SimpleThread: self
		"""
		if self._running: return self # If thread is already running, return self
		self._running = True # Set that thread is running
		self._internalThread.start() # Start internal thread
		return self # Return self

	def join(self, timeout: int = 5):
		"""
		Allows for thread to join internal thread

		Should not and cannot be called form main thread

		Args:
			timeout (int, optional): Number of seconds to wait before exiting thread join, default 5

		Returns:
			None
		"""
		if current_thread() is main_thread(): # If function has been called from main thread
			LogCode(Threading.JOIN_FROM_MAIN)
			return # Exit function
		self._internalThread.join(timeout) # Wait for thread to terminal but added timeout