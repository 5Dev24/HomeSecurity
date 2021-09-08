from typing import Dict, List, NamedTuple, Union
from datetime import datetime, timezone
from threading import RLock
import secrets

class SessionManager:

	__instance = None

	@classmethod
	def get_manager(cls) -> "SessionManager":
		if cls.__instance is None:
			cls.__instance = cls.__new__(cls)
			self = cls.__instance

			self.__dead = False

			self.sessions = {}
			self.lock = RLock()
			self.folder_path = io_handles.FileUtil.root() + "/data/sessions/"

		if cls.__instance.__dead:
			dead = type("Dead SessionManager", (object,), {})
			dead.sessions = dead.lock = dead.folder_path = dead.__dead = None
			dead.get_session = dead.make_session = dead.is_session_authenticated = dead.shutdown = lambda *args, **kwargs: None
			return dead

		return cls.__instance

	def __init__(self):
		# For typing
		self.sessions: Dict[bytes, Session]
		self.lock: RLock
		self.folder_path: str

		self.__dead: bool

		raise RuntimeError("Get session manager from SessionManager.get_manager()")

	def get_session(self, session_id: bytes) -> "Session":
		with self.lock:
			if not self.__dead:
				if session_id in self.sessions:
					if not self.sessions[session_id].destroyed:
						return self.sessions[session_id]

				filepath = self.folder_path + ",".join([str(byte) for byte in session_id]) + ".homesec"
				if io_handles.FileUtil.does_file_exist(filepath):
					return Session.session_from_file(io_handles.EasyFile(filepath))

	def make_session(self) -> "Session":
		with self.lock:
			if not self.__dead:
				id = secrets.token_bytes(32)

				while id in self.sessions:
					id = secrets.token_bytes(32)

				session = Session(int(datetime.now(timezone.utc).timestamp()) + 1800, id, 0, bytes([0]) * 32, bytes([0]) * 32, bytes([0]) * 32)
				session.save()

				self.sessions[id] = session

				return session

	def is_session_authenticated(self, session_id: bytes) -> bool:
		with self.lock:
			if not self.__dead:
				session = self.get_session(session_id)

				return session is not None and session.shared_aes is not None and len(session.shared_aes) == 32

		return False

	def shutdown(self) -> None:
		with self.lock:
			if not self.__dead:
				self.__dead = True

				for session in self.sessions.values():
					if not session.destroyed:
						session.save()

				self.sessions = {}

class Session(NamedTuple):
	expires: int # 4 bytes
	id: bytes # 32 bytes
	step: int # 2 bytes
	past_random: bytes # 32 bytes, prior random we generated
	present_random: bytes # 32 bytes, random recieved from other party, they expect it in the next packet
	future_random: bytes # 32 bytes, next expected random we generated

	shared_aes: bytes = None # 32 bytes
	server_rsa_public: bytes = None
	server_rsa_private: bytes = None
	client_rsa_public: bytes = None
	client_rsa_private: bytes = None

	internal_lock = RLock()
	internal_file: "io_handles.EasyFile" = None
	destroyed: bool = False

	@staticmethod
	def session_from_file(file: "io_handles.EasyFile") -> Union["Session", None]:
		mngr = SessionManager.get_manager()

		file_name_splits = file.name.split(",")
		if len(file_name_splits) != 32:
			return None

		id_bytes = []

		for id_part in file_name_splits:
			if id_part.isdigit():
				id_bytes.append(int(id_part))
			else:
				return None

		id = bytes(id_bytes)
		del file_name_splits, id_bytes

		with mngr.lock:
			if id in mngr.sessions:
				return mngr.sessions[id]

			session_data = io_handles.SessionFileFormat().from_file(file)

			session = Session(session_data.expires, id, session_data.step, session_data.past_random, \
				session_data.present_random, session_data.future_random, session_data.shared_aes, session_data.server_rsa_public, \
				session_data.server_rsa_private, session_data.client_rsa_public, session_data.client_rsa_private, file)

			mngr.sessions[id] = session
			return session

	def save(self):
		with self.__internal_lock:
			if self.destroyed:
				return

			if self.internal_file is None:
				self.internal_file = io_handles.EasyFile(self.filepath)

			io_handles.SessionFileFormat().save_to(self.internal_file, io_handles.SessionFileData(self.expires, self.step, \
				self.past_random, self.present_random, self.future_random, self.shared_aes, self.server_rsa_public, \
				self.server_rsa_private, self.client_rsa_public, self.client_rsa_private))

	def destroy(self):
		with self.__internal_lock:
			if not self.destroyed:
				self.destroyed = True

				if io_handles.FileUtil.does_file_exist(self.filepath):
					io_handles.FileUtil.delete_file(self.filepath)

				mngr = SessionManager.get_manager()

				with mngr.lock:
					del mngr.sessions[self.id]

	@property
	def filepath(self) -> str:
		return io_handles.FileUtil.root() + "/data/sessions/" + ",".join([str(byte) for byte in self.id]) + ".homesec"

	@property
	def has_expired(self) -> bool: int(datetime.now(timezone.utc).timestamp()) >= self.expires

import io_handles