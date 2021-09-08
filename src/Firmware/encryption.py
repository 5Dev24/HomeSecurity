from Crypto.Random import get_random_bytes
from Crypto.Cipher import AES, PKCS1_v1_5
from Crypto.Signature import pkcs1_15
from Crypto.Cipher._mode_eax import EaxMode
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA3_512
from typing import Tuple, Union

class EasyAES:

	def __init__(self, key: bytes = None):
		if not isinstance(key, bytes):
			key = get_random_bytes(32)

		if len(key) != 32:
			raise ValueError("AES key length isn't 32 bytes")

		self.key = key # 32 bytes

	def encrypt(self, data: bytes) -> Tuple[bytes, bytes, bytes]:
		aes: EaxMode = AES.new(self.key, AES.MODE_EAX)
		return (*aes.encrypt_and_digest(data), aes.nonce) # (ciphertext, mac tag, nonce)

	def decrypt(self, ciphertext: bytes, mac_tag: bytes, nonce: bytes) -> bytes:
		aes: EaxMode = AES.new(self.key, AES.MODE_EAX, nonce)
		return aes.decrypt_and_verify(ciphertext, mac_tag)

class EasyRSA:

	def __init__(self, rsa: Union[RSA.RsaKey, bytes] = None):
		if isinstance(rsa, bytes):
			rsa = RSA.import_key(rsa)
		elif not isinstance(rsa, RSA.RsaKey):
			rsa = RSA.generate(4096)

		self.pkcs: PKCS1_v1_5.PKCS115_Cipher = PKCS1_v1_5.new(rsa)
		self.pkcs_sig: pkcs1_15.PKCS115_SigScheme = pkcs1_15.new(rsa)

	@property
	def public_key(self) -> bytes: return self.pkcs._key.public_key().export_key("DER")

	@property
	def private_key(self) -> bytes: return self.pkcs._key.export_key("DER")

	# Requires public
	def encrypt(self, data: bytes) -> bytes:
		return self.pkcs.encrypt(data)

	# Requires private
	def decrypt(self, data: bytes) -> bytes:
		return self.pkcs.decrypt(data)

	# Requires private
	def sign(self, data: bytes) -> bytes:
		return self.pkcs_sig.sign(SHA3_512.new(data))

	# Requires public
	def verify(self, data: bytes, signature: bytes) -> bool:
		try:
			self.pkcs_sig.verify(SHA3_512.new(data), signature)
		except ValueError:
			return False
		else:
			return True
