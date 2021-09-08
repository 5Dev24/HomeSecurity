from __future__ import annotations

import bluetooth
from typing import Callable, List, Dict

class ServiceIDs:

	ServerID = "e8a407fa-0000-1000-8000-00805f9b34fb"
	ClientID = "e8a407fb-0000-1000-8000-00805f9b34fb" # Unused as relay clients have not been implemented yet

class Connection:

	def __init__(self, bt_sock: bluetooth.BluetoothSocket, recv_callback: Callable[["Connection", bytes], bool], disconnect_callback: Callable[["Connection"], None]):
		self.bt_sock = bt_sock
		self.mac: str = bt_sock._sock.getpeername()[0].upper()
		self.listen_thread = thread.EasyThread(self.__internal_init, True, recv_callback)
		self.listen_thread.start()
		self.disconnect_callback = disconnect_callback

		self.active_unencrypted_protocol: protocol.Protocol = None
		self.active_encrypted_protocol: protocol.Protocol = None
		self.session: sessions.Session = None

	def __del__(self):
		if self.session is not None:
			self.session.save()

	@property
	def closed(self):
		return getattr(self.bt_sock._sock, '_closed', False)

	def close(self):
		self.bt_sock.close()

	def send(self, data: bytes):
		if not self.closed:
			self.bt_sock.send(data)

	def __internal_init(self, callback: Callable[["Connection", bytes], bool]):
		"""
		Callback should return a truthy value to continue the connection
		Return false will terminate the connection
		"""

		if self.closed:
			self.disconnect_callback(self)
			raise thread.EasyThreadClose("Internal bluetooth socket has been closed")

		try:
			is_encrypted = self.bt_sock.recv(1)

			if len(is_encrypted) == 1:
				length_bytes = self.bt_sock.recv(3)

				if len(length_bytes) == 3:
					packet_length = packet.from_base256(length_bytes)

					if is_encrypted[0] == 0:
						if packet_length > 65544:
							raise thread.EasyThreadClose(f"Terminated recv thread due to bad unencrypted packet")

					elif is_encrypted[0] == 1:
						if packet_length > 66441:
							raise thread.EasyThreadClose(f"Terminated recv thread due to bad encrypted packet")

					else:
						raise thread.EasyThreadClose(f"Terminated recv thread due to bad flag bit ({is_encrypted[0]})")

					data: bytes = self.bt_sock.recv(packet_length)

					if len(data) == packet_length + 3:
						data = is_encrypted + length_bytes + data

						callback_return = callback(self, data)
						if callback_return: return

						self.close()
						self.disconnect_callback(self)
						raise thread.EasyThreadClose(f"Terminated recv thread due to callback returning {callback_return}")

			self.close()
			self.disconnect_callback(self)
			raise thread.EasyThreadClose(f"Terminated recv thread due to bad data")

		except bluetooth.btcommon.BluetoothError:
			self.disconnect_callback(self)
			raise thread.EasyThreadClose("Bluetooth socket died")

class Client:

	def __init__(self):
		self.bt_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
		self.server_connection: Connection = None

		self.setup()
		self.start_comms()

	def nullify(self):
		self.bt_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
		self.server_connection = None

	def setup(self, searches: int = 0):
		if searches > 32:
			print("Couldn't find server after 32 tries")
			# Device should be rebooted
			raise RuntimeError("Couldn't find a server")

		servers = self.find_servers()

		for server in servers:
			if server["protocol"] == "RFCOMM":
				try:
					print("Trying to connect")
					self.bt_sock.connect((server["host"], server["port"]))
					self.server_connection = Connection(self.bt_sock, self.__server_recv_callback, self.__server_disconnect_callback)
					return
				except bluetooth.btcommon.BluetoothError as e:
					print("Failed to connect", e)
					continue

		self.setup(searches + 1)

	def find_servers(self) -> List[dict]:
		devices = bluetooth.discover_devices(3)
		servers = []

		try:
			for address in devices:
				try:
					spd_session = bluetooth._bluetooth.SDPSession()
					spd_session.connect(address)

					for possible in spd_session.search(ServiceIDs.ServerID):
						possible["host"] = address
						servers.append(possible)

				except bluetooth._bluetooth.error:
					continue

		except bluetooth._bluetooth.error:
			pass

		return servers

	def start_comms(self):
		if self.server_connection is not None:
			if self.server_connection.session is None:
				session_mngr = sessions.SessionManager.get_manager()
				with session_mngr.lock:
					session_mngr.get_session()
		else:
			self.setup()
			self.start_comms()

	def __server_recv_callback(self, server: Connection, data: bytes) -> bool:
		try:
			packet_data = packet.dissect_packet(data)
		except ValueError:
			print("Bad packet")
			return False # Terminate connection if bad packet

	def __server_disconnect_callback(self, server: Connection):
		print("Server has disconnected at", server.mac)
		self.nullify()
		self.find_servers()

