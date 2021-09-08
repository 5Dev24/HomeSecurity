from os import access, R_OK, W_OK, X_OK, makedirs, open as fdesk, remove
from os.path import abspath, isfile, isdir, sep, dirname
from hashlib import sha256
from typing import AnyStr, BinaryIO, Dict, IO, Callable, List, Any, Type, Tuple, TypeVar, Union
import inspect, re, pathlib

T = TypeVar("T")

def get_file_access(action: str) -> str:
	"""
	Returns the correct open mode for an action
	"""

	if isinstance(action, str):
		action = action.lower()
		if action in ("override", "overwrite", "write"): return "bw+"
		elif action == "append": return "ba"
		elif action == "read": return "br"

def get_file_perms(filepath: str) -> int:
	"""
	Returns the file permissions of a file (from root's perspective)
	"""

	return 4 * access(filepath, R_OK) + 2 * access(filepath, W_OK) + access(filepath, X_OK)

class EasyFile:
	"""
	A simplified way to work with files
	"""

	def __init__(self, filepath: str, should_create: bool = False, force_extension: bool = True):
		if force_extension and not filepath.endswith(".homesec"): filepath += ".homesec"
		self.filepath = abspath(filepath)

		if not self.exists:
			if should_create:
				if not FileUtil.does_folder_exist(self.parent_directory):
					makedirs(self.parent_directory, 0o700, exist_ok = True)

				with open(self.filepath, "w", opener = lambda path, flags: fdesk(path, flags, 0x700)):
					pass
			else:
				raise FileNotFoundError(f"{self.filepath} was expected to exist")

		assert self.exists, f"{self.filepath} didn't point to a file"

	@property
	def name(self) -> str: return self.filepath.split(sep)[::-1][0]

	@property
	def parent_directory(self) -> str: return dirname(self.filepath)

	@property
	def perms(self) -> int: return get_file_perms(self.filepath)

	@property
	def exists(self) -> bool: return FileUtil.does_file_exist(self.filepath)

	@property
	def can_read(self) -> bool: return access(self.filepath, R_OK)

	@property
	def can_write(self) -> bool: return access(self.filepath, W_OK)

	@property
	def can_append(self) -> bool: self.can_write

	def delete(self):
		return FileUtil.delete_file(self.filepath)

	def shred(self): return self.delete() # Cooler name

	def get_stream(self, action: str, callback: Callable[[BinaryIO], T]) -> T:
		access_action = get_file_access(action)

		if access_action:
			action = action.lower()

			if action in ("write", "append") and not self.can_write:
				raise PermissionError(f"Cannot {action} the file")
			elif action in ("read",) and not self.can_read:
				raise PermissionError("Cannot read the file")

			argspec = inspect.getfullargspec(callback)
			if len(argspec.args) == 1:
				if argspec.args[0] in argspec.annotations:
					if argspec.annotations[argspec.args[0]] in (BinaryIO, IO):
						with open(self.filepath, access_action) as file_access:
							return callback(file_access)
				else:
					with open(self.filepath, access_action) as file_access:
						return callback(file_access)

class FileDecodeError(Exception): pass

class FileEncodeError(Exception): pass

class EasyFileData: pass

class EasyFileFormatMeta(type):

	def __new__(cls, name: str, bases: Tuple[Type], namespace: Dict[str, Any], **kwargs):
		is_manager = "manager" in kwargs and kwargs["manager"]
		namespace["manager"] = is_manager

		if is_manager:
			namespace["children"] = {}
			return super().__new__(cls, name, bases, namespace)

		if "data" not in kwargs or not isinstance(kwargs["data"], type) or EasyFileData not in kwargs["data"].__bases__:
			raise ValueError("Need a file data data to be provided")

		for base in bases:
			if "manager" in dir(base) and base.manager:
				instance = super().__new__(cls, name, bases, namespace)
				base.children[name] = (instance, kwargs["data"])
				return instance

		raise ValueError("Format must inherit from a manager, try EasyFileFormat")

class EasyFileFormat(metaclass = EasyFileFormatMeta, manager = True):

	def from_file(self, file: EasyFile) -> EasyFileData:
		"""
		Loads data from the file provided and attempts to
		decode the data into an EasyFileData object or an
		object that has inheritted from EasyFileData.

		Classes that override should put a type specification
		for the return value. If data cannot be decoded,
		FileDecodeError should be raised.
		"""
		raise NotImplementedError()

	def save_to(self, file: EasyFile, data: EasyFileData) -> bool:
		"""
		Save the data from an EasyFileData object to the file
		provided. The boolean returned is if the save was
		successful or not.

		If the data cannot be saved and it is unsafe for the
		program to continue to function without safe saving,
		FileEncodeError should be raised.
		"""
		raise NotImplementedError()

