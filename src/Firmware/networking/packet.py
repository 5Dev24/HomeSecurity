import secrets
from struct import pack
from typing import NamedTuple, Tuple

class PacketStructure(NamedTuple):
	encrypted: bool
	packet_length: int
	device_version: Tuple[int, int, int]
	protocol_id: int
	payload: bytes

	step: int = None
	session_id: bytes = None
	nonce: bytes = None
	mac_tag: bytes = None
	previous_random: bytes = None
	next_random: bytes = None
	signature: bytes = None

def from_base256(data: bytes) -> int:
	value = len(data) - 1
	total = 0

	for index in range(value, -1, -1):
		total += 256 ** (value - index) * data[index]

	return total

def to_base256(value: int) -> bytes:
	values = []

	while value > 0:
		values.insert(0, value % 256)
		value //= 256

	return bytes(values)

def get_length_data(length: int, min_length: int = None, max_length: int = None) -> bytes:
	length_bytes = to_base256(length)

	if max_length is not None and max_length > 0 and min_length is not None and min_length > 0 and min_length > max_length:
		raise ValueError(f"Minimum length is greater than maximum length, ({min_length} > {max_length})")

	if min_length is not None and min_length > 0:
		if len(length_bytes) < min_length:
			length_bytes = (b"\00" * (min_length - len(length_bytes))) + length_bytes

	if max_length is not None and max_length > 0:
		if len(length_bytes) > max_length:
			raise ValueError(f"Data is too long such that it's length cannot be saved in only {max_length} bytes, it needs at least {len(length_bytes)} bytes")

	return length_bytes

def add_length_data(data: bytes, min_length: int = None, max_length: int = None) -> bytes:
	return get_length_data(len(data), min_length, max_length) + data

def build_unencrypted_packet(payload: bytes, protocol_id: int) -> bytes:
	if protocol_id < 0 or protocol_id > 255:
		raise ValueError("Protocol ID must be between 0 and 255, greater than 255 is encrypted and lower isn't supported")

	if len(payload) > 65535:
		raise ValueError("Invalid Payload, too long")

	packet: bytes = installer.get_version_bytes()

	packet += to_base256(protocol_id)

	packet += add_length_data(payload, 2, 2) # No error should be raised

	return bytes([0]) + add_length_data(packet, 3, 3) # If ValueError raised, packet is too long

