import ctypes
# Can't use multiprocessing as I/O bound, few active connections and background threads
from threading import Thread, current_thread, main_thread, _active, RLock
from typing import Callable, Dict, List, Optional, Tuple
from types import FunctionType

def lock_main_thread() -> None:
	if current_thread() != main_thread():
		return

	try:
		while len(EasyThread.__threads__):
			if EasyThread.__stop__: return

			for thread in EasyThread.__threads__:
				if EasyThread.__stop__: return

				thread.join(30, main_joining = True)
	except BaseException as e:
		failure.die(failure.Threading.Exception_Raised, "An error was raised while main was joining active threads", True, e)
	finally:
		EasyThread.kill_threads()
		EasyThread.__stop__ = True

def is_main_alive() -> bool:
	if main_thread().is_alive():
		return True
	
	EasyThread.kill_threads()
	return False

class EasyThreadException(Exception): pass # Base class for EasyThread exceptions

class EasyThreadClose(EasyThreadException): pass # Thread is forcefully closed

class EasyThreadMainDied(EasyThreadException): pass # Main thread died

class EasyThread:

	__threads__: List["EasyThread"] = []
	__lock__ = RLock()
	__stop__ = False

	@staticmethod
	def kill_threads():
		if not EasyThread.__stop__:
			EasyThread.__stop__ = True
			for thread in EasyThread.__threads__:
				thread.kill()

	# `catch` should return True if they want the exception to be suppressed
	def __init__(self, target: FunctionType, loop: Optional[bool] = False, catch: Callable[[Exception], bool] = None, *args, **kwargs):
		self.__internal_thread = Thread(target = self.__internal_target, daemon = True)
		self.__target = target
		self.__catch = catch
		self.__args = tuple() if args is None else args
		self.__kwargs = dict() if kwargs is None else kwargs
		self.__should_loop = loop
		self.__started = False
		self.__running = False
		self.__internal_lock = RLock()

	@property
	def args(self) -> Tuple: return tuple(self.__args)

	@property
	def kwargs(self) -> Dict: return dict(self.__kwargs)

	@property
	def does_loops(self) -> bool: return self.__should_loop

	@property
	def is_running(self) -> bool: return self.__running

	@property
	def is_alive(self) -> bool: return self.__running

	@property
	def has_started(self) -> bool: return self.__started

	@property
	def is_registered(self) -> bool: return self in EasyThread.__threads__

	@property
	def safe(self) -> bool: return is_main_alive() and self.__running \
		and self.is_registered and not EasyThread.__stop__ \
		and self.__target is not None and self.__args is not None \
		and self.__kwargs is not None

	def start(self) -> bool:
		with self.__internal_lock:
			if self.__running or self.__started:
				return False

			with EasyThread.__lock__:
				self.__started = True
				EasyThread.__threads__.append(self)
				self.__running = True
				self.__internal_thread.start()
				return True

	def kill(self) -> None:
		if not self.__running: return
		self.__del__()
		if self.__internal_thread is not None and self.__internal_thread.is_alive():
			for thread_id, thread_object in _active.items():
				if self.__internal_thread is thread_object:
					exception_object = ctypes.py_object(EasyThreadClose if is_main_alive() else EasyThreadMainDied)

					response = ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, exception_object)
					if response > 1:
						ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, 0)
						raise SystemError("PyThreadState_SetAsyncExc failed")

		self.__running = False
		self.__target = self.__args = self.__kwargs = None

	def __del__(self):
		if self.is_registered:
			EasyThread.__threads__.remove(self)

	def __internal_target(self):
		try:
			if self.__should_loop:
				while self.safe:
					try:
						self.__target(*self.__args, **self.__kwargs)

					except Exception as e:
						if not isinstance(e, EasyThreadException):
							if self.__catch and callable(self.__catch):
								try:
									if self.__catch(e):
										return
								except Exception as e2:
									if not isinstance(e2, EasyThreadException):
										failure.notice(failure.Threading.Exception_Raised, f"{self.__internal_thread} raised {e2.__class__.__name__} while trying to handle {e.__class__.__name__}", True, e, e2)
										return

							failure.notice(failure.Threading.Exception_Raised, f"{self.__internal_thread} raised {e.__class__.__name__}", True, e)
						raise e

			else: # Single run
				try:
					self.__target(*self.__args, **self.__kwargs)

				except Exception as e:
					if not isinstance(e, EasyThreadException):
						if self.__catch and callable(self.__catch):
							try:
								if self.__catch(e):
									return
							except Exception as e2:
								if not isinstance(e2, EasyThreadException):
									failure.notice(failure.Threading.Exception_Raised, f"{self.__internal_thread} raised {e2.__class__.__name__} while trying to handle {e.__class__.__name__}", True, e, e2)
									return

						failure.notice(failure.Threading.Exception_Raised, f"{self.__internal_thread} raised {e.__class__.__name__}", True, e)
					raise e

		except Exception as e:
			if isinstance(e, EasyThreadClose):
				failure.notice(failure.Threading.Killed, f"{self.__internal_thread} died to {e.__class__.__name__}", True, e)

			elif self.__catch and callable(self.__catch):
				try:
					if self.__catch(e):
						return
				except Exception as e2:
					if not isinstance(e2, EasyThreadException):
						failure.notice(failure.Threading.Exception_Raised, f"{self.__internal_thread} raised {e2.__class__.__name__} while trying to handle {e.__class__.__name__}", True, e, e2)
						return

				raise e				

		finally:
			self.kill()

	def join(self, timeout: int = 5, main_joining: bool = False):
		if current_thread() == main_thread() and not main_joining:
			raise RuntimeError("Main cannot join a thread without explicitly stating that the main is meant to join a thread")

		if isinstance(timeout, int):
			if timeout > 300: timeout = 300
			elif timeout < 0: timeout = 0

			self.__internal_thread.join(timeout)

import failure