import traceback, ctypes
from threading import Thread, current_thread, main_thread, _active
from . import codes as _codes

def HoldMain():
	while len(SimpleThread.__threads__) > 0:
		for thread in SimpleThread.__threads__:
			thread.join(5, True)
	SimpleThread.__stop__ = True

class SimpleClose(Exception): pass

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
		SimpleThread.__threads__.append(self)

	def stop(self):
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
					response = ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, ctypes.py_object(SimpleClose))
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

	def _internal(self):
		try:
			if self._loop:
				while self._running and self.is_registered and not SimpleThread.__stop__:
					try: self._target(*self._args, **self._kwargs)
					except Exception as e:
						if type(e) != SimpleClose:
							_codes.LogCode(_codes.Threading.LOOPING_THREAD_ERROR, f"({self._internalThread}) {e.__class__.__name__} Traceback:\n{traceback.format_exc()}")
						break
			elif self._running and self.is_registered and not SimpleThread.__stop__:
				try: self._target(*self._args, **self._kwargs)
				except Exception as e:
					if type(e) != SimpleClose:
						_codes.LogCode(_codes.Threading.SINGLE_THREAD_ERROR, f"({self._internalThread}) {e.__class__.__name__} Traceback:\n{traceback.format_exc()}")
		finally:
			try:
				self.stop()
			except SimpleClose: pass
			finally:
				del self._internalThread, self._args, self._kwargs

	def start(self):
		if self._running: return self
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
