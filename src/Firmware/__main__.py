#!/usr/bin/python3

from typing import Tuple
import sys, atexit, argparse

def init_argparse() -> Tuple[argparse.ArgumentParser, argparse.Namespace]:
	parser = argparse.ArgumentParser(prog = "homesec", description = "HomeSec Security System", allow_abbrev = False)
	parser.add_argument("--install", nargs = 1, type = str, help = "Causes HomeSec to be installed on the device", metavar = "type")
	parser.add_argument("--force", action = "store_true", help = "Forces actions that prompt for force to be used")
	parser.add_argument("--logs", nargs = "*", type = int, help = "Displays the last 50 log entries and exits", metavar = "count")
	parser.add_argument("--aided", action="store_true", help = "Acts as a guided install")
	return (parser, parser.parse_args(sys.argv[1:]))

def main():
	import logger
	from networking import sessions

	# Save sessions and clear out the save & log queues
	atexit.register(sessions.SessionManager.get_manager().shutdown)
	atexit.register(logger.Logger.get_logger().finalize)

	parser, options = init_argparse()

	if options.install and isinstance(options.install, list) and len(options.install) == 1:
		import installer
		install_type = options.install[0].lower()
		if install_type not in ("server", "client"):
			parser.error("Provided install type must be either \"server\" or \"client\"")

		installer.main(install_type, options.force)

	elif isinstance(options.logs, list):
		import logger
		if len(options.logs) != 1: options.logs = [50]

		logs = logger.Logger.get_logger().get(options.logs[0])

		for log in logs:
			logger.Logger.get_logger().print(log)

	elif options.aided:
		choice = ""
		while choice not in ("server", "client"):
			choice = input("What type of installation do you want [server/client]: ").lower()

		install_type = choice

		while choice not in ("y", "yes", "no", "n", "false", "f", "true", "t"):
			choice = input("Would you like to forcefully override any pre-existing installation if it is found while installing (yes/no): ").lower()

		force = choice in ("y", "yes", "true", "t")

		import installer

		installer.main(install_type, force)

	else:
		import installer
		install_data = installer.get_installation()
		print("Starting as", install_data)

		# init system

		import networking.net_io_handles as net_handles
		import networking.packet as packet

		if install_data[0] == "server":
			net_handles.Server()
			import thread
			thread.lock_main_thread()

		elif install_data[0] == "client":
			client = net_handles.Client()

			while True:
				data_to_send = input("Data: ")
				if data_to_send == "exit":
					client.bt_sock.close()
					break

				client.bt_sock.send(packet.build_packet(data_to_send.encode("utf-8"), 2, 0))

				data = client.bt_sock.recv(65833)
				if data:
					try:
						packet_data = packet.dissect_packet(data)
					except ValueError:
						print("Failed to parse server packet")
						client.bt_sock.close()
						break

					print(f"Server responded with {packet_data}")

		import failure
		failure.die(failure.SystemCode.Success, "Exited normally")

if __name__ == "__main__":
	main()