class Server:

	def __init__(self):
		self.broadcast_thread = thread.EasyThread(self.__internal_broadcast, False)
		self.bt_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
		self.bt_sock.bind((bluetooth.read_local_bdaddr()[0], 2))
		self.bt_sock.listen(3)

		self.clients: Dict[str, Connection] = {}

		self.broadcast_thread.start()

	def __internal_broadcast(self) -> None:
		bluetooth.advertise_service(self.bt_sock, "HomeSec-Server", ServiceIDs.ServerID, description = "")
		print("Server is broadcasting")

		while not getattr(self.bt_sock._sock, "_closed", False):
			print("Waiting for client")
			client, info = self.bt_sock.accept()
			device_mac = info[0].upper()
			print(f"Got client {device_mac}")

			if device_mac not in self.clients:
				print(f"Starting new connection with {device_mac}")
				self.clients[device_mac] = Connection(client, self.__client_recv_callback, self.__client_disconnect_callback)

			else:
				client.close()

	def __client_recv_callback(self, client: Connection, data: bytes) -> bool:
		try:
			packet_data = packet.dissect_packet(data)
		except ValueError:
			print("Bad packet")
			return False # Terminate connection if bad packet

		print(f"Received {packet_data}")

		# See if we know the protocol
		proto_manager = protocol.ProtocolManager.get_manager()
		if proto_manager.is_registered_protocol(packet_data.protocol_id):
			print(f"We know protocol {packet_data.protocol_id}")

			if packet_data.encrypted:
				session_manager = sessions.SessionManager.get_manager()
				if not session_manager.is_session_authenticated(packet_data.session_id):
					client.send(packet.build_unencrypted_packet(b"New session needed", 16))
					return True

				if client.session is None:
					client.session = session_manager.get_session(packet_data.session_id)

					if client.session is None: # If Session Manager dies, it will be None
						client.send(packet.build_unencrypted_packet(b"New session needed", 16))
						return True

				if client.session.id != packet_data.session_id:
					client.send(packet.build_unencrypted_packet(b"New session needed", 16))
					return True

				if client.session.has_expired:
					client.send(packet.build_unencrypted_packet(b"New session needed", 16))
					return True

				if type(client.session.client_rsa_public) != bytes:
					client.send(packet.build_unencrypted_packet(b"Cannot verify signature, no public key", 16))
					return True

				if not encryption.EasyRSA(client.session.client_rsa_public).verify(data[1:-512], packet_data.signature):
					client.send(packet.build_unencrypted_packet(b"Cannot verify signature, data didn't match signature", 16))
					return True

				failed = True

				try:
					decrypted_payload = encryption.EasyAES(client.session.shared_aes).decrypt(packet_data.payload, packet_data.mac_tag, packet_data.nonce)
				except TypeError:
					pass
				except ValueError:
					pass
				else:
					failed = False

				if failed:
					client.send(packet.build_unencrypted_packet(b"Couldn't decrypt payload", 16))
					return True

				if packet_data.previous_random != client.session.future_random: # If false, everything is working as intended
					if packet_data.previous_random != client.session.past_random: # If false, a packet was dropped
						client.send(packet.build_unencrypted_packet(b"Previous random isn't correct", 16))
						return True
					else: # The last sent packet was dropped
						# The below line subtracks one from the session step [(step - 1 + 65536) mod 65536], prevents negatives
						client.session.step = (client.session.step + 65535) % 65536 # Roll back step as we dropped a packet and the step check will fail

				if packet_data.step != (client.session.step + 1) % 65536:
					client.send(packet.build_unencrypted_packet(b"Step isn't correct", 16))
					return True

				client.session.step = packet_data.step # Save the step we've just received
				client.session.present_random = packet_data.next_random
				client.session.save()

				packet_data.payload = decrypted_payload

			# Clean up dead protocol instances
			if not client.active_unencrypted_protocol.alive:
				client.active_unencrypted_protocol = None
			if not client.active_encrypted_protocol.alive:
				client.active_encrypted_protocol = None

			if protocol.ProtocolManager.is_unencrypted_protocol(packet_data.protocol_id):
				if client.active_unencrypted_protocol is None or client.active_unencrypted_protocol.protocol_id != packet_data.protocol_id:
					if protocol.ProtocolManager.is_special_protocol(packet_data.protocol_id):
						if packet_data.protocol_id == 0: # EOP
							if client.active_unencrypted_protocol is not None:
								try:
									client.active_unencrypted_protocol.end()
								except protocol.ProtocolEnded:
									pass

								client.active_unencrypted_protocol = None

					elif protocol.ProtocolManager.is_recv_only_protocol(packet_data.protocol_id):
						tmp_proto = proto_manager.spawn_protocol(packet_data.protocol_id)
						tmp_proto.start_server(client)
						tmp_proto.received_data(packet_data.payload)
						del tmp_proto

					else:
						client.active_unencrypted_protocol = proto_manager.spawn_protocol(packet_data.protocol_id)
						client.active_unencrypted_protocol.start_server(client)
						client.active_unencrypted_protocol.received_data(packet_data.payload)

						data = client.active_unencrypted_protocol.sending_data()
						if isinstance(data, bytes) and len(data):
							client.send(packet.build_unencrypted_packet(data, packet_data.protocol_id))

				elif client.active_unencrypted_protocol.protocol_id == packet_data.protocol_id:
					client.active_unencrypted_protocol.received_data(packet_data.payload)

					data = client.active_unencrypted_protocol.sending_data()
					if isinstance(data, bytes) and len(data):
						client.send(packet.build_unencrypted_packet(data, packet_data.protocol_id))

			elif protocol.ProtocolManager.is_encrypted_protocol(packet_data.protocol_id):
				if client.active_encrypted_protocol is None or client.active_encrypted_protocol.protocol_id != packet_data.protocol_id:
					if protocol.ProtocolManager.is_special_protocol(packet_data.protocol_id):
						if packet_data.protocol_id == 256: # EOSP
							if client.active_encrypted_protocol is not None:
								try:
									client.active_encrypted_protocol.end()
								except protocol.ProtocolEnded:
									pass

								client.active_encrypted_protocol = None

					elif protocol.ProtocolManager.is_recv_only_protocol(packet_data.protocol_id):
						tmp_proto = proto_manager.spawn_protocol(packet_data.protocol_id)
						tmp_proto.start_server(client)
						tmp_proto.received_data(packet_data.payload)
						del tmp_proto

					else:
						client.active_encrypted_protocol = proto_manager.spawn_protocol(packet_data.protocol_id)
						client.active_encrypted_protocol.start_server(client)
						client.active_encrypted_protocol.received_data(packet_data.payload)

						data = client.active_encrypted_protocol.sending_data()
						if isinstance(data, bytes) and len(data):
							client.send(packet.build_encrypted_packet_with_aes(data, packet_data.protocol_id, client.session, "server"))

				elif client.active_encrypted_protocol.protocol_id == packet_data.protocol_id:
					client.active_encrypted_protocol.received_data(packet_data.payload)

					data = client.active_encrypted_protocol.sending_data()
					if isinstance(data, bytes) and len(data):
						client.send(packet.build_encrypted_packet_with_aes(data, packet_data.protocol_id, client.session, "server"))

		else:
			print("We don't know protocol", packet_data.protocol_id)
			client.send(packet.build_unencrypted_packet(b"Unknown protocol", 16))

		return True

	def __client_disconnect_callback(self, client: Connection):
		print("Client has disconnected at", client.mac)
		if client.mac in self.clients:
			del self.clients[client.mac]

import thread, encryption
from networking import packet, sessions, protocol