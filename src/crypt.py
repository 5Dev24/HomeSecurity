
from Crypto.Random import get_random_bytes
from Crypto.Cipher import AES as _AES
from Crypto.Cipher import PKCS1_OAEP as _PKCS
from Crypto.PublicKey import RSA as _RSA
from Crypto.PublicKey.pubkey import getPrime
from Crypto.Hash import SHA256 as _SHA256
from hashlib import sha256
import hashlib
from error import Error, Codes

CONSTS = {
	"SALT_LENGTH": 2**16,
	"AES_KEY_SIZE": 144,
	"KEY_ITERNATIONS": 2**16
}

class AES:
	"""
	Handles all AES encryption

	All errors or problems will end with the program dying as if encryption fails, the program should die
	"""

	def __init__(self, key: str = None):
		if key is None: Error(TypeError(), Codes.KILL, "No key for AES was sent (1)")
		self._key = bytes(key, "utf-8")

	def _generateKey(self, key: bytes = None, salt: bytes = None):
		if key is None: Error(TypeError(), Codes.KILL, "No key for AES was sent (2)")
		if salt is None: Error(TypeError(), Codes.KILL, "No salt for AES was sent")
		key += salt
		for i in range(CONSTS["KEY_ITERNATIONS"]): key = sha256(key).digest()
		return [key, salt]

	def _addPadding(self, msg: str = None):
		if msg is None or len(msg) == 0: Error(TypeError(), Codes.KILL, "No message as passed for AES padding addition")
		paddingBytes = len(msg) % CONSTS["AES_KEY_SIZE"]
		paddingSize = CONSTS["AES_KEY_SIZE"] - paddingBytes
		msg += chr(paddingSize) * paddingSize
		return msg

	def _removePadding(self, msg: bytes = None):
		if msg is None or len(msg) < CONSTS["SALT_LENGTH"]: Error(TypeError(), Codes.KILL, "No message as passed for AES padding removal")
		return msg[:-msg[-1]]

	def encrypt(self, msg: str = None):
		if msg is None or len(msg) == 0: Error(TypeError(), Codes.KILL, "Empty message as passed for AES encryption")
		key, salt = self._generateKey(self._key, get_random_bytes(CONSTS["SALT_LENGTH"]))
		aes = _AES.new(key, _AES.MODE_ECB)
		encryptedText = aes.encrypt(self._addPadding(msg))
		return salt + encryptedText

	def decrypt(self, msg: str = None):
		if msg is None or len(msg) < CONSTS["SALT_LENGTH"]: Error(TypeError(), Codes.KILL, "Empty message as passed for AES decryption")
		key, salt = self._generateKey(self._key, msg[:CONSTS["SALT_LENGTH"]])
		aes = _AES.new(key, _AES.MODE_ECB)
		return self._removePadding(aes.decrypt(msg[CONSTS["SALT_LENGTH"]:])).decode("utf-8")

'''
a = _RSA.generate(256*16, e=getPrime(2^64 - 1))
b = _PK.new(a, hashAlgo=_SHA)
msg = 'test'
c = b.encrypt(bytes(msg, "utf-8"))
d = b.decrypt(c)
'''

class RSA:

	@staticmethod
	def new(isClient: bool = False, pubKeyOpenSSH: str = None):
		return RSA(isClient, _RSA.importKey(pubKeyOpenSSH, passphrase=None if not (pubKeyOpenSSH is None) else RSA()))

	def __init__(self, isClient: bool = False, rsa: object = None):
		if rsa is None: self._rsa = _RSA.generate(256*(8 if isClient else 16), e=getPrime(2^64 - 1))
		else: self._rsa = rsa
		self._pkcs = _PKCS.new(self._rsa, hashAlgo=_SHA256)

	def pubKey(self): return self._rsa.exportKey(format="OpenSSH", passphrase=None, pkcs=1)

	def verifyPubSame(self, pubKeyOpenSSH: str = None): return self.pubKey() == pubKeyOpenSSH

	def encrypt(self, msg: str = None):
		if msg is None or len(msg) == 0: Error(TypeError(), Codes.KILL, "No message was passed for RSA encryption")
		return self._pkcs.encrypt(msg)

	def decrypt(self, msg: bytes = None):
		if msg is None or len(msg) == 0: Error(TypeError(), Codes.KILL, "No message was passed for RSA decryption")
		return self._pkcs.decrypt(msg).decode("utf-8")

'''
Client requests Servers Public Key
Client encypts their Public Key with Server Public Key
Client sends server back there encrypted Client Public Key 
Server decrypts Clients RSA Public Key using Server Private Key
Server uses Client Public Key to encrypt AES Key
Server sends encrypted AES Key to Client
Client decrypts AES Key using Client Private Key
Client encrypts the message "Key Recieved" and sends it to the server
Server decrypts the message and should recieve "Key Recieved" if not, repeat process until AES Key is properly exchanged
'''
