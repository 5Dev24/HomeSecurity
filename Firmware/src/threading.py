import traceback, ctypes
from threading import Thread, current_thread, main_thread, _active
from . import codes as _codes, logging as _logging

def HoldMain():
	try:
		while len(SimpleThread.__threads__) > 0:
			for thread in SimpleThread.__threads__:
				_logging.Log(_logging.LogType.Debug, "Joining thread invoking " + thread._target.__name__).post()
				thread.join(5, True)
		_logging.Log(_logging.LogType.Debug, "No active threads found").post()
	except BaseException as e:
		_logging.Log(_logging.LogType.Debug, "Exception of type " + type(e).__name__ + " was raised").post()
	finally:
		SimpleThread.__stop__ = True

def MainDead():
	dead = not main_thread().is_alive()
	if dead:
		KillAll()
	return dead

def KillAll():
	try:
		while len(SimpleThread.__threads__) > 0:
			for thread in SimpleThread.__threads__:
				thread.stop(True)
	except SimpleThreadException:
		return

# A base class to catch all exceptions thrown naturally
class SimpleThreadException(Exception): pass

# An exception for when a thread is forcefully closed
class SimpleClose(SimpleThreadException): pass

# An exception for when the main thread dies and the thread needs to die too
class MainClose(SimpleThreadException): pass

class SimpleThread:

	__threads__ = []
	__stop__ = False

	@staticmethod
	def ReleaseThreads():
		for thread in SimpleThread.__threads__:
			thread.stop()
		SimpleThread.__stop__ = True

	def __init__(self, target = None, loop: bool = False, args = tuple(), kwargs = {}):
		self._internalThread = Thread(target=self._internal)
		self._target = target
		self._args = args
		self._kwargs = {} if kwargs is None else kwargs
		self._loop = loop
		self._running = False

	def stop(self, main_dead: bool = False):
		if not self._running: return
		self.__del__()
		try:
			self._internalThread
			self._running
		except: return self
		if self._internalThread is not None:
			# Credit to liuw (https://gist.github.com/liuw/2407154)
			for thread_id, thread_object in _active.items():
				if self._internalThread is thread_object:
					obj = ctypes.py_object(SimpleClose)
					if main_dead:
						obj = ctypes.py_object(MainClose)

					response = ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, obj)
					if response > 1:
						ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, 0)
						raise SystemError("PyThreadState_SetAsyncExc failed")
		self._running = False
		return self

	def __del__(self):
		if self.is_registered:
			SimpleThread.__threads__.remove(self)

	@property
	def is_registered(self):
		return self in SimpleThread.__threads__

	@property
	def _save(self):
		return not MainDead() and self._running and self.is_registered and not SimpleThread.__stop__

	def _internal(self):
		try:
			if self._loop:
				while self._save:
					try: self._target(*self._args, **self._kwargs)
					except Exception as e:
						if type(e) != SimpleClose and type(e) != MainClose:
							_codes.LogCode(_codes.Threading.LOOPING_THREAD_ERROR, f"({self._internalThread}) {e.__class__.__name__} Traceback:\n{traceback.format_exc()}")
						break
			elif self._save:
				try: self._target(*self._args, **self._kwargs)
				except Exception as e:
					if type(e) != SimpleClose and type(e) != MainClose:
						_codes.LogCode(_codes.Threading.SINGLE_THREAD_ERROR, f"({self._internalThread}) {e.__class__.__name__} Traceback:\n{traceback.format_exc()}")
		finally:
			try:
				self.stop()
			except SimpleThreadException: pass
			finally:
				del self._internalThread, self._args, self._kwargs

	def start(self):
		if self._running: return self
		SimpleThread.__threads__.append(self)
		self._running = True
		self._internalThread.start()
		return self

	def join(self, timeout: int = 5, _holdMain: bool = False):
		if current_thread() is main_thread() and not _holdMain:
			_codes.LogCode(_codes.Threading.JOIN_FROM_MAIN)
			return

		if timeout is None or type(timeout) != int: timeout = 5
		elif timeout > 300: timeout = 300
		elif timeout < 0: timeout = 0

		self._internalThread.join(timeout)
