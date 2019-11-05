#!usr/bin/python3

from src.file import RSAFile
from src.crypt import FormatBytes

def main():
	f = RSAFile.new("test.test", False)
	print(f.keys)
	rsa = f.crypto
	originalMsg = "Test Message To Test The Encryption Of RSA That Was Saved To A File Before!"
	print("Original Msg:", originalMsg)
	encrypt_msg = rsa.encrypt(originalMsg)
	formatted = FormatBytes(encrypt_msg)
	unformatted = FormatBytes(formatted)
	print("Original:", encrypt_msg)
	print("Formatted:", formatted)
	print("Unformatted:", unformatted)
	#print("Encrypted Msg:", encrypt_msg)
	decrypt_msg = rsa.decrypt(encrypt_msg)
	print("Decrypted Msg:", decrypt_msg)

if __name__ == "__main__": main()
