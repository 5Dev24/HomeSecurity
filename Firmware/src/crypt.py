from Crypto import Random as _Ran
from Crypto.Random import get_random_bytes
from Crypto.Cipher import AES as _AES
from Crypto.Cipher import PKCS1_OAEP as _PKCS
from Crypto.PublicKey import RSA as _RSA
from Crypto.Util.number import getPrime
from Crypto.Hash import SHA256 as _SHA256
from hashlib import sha256
import hashlib
from .error import Error, Codes
from string import ascii_uppercase as Alph

CONSTS = {
	"SALT_LENGTH": 2**8, # Length of salt
	"AES_KEY_SIZE": 144, # Length of AES keys
	"KEY_ITERNATIONS": 2**16, # Times to use SHA256 on key
	"CLIENT_RSA": 2**10, # RSA key length for clients
	"SERVER_RSA": 2**11, # RSA key length for servers
	"RSA_PRIME": 101 # RSA prime
}
"""
All constants used for encryption
"""

def FormatBytes(obj: object = None):
	"""
	Used to turn a bytearray to a string or to turn a string into a bytearray

	Args:
		obj (bytes/str): A bytearray or string

	Returns:
		bytearray/str: If a bytearray is passed, a string is returned. If a string is passed, a bytearray is returned
	"""
	if type(obj) == bytes: # If object type is bytearray
		return "".join([Alph[i // 26] + Alph[i % 26] for i in obj]) # Create a 2 letter pair to represent the value of the byte and return list of them merged
	elif type(obj) == str: # If object type is string
		return bytes([Alph.find(obj[i]) * 26 + Alph.find(obj[i+1]) for i in range(0, len(obj), 2)]) # Return a list of bytes after decoding letters into bytes

class AES:
	"""
	Handles all AES encryption

	All errors or problems will end with the program dying as if encryption fails, the program should die
	"""

	def __init__(self, key: object = None):
		"""
		Init

		Args:
			key (object): AES key to use, string or bytes list

		Attributes:
			_key (bytes): AES key in a bytearray

		Raises:
			TypeError: Raised if the key is none or the length is less than 32
		"""
		if key is None or len(key) < 32: Error(TypeError(), Codes.KILL, "No key for AES was sent (1)") # Make sure key something and that it's atleast 32 charcters long, else throw error
		if type(key) != bytes: key = bytes(key, "utf-8") # If key isn't a bytearray, make it a bytearray with utf-8 encoding
		self._key = key # Save key as byte list

	def _generateCrypt(self, key: bytes = None, salt: bytes = None):
		"""
		Generates the key and salt for encryption/decrpyion

		Args:
			key (bytes): Key to use
			salt (bytes): Salt to use

		Raises:
			TypeError: Raised if the key is none or length is less than 32 or the salt is none

		Returns:
			list: The key and the salt
		"""
		if key is None or len(key) < 32: Error(TypeError(), Codes.KILL, "No key for AES was sent (2)") # If key is empty or isn't atleast 32 characters long, throw error
		if salt is None: Error(TypeError(), Codes.KILL, "No salt for AES was sent") # If salt is empty, throw error
		key += salt # Add the salt to the key
		for i in range(CONSTS["KEY_ITERNATIONS"]): key = sha256(key).digest() # Push the key through sha256 x number of times
		return [key, salt] # Return key salted and the salt used

	def _addPadding(self, msg: str = None):
		"""
		Adds padding to a message before encryption

		Args:
			msg (str): The message to pad

		Raises:
			TypeError: Raised if the message is none or the length is zero

		Returns:
			str: The padded message
		"""
		if msg is None or not len(msg): Error(TypeError(), Codes.KILL, "No message as passed for AES padding addition") # If message is None or empty, throw error
		paddingBytes = len(msg) % CONSTS["AES_KEY_SIZE"] # Get number of bytes to pad
		paddingSize = CONSTS["AES_KEY_SIZE"] - paddingBytes # Get length of padding
		msg += chr(paddingSize) * paddingSize # Pad using the character representation of the padding size, the padding size number of times
		return msg # Return the now padded message

	def _removePadding(self, msg: bytes = None):
		"""
		Removes padding from a decrypted message

		Args:
			msg (bytes): The message, still in byte form

		Raises:
			TypeError: Raised if the message is none or the length is zero

		Returns:
			bytes: The message, minus the padding
		"""
		if msg is None or len(msg) < CONSTS["SALT_LENGTH"]: Error(TypeError(), Codes.KILL, "No message as passed for AES padding removal") # If message is none or length is less than expected padding, throw error
		return msg[:-msg[-1]] # Remove padding and return message

	def encrypt(self, msg: str = None):
		"""
		Encrypts a message using the key

		Args:
			msg (str): The message to encrypt

		Raises:
			TypeError: Raised if the message is none or the length is zero

		Returns:
			bytes: The encrypted message
		"""
		if msg is None or not len(msg): Error(TypeError(), Codes.KILL, "Empty message as passed for AES encryption") # If message is None or it's empty, throw error
		key, salt = self._generateCrypt(self._key, get_random_bytes(CONSTS["SALT_LENGTH"])) # Generate key from a random salt
		aes = _AES.new(key, _AES.MODE_ECB) # Create a new instance of AES from pycryptodome
		encryptedText = aes.encrypt(bytes(self._addPadding(msg), "utf-8")) # Add padding to message and then encrypt it
		return (salt + encryptedText) # Add salt to front of encrypted message to be able to decrypt later

	def decrypt(self, msg: str = None):
		"""
		Decrypts a message using the key

		Args:
			msg (str): The message to decrypt

		Raises:
			TypeError: Raised if the message is none or the length is less than the salt

		Returns:
			str: The decrypted message
		"""
		if msg is None or len(msg) < CONSTS["SALT_LENGTH"]: Error(TypeError(), Codes.KILL, "Empty message as passed for AES decryption") # If message is empty of less than the salt length, throw error
		key = self._generateCrypt(self._key, msg[:CONSTS["SALT_LENGTH"]])[0] # Get key for decryption
		aes = _AES.new(key, _AES.MODE_ECB) # Create a new instance of AES from pycryptodome
		return self._removePadding(aes.decrypt(msg[CONSTS["SALT_LENGTH"]:])).decode("utf-8") # Decrypt the message, remove the padding, then decode to string in format utf-8

class RSA:
	"""
	Handles all RSA encryption

	All errors or problems will end with the program dying as if encryption fails, the program should die
	"""

	@staticmethod
	def new(isClients: bool = False, key: str = None):
		"""
		Generate new RSA instance from a public key

		:param isClients bool: If this is from a client
		:param key str: The public key in any format

		:returns RSA: New instance spawned from a key
		"""
		return RSA(isClients, _RSA.importKey(key)) # Create key

	@staticmethod
	def removeExtraDetailOnKey(key: object = None):
		"""
		Removes the lines before and after a key that say if it's a public or private key

		:param key object: The key object itself

		:returns str: The key without the exit details
		"""
		if type(key) == bytes: key = key.decode("utf-8") # If key is a bytearray, decode it to a string
		finalKey = [k for k in key.split("\n")] # Split on all newline characters
		del finalKey[0] # Remove the first line
		del finalKey[len(finalKey) - 1] # Remvoe the last line
		return "".join(finalKey) # Merge all remaining lines together

	@staticmethod
	def addExtraDetailToKey(key: str = None, isPublic: bool = True):
		"""
		Adds back if a key is public or private so that an RSA instance can be made from it

		:param key str: The key without the details
		:param isPublic bool: If the key is a public key

		:returns str: The key with the details added back
		"""
		return "-----BEGIN " + ("PUBLIC" if isPublic else "PRIVATE") + " KEY-----\n" + key + "\n-----END " + ("PUBLIC" if isPublic else "PRIVATE") + " KEY-----" # Add back details to key at beginning and end

	def __init__(self, isClients: bool = False, rsa: object = None):
		"""
		Init

		:param isClients bool: If this is from a client
		:param rsa RSA: A rsa instance from pycryptodome, not required

		:returns self: Instance
		"""
		if rsa is None: self._rsa = _RSA.generate(CONSTS["CLIENT_RSA"] if isClients else CONSTS["SERVER_RSA"], e=getPrime(CONSTS["RSA_PRIME"])) # If no rsa was passed, generate new one
		else: self._rsa = rsa # Save rsa if it was already created
		self._pkcs = _PKCS.new(self._rsa, hashAlgo=_SHA256) # Save PKCS for RSA using SHA256

	def pubKey(self):
		"""
		Gets the public key in open ssh format

		:returns str: The public key
		"""
		return RSA.removeExtraDetailOnKey(self._rsa.publickey().export_key("PEM")) # Returns the public key

	def privKey(self):
		"""
		Gets the private key in open ssh format

		:returns str: The private key
		"""
		return RSA.removeExtraDetailOnKey(self._rsa.export_key("PEM")) # Returns the private key

	def verifyPubSame(self, key: str = None):
		"""
		Checks if the input public key is the same as the one in this instance

		:param key str: 

		:returns bool: If they are the same key
		"""
		return self.pubKey() == key # Compare the keys

	def encrypt(self, msg: str = None):
		"""
		Encrypts a string

		:param msg str: The message to encrypt

		:raises: TypeError if the msg is none or the length is 0

		:returns str: The encrypted message
		"""
		if msg is None or len(msg) == 0: Error(TypeError(), Codes.KILL, "No message was passed for RSA encryption") # If message is empty, throw error
		out = "" # Encrypted message
		for i in range(len(msg.encode("utf-8")) // 128 + 1): # Loop through message in chunks of 128
			out += FormatBytes(self._pkcs.encrypt(msg[i*128:(i+1)*128].encode("utf-8"))) # Encrypt a part of the message and encode the bytes to the system of bytes I created
		return out # Return encrypted message

	def decrypt(self, msg: str = None):
		"""
		Decrypts a string

		:param msg str: The message to decrypt

		:raises: TypeError if the msg is none or the length is 0

		:returns str: The decrypted message
		"""
		if msg is None or len(msg) == 0: Error(TypeError(), Codes.KILL, "No message was passed for RSA decryption") # If message is empty, throw errro
		out = "" # Decrypted string
		for i in range(len(msg.encode("utf-8")) // 512): # Loop through message in chunks of 512
			out += self._pkcs.decrypt(FormatBytes(msg[i*512:(i+1)*512])).decode("utf-8") # Unformat the bytes, decrypt it, then decode to utf-8
		return out # Return the decrypted string
