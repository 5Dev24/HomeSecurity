"""

Donny G Measurements

Base 28cm X 36cm (side x front)
152cm tall



Instructions

sudo apt update && sudo apt upgrade
sudo apt install python3 python3-pip python3-dev bluetooth
sudo pip3 install pybluez

sudo sdptool add SP

Consider changing "ControllerMode" in /etc/bluetooth/main.conf to "le" to force low energy only mode

sudo reboot
or
sudo systemctl daemon-reload
sudo service bluetooth restart

Run 'sudo bluetoothctl system-alias "<name>"' to change the adapter name
"""

import bluetooth, threading # Change to multiprocessing later
from typing import List

server_id = "e8a407fa-0000-1000-8000-00805f9b34fb"
client_id = "e8a407fb-0000-1000-8000-00805f9b34fb"

server_uuid = "jnbsisebngf30n038nfw0eifknse0ofiun03tuw9ofuinseo9gfnse"
client_uuid = "uwnf92fu239nf0qifnm0ifnmai0nf0egu4h9u0uo9wng0eiasnf0ne"

def server_client_thread(client: bluetooth.BluetoothSocket, info: str):
	try:
		print("Client info: ", info, ", Type: ", type(info), sep="")
		while True:
			data = client.recv(2048)
			if data:
				data = data.decode("utf-8")
				print(f"Got \"{data}\"")
				client.send(f"echo {data}")
	except bluetooth.btcommon.BluetoothError:
		print("Bluetooth error was raised")
	finally:
		client.close()
		print("Closed the client connection to us (server)")

def main():
	name = input("Type (Server/Client): ").lower()

	if name == "server":
		try:
			server_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
			server_sock.bind((bluetooth.read_local_bdaddr()[0], 2))
			server_sock.listen(2)

			bluetooth.advertise_service(server_sock, "HomeSec-Server", server_id, description = server_uuid)
			print("Advertising...")

			while True:
				print("Awaiting client connection")
				client, info = server_sock.accept()
				bluetooth.stop_advertising(server_sock)
				threading.Thread(target = server_client_thread, args = (client, info), daemon = True).start()
		finally:
			server_sock.close()
			print("Closed server socket")

	else:
		devices: List[dict] = []
		while not len(devices):
			print("Searching for server service")
			devices = bluetooth.find_service(uuid = server_id)

		for device in devices:
			print("device", device)
			print(f"Found a server at {device['host']}:{device['port']} on {device['protocol']}, attempting to open socket")
			if device['protocol'] != "RFCOMM":
				print("Unsupported protocol")
				continue

			try:
				client_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
				client_sock.connect((device['host'], device['port']))

				while True:
					data_to_send = input("Data: ")
					if data_to_send == "exit":
						break

					client_sock.send(data_to_send)

					data = client_sock.recv(2048)
					if data:
						data = data.decode("utf-8")
						print(f"Got back \"{data}\"")

			except bluetooth.btcommon.BluetoothError:
				print("Bluetooth error was raised")
			finally:
				client_sock.close()
				print("Closed client to server socket")

if __name__ == "__main__":
	main()