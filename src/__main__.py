#!usr/bin/python3

from __future__ import annotations
from parsing import ArgumentParser
from error import Codes, Error
from networking import Server, Request
from crypt import AES, RSA
from Crypto.Random import get_random_bytes
import sys

def main():
	'''
	Argument Parsing Example

	args = sys.argv[1:]
	argParser = ArgumentParser(None, {
		"vars": {
			"required": {
				"ip": "string"
			},
			"optional": {
				"port": "int",
				"server": "boolean"
			}
		}
	})
	argParser.parse(args)
	response = argParser.execute()

	if response == 1:
		print(argParser)
		print("Reading Variables")
		print("IP:   \"", argParser.readVariable("ip"), '"', sep = '')
		print("Port: \"", argParser.readVariable("port"), '"', sep = '')
		print("Server: \"", argParser.readVariable("server"), '"', sep = '')
		ip = argParser.readVariable("ip")
		port = argParser.readVariable("port")
		isServer = argParser.readVariable("server")
		if isServer:
			Service(ip, port, isServer)
		else:
			c = Client(ip, port + 1)
			c.connectToServer(ip)
	else: print("Got", response, "as a response!")
	'''



	'''
	Network Request Testing

	initRequest = Request(Request.methodFromString("QUERY_DATA"))
	initRequest.addData("$test")
	genRequest = Request.new(initRequest.getRequestString())
	print(initRequest.toPrint())
	print(genRequest)
	'''


	'''
	Network Broadcasting Testing
	'''
	server = Server()
	client = Client()



	'''
	Proof That AES Key Exchange Can Occur Using RSA

	B = ""
	while len(B) < 128:
		try:
			B += str(repr(get_random_bytes(1).decode("utf-8")).replace("\'", "").replace("\\", "").replace(" ", ""))
		except:
			pass
	print("Key:", B) # Server creates key
	aes = AES(B) # Server creates AES with key
	initialMessageServerWantsToSend = "AES key was sent securly with zero problems!"
	resultFromServer = aes.encrypt(initialMessageServerWantsToSend)
	serverRSA = RSA(False) # Server creates a RSA
	print("\nServer Public Key:", serverRSA.pubKey())

	clientRSA = RSA(True) # Client creates a RSA
	print("\nClient Public Key:", clientRSA.pubKey())
	serverRSASentToClient = serverRSA.pubKey() # Client gets server's public rsa key
	serverRSAForClient = RSA.new(True, serverRSASentToClient) # Client creates an rsa with the servers public key

	clientRSAToBeSentToServer = serverRSAForClient.encrypt(clientRSA.pubKey()) # Client encrypts its own RSA key with the server's public key
	print("\nClient's Encrypted Public Key: ", clientRSAToBeSentToServer)
	clientsRSAForServer = RSA.new(False, serverRSA.decrypt(clientRSAToBeSentToServer)) # Server decrypts the clients RSA key with its own private key
	print("\nClient's Decrypted Public Key: ", clientsRSAForServer.pubKey())

	print("\nKeys Match?:", clientsRSAForServer.verifyPubSame(clientRSA.pubKey()))

	AESKeyEncrpytedForClient = clientsRSAForServer.encrypt(bytes(B, "utf-8"))
	print("\nEncrypted AES Key For Client:", AESKeyEncrpytedForClient)

	clientDecryptedAESKey = clientRSA.decrypt(AESKeyEncrpytedForClient)
	print("\nDecrypted AES Key In Client:", clientDecryptedAESKey)

	clientAESInstance = AES(clientDecryptedAESKey)
	clientDecryptedServerMessageEncryptedWithAES = clientAESInstance.decrypt(resultFromServer)
	print("\nDecrypted Message From AES:", clientDecryptedServerMessageEncryptedWithAES)

	print("\nMessage Match?:", clientDecryptedServerMessageEncryptedWithAES == initialMessageServerWantsToSend)
	'''



	'''
	Testing AES and RSA

	aes = AES("my special key that noone knows, in the entire world!")
	msg = "my secret message that should be kept secret"
	enc = aes.encrypt(msg)
	dec = aes.decrypt(enc)
	rsa1 = RSA()
	rsa2 = RSA.new(rsa1.pubKey())
	print("PubKey 1:", rsa1.pubKey())
	print("PubKey 2:", rsa2.pubKey())
	print(rsa1 == rsa2)
	print(rsa1.pubKey() == rsa2.pubKey())

	print("Original Message:", msg)
	print("Encrypted Message:", enc)
	print("Decrypted Message:", dec)
	'''

if __name__ == "__main__": main()
