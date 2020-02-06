from Crypto import Random as _Ran
from Crypto.Random import get_random_bytes
from Crypto.Cipher import AES as _AES
from Crypto.Cipher import PKCS1_OAEP as _PKCS
from Crypto.PublicKey import RSA as _RSA
from Crypto.Util.number import getPrime
from Crypto.Hash import SHA256 as _SHA256
from hashlib import sha256
from string import ascii_uppercase as Alph

CONSTS = {
	"SALT_LENGTH": 2**8, # Length of salt
	"AES_KEY_SIZE": 144, # Length of AES keys
	"KEY_ITERNATIONS": 2**16, # Times to use SHA256 on key
	"CLIENT_RSA": 2**10, # RSA key length for clients
	"SERVER_RSA": 2**11, # RSA key length for servers
	"RSA_PRIME": 101 # RSA prime
}

def FormatBytes(obj: object = None):
	if type(obj) == bytes: # If object type is bytearray
		return "".join([Alph[i // 26] + Alph[i % 26] for i in obj]) # Create a 2 letter pair to represent the value of the byte and return list of them merged
	elif type(obj) == str: # If object type is string
		return bytes([Alph.find(obj[i]) * 26 + Alph.find(obj[i+1]) for i in range(0, len(obj), 2)]) # Return a list of bytes after decoding letters into bytes

class AES:

	def __init__(self, key: object = None):
		if key is None or len(key) < 32: return None
		if type(key) is not bytes: key = bytes(key, "utf-8")

		self._key = key

	def _generate_crypt(self, key: bytes = None, salt: bytes = None):
		if type(key) is not bytes or len(key) < 32: return None
		if type(key) is not bytes: return None

		key += salt
		for i in range(CONSTS["KEY_ITERNATIONS"]): key = sha256(key).digest()
		return [key, salt]

	def _add_padding(self, msg: str = None):
		if msg is None or not len(msg): return None

		paddingBytes = len(msg) % CONSTS["AES_KEY_SIZE"]
		paddingSize = CONSTS["AES_KEY_SIZE"] - paddingBytes
		msg += chr(paddingSize) * paddingSize
		return msg

	def _remove_padding(self, msg: bytes = None):
		if msg is None or len(msg) < CONSTS["SALT_LENGTH"]: return ""
		return msg[:-msg[-1]]

	def encrypt(self, msg: str = None):
		if msg is None or not len(msg): return None

		key, salt = self._generate_crypt(self._key, get_random_bytes(CONSTS["SALT_LENGTH"]))
		aes = _AES.new(key, _AES.MODE_ECB)
		encryptedText = aes.encrypt(bytes(self._add_padding(msg), "utf-8"))
		return (salt + encryptedText)

	def decrypt(self, msg: str = None):
		if msg is None or len(msg) < CONSTS["SALT_LENGTH"]: return None

		key = self._generate_crypt(self._key, msg[:CONSTS["SALT_LENGTH"]])[0]
		aes = _AES.new(key, _AES.MODE_ECB)
		return self._remove_padding(aes.decrypt(msg[CONSTS["SALT_LENGTH"]:])).decode("utf-8")

class RSA:

	@staticmethod
	def new(is_clients: bool = False, key: str = None):
		return RSA(is_clients, _RSA.importKey(key))

	@staticmethod
	def remove_extra_detail_on_key(key: object = None):
		if type(key) == bytes: key = key.decode("utf-8")

		finalKey = [k for k in key.split("\n")]
		del finalKey[0]
		del finalKey[len(finalKey) - 1]

		return "".join(finalKey)

	@staticmethod
	def add_extra_detail_to_key(key: str = None, is_public: bool = True):
		return "-----BEGIN " + ("PUBLIC" if is_public else "PRIVATE") + " KEY-----\n" + key + "\n-----END " + ("PUBLIC" if isPublic else "PRIVATE") + " KEY-----"

	def __init__(self, is_clients: bool = False, rsa: object = None):
		if rsa is None: self._rsa = _RSA.generate(CONSTS["CLIENT_RSA"] if is_clients else CONSTS["SERVER_RSA"], e=getPrime(CONSTS["RSA_PRIME"]))
		else: self._rsa = rsa
		self._pkcs = _PKCS.new(self._rsa, hashAlgo=_SHA256)

	def pubKey(self):
		return RSA.remove_extra_detail_on_key(self._rsa.publickey().export_key("PEM"))

	def privKey(self):
		return RSA.remove_extra_detail_on_key(self._rsa.export_key("PEM"))

	def verifyPubSame(self, key: str = None):
		return self.pubKey() == key

	def encrypt(self, msg: str = None):
		if msg is None or len(msg) == 0: return None

		out = ""
		for i in range(len(msg) // 128 + 1):
			out += FormatBytes(self._pkcs.encrypt(msg[i*128:(i+1)*128].encode("utf-8")))
		return out

	def decrypt(self, msg: str = None):
		if msg is None or len(msg) == 0: return None

		out = ""
		for i in range(len(msg.encode("utf-8")) // 512):
			out += self._pkcs.decrypt(FormatBytes(msg[i*512:(i+1)*512])).decode("utf-8", "blackslashreplace")
		return out