class LogFileData(EasyFileData):
	"""
	Log file's data

	All logs are stored in a list of logger.LogData as the property logs

	This property shouldn't be directly modified, please use add_log as
	logs should never be deleted.
	"""

	def __init__(self):
		self.logs: List[logger.LogData] = []

	def add_log(self, log: "logger.LogData"):
		self.logs.append(log)

	def get_head(self, count: int):
		return self.logs[:count]

	def get_tail(self, count: int):
		return self.logs[-count:]

class LogFileFormat(EasyFileFormat, data = LogFileData):
	"""
	Log file format
	"""

	def from_file(self, file: EasyFile) -> LogFileData:
		data = LogFileData()

		def read(stream: BinaryIO):
			line_num = 1
			for line in stream.readlines(): # May change to enumerate
				line = line.rstrip(b"\n").decode("utf-8")

				match: re.Match[AnyStr] = re.match(r"\d{2}/\d{2}/\d{4} :: \d{2}:\d{2}:\d{2} \[\w+\]", line)
				if match:
					date = re.search(r"\d{2}/\d{2}/\d{4}", line).group(0)
					time = re.search(r"\d{2}:\d{2}:\d{2}", line).group(0)
					logtype = re.search(r"\[\w+\]", line).group(0)[1:-1]
					info = line[match.end(0) + 1:].encode("utf-8").decode("unicode_escape")

					logdata: logger.LogData = logger.Log(logtype, info, False, False)
					logdata.timestamp.date = date
					logdata.timestamp.time = time
					data.add_log(logdata)

					line_num += 1
				else:
					raise FileDecodeError(f"One or more log entries were invalid (First line fail: {line_num})")

		file.get_stream("read", read)
		return data

	def save_to(self, file: EasyFile, data: LogFileData) -> bool:
		def write(stream: BinaryIO):
			for log in data.logs:
				stream.write(repr(log).encode("utf-8") + b"\n")

		file.get_stream("write", write)
		return True

class ConfigFileData(EasyFileData):
	"""
	A "config" file's data

	Class works like a mutable namedtuple (so a namedlist/dictionary)

	The data property is a dictionary that can be modified directly
	if you're unsure how to read/write data.
	"""

	def __init__(self):
		self.data: Dict[str, Any] = {}

	def __getattribute__(self, name: str) -> Any:
		if name == "data":
			return object.__getattribute__(self, "data")

		if name in self.data:
			return self.data[name]

	def __setattr__(self, name: str, value: Any) -> None:
		if name == "data":
			return object.__setattr__(self, "data", value)

		self.data[name] = value