def build_encrypted_packet(payload: bytes, protocol_id: int, session: "sessions.Session", sender: str, nonce: bytes, mac_tag: bytes) -> bytes:
	if protocol_id < 256 or protocol_id > 65535:
		raise ValueError("Protocol ID must be between 256 and 65535, lower than 256 is unencrypted and higher isn't supported")

	if session.step < 0:
		raise ValueError("Invalid Step")

	if not isinstance(session.id, bytes) or len(session.id) != 32:
		raise ValueError("Invalid Session ID")

	if not isinstance(nonce, bytes) or len(nonce) != 16:
		raise ValueError("Invalid Nonce")

	if not isinstance(mac_tag, bytes) or len(mac_tag) != 16:
		raise ValueError("Invalid Mac Tag")

	next_random = secrets.token_bytes(32)

	if len(payload) > 65535:
		raise ValueError("Invalid Payload, too long")

	sender = sender.lower()
	if sender not in ("server", "client"):
		raise ValueError("Invalid Sender")

	packet = installer.get_version_bytes()

	packet += add_length_data(to_base256(protocol_id), 1, 1) # No error should be raised

	packet += bytes([(session.step + 1) // 256 % 256, (session.step + 1) % 256])

	packet += session.id

	packet += nonce

	packet += mac_tag

	packet += session.present_random

	packet += next_random

	packet += add_length_data(payload, 2, 2) # No error should be raised

	packet = add_length_data(len(packet) + 512, 3, 3) + packet

	if sender == "server":
		rsa = encryption.EasyRSA(session.server_rsa_private)
	elif sender == "client":
		rsa = encryption.EasyRSA(session.client_rsa_private)

	signature = rsa.sign(packet)

	session.step = (session.step + 1) % 65536 # Save the step we've just sent, we'll expect plus 1 back
	session.past_random = session.future_random
	session.future_random = next_random
	session.save()

	return bytes([1]) + packet + signature # If ValueError raised, packet is too long

def build_encrypted_packet_with_aes(payload: bytes, protocol_id: int, session: "sessions.Session", sender: str) -> bytes:
	payload, mac_tag, nonce = encryption.EasyAES(session.shared_aes).encrypt(payload)

	return build_encrypted_packet(payload, protocol_id, session, sender, nonce, mac_tag)

def dissect_packet(packet: bytes) -> PacketStructure:
	current_packet_length = len(packet)

	if not current_packet_length:
		raise ValueError("Empty packet")

	is_encrypted = packet[0] == 1
	packet = packet[1:]
	current_packet_length -= 1

	if current_packet_length < 3:
		raise ValueError("Invalid End Of Packet")

	packet_length = from_base256(packet[:3])
	packet = packet[3:]
	current_packet_length -= 3

	if current_packet_length < 3:
		raise ValueError("Invalid End Of Packet")

	device_version = tuple(packet[:3])
	packet = packet[3:]
	current_packet_length -= 3

	if current_packet_length < 2:
		raise ValueError("Invalid End Of Packet")

	if is_encrypted:
		protocol_id_length = from_base256(packet[:1])
		packet = packet[1:]
		current_packet_length -= 1

		if current_packet_length < protocol_id_length:
			raise ValueError("Invalid End Of Packet")

		protocol_id = from_base256(packet[:protocol_id_length])
		packet = packet[protocol_id_length:]
		current_packet_length -= protocol_id_length

	else:
		protocol_id = from_base256(packet[:1])
		packet = packet[1:]
		current_packet_length -= 1

	if current_packet_length < 2:
		raise ValueError("Invalid End Of Packet")

	step = None
	session_id = None
	nonce = None
	mac_tag = None
	previous_random = None
	next_random = None
	signature = None

	if is_encrypted:
		if current_packet_length < 2:
			raise ValueError("Invalid End Of Packet")

		step = from_base256(packet[:2])
		packet = packet[2:]
		current_packet_length -= 2

		if current_packet_length < 32:
			raise ValueError("Invalid End Of Packet")

		session_id = packet[:32]
		packet = packet[32:]
		current_packet_length -= 32

		if current_packet_length < 16:
			raise ValueError("Invalid End Of Packet")

		nonce = packet[:16]
		packet = packet[16:]
		current_packet_length -= 16

		if current_packet_length < 16:
			raise ValueError("Invalid End Of Packet")

		mac_tag = packet[:16]
		packet = packet[16:]
		current_packet_length -= 16

		if current_packet_length < 32:
			raise ValueError("Invalid End Of Packet")

		previous_random = packet[:32]
		packet = packet[32:]
		current_packet_length -= 32

		if current_packet_length < 32:
			raise ValueError("Invalid End Of Packet")

		next_random = packet[:32]
		packet = packet[32:]
		current_packet_length -= 32

	if current_packet_length < 2:
		raise ValueError("Invalid End Of Packet")

	payload_length = from_base256(packet[:2])
	packet = packet[2:]
	current_packet_length -= 2

	if current_packet_length < payload_length:
		raise ValueError("Invalid End Of Packet")

	payload = packet[:payload_length]
	packet = packet[payload_length:]
	current_packet_length -= payload_length

	if is_encrypted:
		if current_packet_length < 512:
			raise ValueError("Invalid End Of Packet")

		signature = packet[:512]
		packet = packet[512:]
		current_packet_length -= 512

	if len(packet):
		raise ValueError("Didn't reach End Of Packet")

	return PacketStructure(is_encrypted, packet_length, device_version, protocol_id, payload, step, session_id, nonce, mac_tag, previous_random, next_random, signature)

import installer, encryption
from networking import sessions

def test():
	pass # Make unit tests