class ConfigFileFormat(EasyFileFormat, data = ConfigFileData):
	"""
	Config file format
	"""

	def from_file(self, file: EasyFile) -> ConfigFileData:
		data = ConfigFileData()

		def read(stream: BinaryIO):
			while True:
				try:
					key_length_data = stream.read(2)
					if len(key_length_data) != 2:
						if not len(key_length_data): # EOF at the right time
							break

						raise FileDecodeError("EOF reached at an invalid point in config file (1)")

					key_length = from_base256(key_length_data)
					key_value = stream.read(key_length)

					if len(key_value) != key_length:
						raise FileDecodeError("EOF reached at an invalid point in config file (2)")

					key_value = key_value.decode("unicode_escape")

					value_length_data = stream.read(2)

					if len(value_length_data) != 2:
						raise FileDecodeError("EOF reached at an invalid point in config file (3)")

					value_length = from_base256(value_length_data)
					value_value = stream.read(value_length)

					if len(value_value) != value_length:
						raise FileDecodeError("EOF reached at an invalid point in config file (4)")

					value_value = value_value.decode("unicode_escape")

					data.data[key_value] = value_value
				except UnicodeDecodeError:
					raise FileDecodeError("Invalid character, cannot decode config file (5)")

		file.get_stream("read", read)
		return data

	def save_to(self, file: EasyFile, data: ConfigFileData) -> bool:
		def write(stream: BinaryIO):
			for key, value in data.data.items():
				key = repr(key)[1:-1].encode("utf-8")
				value = repr(value)[1:-1].encode("utf-8")

				key_length = len(key)
				value_length = len(value)

				stream.write(bytes([key_length // 256, key_length % 256]))
				stream.write(key)
				stream.write(bytes([value_length // 256, value_length % 256]))
				stream.write(value)

		file.get_stream("write", write)
		return True

class SessionFileData(EasyFileData):
	"""
	Unserialized data of a session
	"""

	def __init__(self, expires: int = None, step: int = None, past_random: bytes = None, present_random: bytes = None, \
		future_random: bytes = None, shared_aes: bytes = None, server_rsa_public: bytes = None, server_rsa_private: bytes = None, \
		client_rsa_public: bytes = None, client_rsa_private: bytes = None):

		self.expires = expires
		self.step = step
		self.past_random = past_random
		self.present_random = present_random
		self.future_random = future_random
		self.shared_aes = shared_aes
		self.server_rsa_public = server_rsa_public
		self.server_rsa_private = server_rsa_private
		self.client_rsa_public = client_rsa_public
		self.client_rsa_private = client_rsa_private

class SessionFileFormat(EasyFileFormat, data = SessionFileData):
	"""
	Session file format
	"""

	SHARED_AES_BITMASK         = 0b00001
	SERVER_RSA_PUBLIC_BITMASK  = 0b00010
	SERVER_RSA_PRIVATE_BITMASK = 0b00100
	CLIENT_RSA_PUBLIC_BITMASK  = 0b01000
	CLIENT_RSA_PRIVATE_BITMASK = 0b10000

	def generate_key_byte(data: SessionFileData) -> bytes:
		value = 0b00000

		if data.shared_aes:
			value |= SessionFileFormat.SHARED_AES_BITMASK
		if data.server_rsa_public:
			value |= SessionFileFormat.SERVER_RSA_PUBLIC_BITMASK
		if data.server_rsa_private:
			value |= SessionFileFormat.SERVER_RSA_PRIVATE_BITMASK
		if data.client_rsa_public:
			value |= SessionFileFormat.CLIENT_RSA_PUBLIC_BITMASK
		if data.client_rsa_private:
			value |= SessionFileFormat.CLIENT_RSA_PRIVATE_BITMASK

		return bytes([value])

	def has(key_byte: int, bitmask: int):
		return (key_byte & bitmask) == bitmask

	def from_file(self, file: EasyFile) -> SessionFileData:
		data = SessionFileData()

		def read(stream: BinaryIO):
			expires_length_bytes = stream.read(4)
			if len(expires_length_bytes) != 4:
				raise FileDecodeError("EOF reached at an invalid point in session file (1)")

			expires_length = from_base256(expires_length_bytes)
			expires_bytes = stream.read(expires_length)

			if len(expires_bytes) != expires_length:
				raise FileDecodeError("EOF reached at an invalid point in session file (2)")

			data.expires = from_base256(expires_bytes)
			del expires_length_bytes, expires_length, expires_bytes

			step_length_bytes = stream.read(2)
			if len(step_length_bytes) != 2:
				raise FileDecodeError("EOF reached at an invalid point in session file (3)")

			step_length = from_base256(step_length_bytes)
			step_bytes = stream.read(step_length)

			if len(step_bytes) != step_length:
				raise FileDecodeError("EOF reached at an invalid point in session file (4)")

			data.step = from_base256(step_bytes)
			del step_length_bytes, step_length, step_bytes

			past_random = stream.read(32)

			if len(past_random) != 32:
				raise FileDecodeError("EOF reached at an invalid point in session file (5)")

			data.past_random = past_random
			del past_random

			present_random = stream.read(32)

			if len(present_random) != 32:
				raise FileDecodeError("EOF reached at an invalid point in session file (6)")

			data.present_random = present_random
			del present_random

			future_random = stream.read(32)

			if len(future_random) != 32:
				raise FileDecodeError("EOF reached at an invalid point in session file (7)")

			data.future_random = future_random
			del future_random

			key_byte = stream.read(1)

			if len(key_byte) != 1:
				raise FileDecodeError("EOF reached at an invalid point in session file (8)")

			if SessionFileFormat.has(key_byte, SessionFileFormat.SHARED_AES_BITMASK):
				shared_aes = stream.read(32)

				if len(shared_aes) != 32:
					raise FileDecodeError("EOF reached at an invalid point in session file (9)")

				data.shared_aes = shared_aes
				del shared_aes

			if SessionFileFormat.has(key_byte, SessionFileFormat.SERVER_RSA_PUBLIC_BITMASK):
				server_rsa_public_length_bytes = stream.read(2)

				if len(server_rsa_public_length_bytes) != 2:
					raise FileDecodeError("EOF reached at an invalid point in session file (10)")

				server_rsa_public_length = from_base256(server_rsa_public_length_bytes)
				server_rsa_public = stream.read(server_rsa_public_length)

				if len(server_rsa_public) != server_rsa_public_length:
					raise FileDecodeError("EOF reached at an invalid point in session file (11)")

				data.server_rsa_public = server_rsa_public
				del server_rsa_public_length_bytes, server_rsa_public_length, server_rsa_public

			if SessionFileFormat.has(key_byte, SessionFileFormat.SERVER_RSA_PRIVATE_BITMASK):
				server_rsa_private_length_bytes = stream.read(2)

				if len(server_rsa_public_length_bytes) != 2:
					raise FileDecodeError("EOF reached at an invalid point in session file (12)")

				server_rsa_private_length = from_base256(server_rsa_private_length_bytes)
				server_rsa_private = stream.read(server_rsa_private_length)

				if len(server_rsa_private) != server_rsa_private_length:
					raise FileDecodeError("EOF reached at an invalid point in session file (13)")

				data.server_rsa_private = server_rsa_private
				del server_rsa_private_length_bytes, server_rsa_private_length, server_rsa_private

			if SessionFileFormat.has(key_byte, SessionFileFormat.CLIENT_RSA_PUBLIC_BITMASK):
				client_rsa_public_length_bytes = stream.read(2)

				if len(client_rsa_public_length_bytes) != 2:
					raise FileDecodeError("EOF reached at an invalid point in session file (14)")

				client_rsa_public_length = from_base256(client_rsa_public_length_bytes)
				client_rsa_public = stream.read(client_rsa_public_length)

				if len(client_rsa_public) != client_rsa_public_length:
					raise FileDecodeError("EOF reached at an invalid point in session file (15)")

				data.client_rsa_public = client_rsa_public
				del client_rsa_public_length_bytes, client_rsa_public_length, client_rsa_public

			if SessionFileFormat.has(key_byte, SessionFileFormat.CLIENT_RSA_PRIVATE_BITMASK):
				client_rsa_private_length_bytes = stream.read(2)

				if len(client_rsa_public_length_bytes) != 2:
					raise FileDecodeError("EOF reached at an invalid point in session file (16)")

				client_rsa_private_length = from_base256(client_rsa_private_length_bytes)
				client_rsa_private = stream.read(client_rsa_private_length)

				if len(client_rsa_private) != client_rsa_private_length:
					raise FileDecodeError("EOF reached at an invalid point in session file (17)")

				data.client_rsa_private = client_rsa_private
				del client_rsa_private_length_bytes, client_rsa_private_length, client_rsa_private

		file.get_stream("read", read)
		return data

	def save_to(self, file: EasyFile, data: SessionFileData) -> bool:
		def write(stream: BinaryIO):
			stream.write(add_length_data(to_base256(data.expires), 4, 4))
			stream.write(add_length_data(to_base256(data.step), 2, 2))
			stream.write(data.past_random)
			stream.write(data.present_random)
			stream.write(data.future_random)

			stream.write(SessionFileFormat.generate_key_byte(data))
			if data.shared_aes:
				stream.write(data.shared_aes)
			if data.server_rsa_public:
				stream.write(add_length_data(data.server_rsa_public, 2, 2))
			if data.server_rsa_private:
				stream.write(add_length_data(data.server_rsa_private, 2, 2))
			if data.client_rsa_public:
				stream.write(add_length_data(data.client_rsa_public, 2, 2))
			if data.client_rsa_private:
				stream.write(add_length_data(data.client_rsa_private, 2, 2))

		file.get_stream("write", write)
		return True

class FileUtil:

	@staticmethod
	def root() -> str: return str(pathlib.Path(__file__).parent.absolute().resolve())

	@staticmethod
	def checksum(data: Union[List[bytes], bytes]) -> bytes:
		if type(data) == list:
			return FileUtil.checksum(b"\n".join(data))
		elif type(data) == bytes:
			return sha256(data).digest()

	@staticmethod
	def does_file_exist(filepath: str) -> bool:
		return isfile(filepath)

	@staticmethod
	def does_folder_exist(folderpath: str) -> bool:
		return isdir(folderpath)

	@staticmethod
	def delete_file(filepath: str) -> bool:
		if FileUtil.does_file_exist(filepath):
			remove(filepath)

		return not FileUtil.does_file_exist(filepath)

	@staticmethod
	def write_lines(file: EasyFile, lines: List[bytes]) -> None:
		def write(stream: BinaryIO):
			stream.write(b"\n".join(lines))

		file.get_stream("write", write)

	@staticmethod
	def append_lines(file: EasyFile, lines: List[bytes]) -> None:
		def write(stream: BinaryIO):
			stream.write(b"\n".join(lines))

		file.get_stream("append", write)

	@staticmethod
	def extend_lines(file: EasyFile, lines_out: List[bytes]) -> None:
		def read(stream: BinaryIO):
			lines_out.extend(stream.readlines())

		file.get_stream("read", read)

	@staticmethod
	def read_lines(file: EasyFile) -> List[bytes]:
		lines: List[bytes] = []
		def read(stream: BinaryIO):
			lines.extend(stream.readlines())

		file.get_stream("read", read)
		return lines

import logger
from networking.packet import to_base256, from_base256, add_length_data