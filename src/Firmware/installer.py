from typing import BinaryIO, Tuple
import subprocess

def get_current_version() -> str: return "0.0.1"

def get_version_string() -> str: return get_installation()[1]

def get_version_tuple() -> Tuple[int, int, int]: return [int(value) for value in get_version_string().split(".")]

def get_version_bytes() -> bytes: return bytes(get_version_tuple())

def get_installation() -> Tuple[str, str, str]:
	config_file = io_handles.EasyFile(io_handles.FileUtil.root() + "/data/config.homesec", True)
	config_data = io_handles.ConfigFileFormat().from_file(config_file)

	if "successful_install" in config_data.data and config_data.successful_install == "True":
		if "install_type" in config_data.data and "version" in config_data.data and "uuid" in config_data.data:
			return config_data.install_type, config_data.version, config_data.uuid

		failure.die(failure.Installation.No_History, "Cannot read \"install_type\", \"version\", \"uuid\" from config")

	failure.die(failure.Installation.No_History, "Install failed thus HomeSecurity cannot start")

def run_command(command: str) -> str:
	process = subprocess.Popen("/bin/bash", stdin = subprocess.PIPE,\
		stdout = subprocess.PIPE, stderr = subprocess.PIPE,\
		text = True, shell = True)
	return process.communicate(command)[1]

def main(install_type: str, force: bool) -> None:
	config_file_path = io_handles.FileUtil.root() + "/data/config.homesec"
	service_file = "/lib/systemd/system/HomeSecurity.service"
	init_file = "/opt/Firmware/init.sh"
	bluetooth_service_file = "/lib/systemd/system/bluetooth.service"

	if io_handles.FileUtil.does_file_exist(config_file_path) or io_handles.FileUtil.does_file_exist(service_file):
		if not force:
			failure.die(failure.Installation.Previous_Install, "An install already exists")

	if io_handles.FileUtil.delete_file(config_file_path) and io_handles.FileUtil.delete_file(service_file):
		logger.Log("install", "01 / 13 - purged old configs and/or service file if they existed", print = True)



		err = run_command("apt-get -y install libbluetooth-dev")

		if err and len(err):
			failure.die(failure.Installation.Missing_Perms_Package, "Couldn't isntall libbluetooth-dev")
			return

		logger.Log("install", "02 / 10 - installed libbluetooth-dev package for bluetooth support", print = True)



		err = run_command("sdptool add SP")

		if err and len(err):
			failure.die(failure.Installation.Failure, "Failed to add SP as a service, error message:\n" + err)
			return

		logger.Log("install", "03 / 10 - added serial port as a service", print = True)
		


		def write_service(stream: BinaryIO) -> bool:
			try:
				stream.write(b"""[Unit]
Description=HomeSecurity
After=bluetooth.target network.target
Requires=bluetooth.target
StartLimitBurst=3
StartLimitIntervalSec=20

[Service]
WorkingDirectory=/opt/Firmware/
ExecStart=/bin/bash """ + init_file.encode("utf-8") + b"""
Restart=on-failure
RestartSec=3s
#StartLimitAction=reboot
LimitNPROC=1

[Install]
WantedBy=multi-user.target""")
			except IOError:
				return False
			return True

		server_easy_file = io_handles.EasyFile(service_file, True, False)

		if not server_easy_file.can_write or not server_easy_file.get_stream("write", write_service):
			failure.die(failure.Installation.Missing_Perms_Service, "Failed to create HomeSecurity service")

		logger.Log("install", "04 / 10 - wrote service file", print = True)



		def override_bluetooth_service(stream: BinaryIO) -> bool:
			try:
				stream.write(b"""[Unit]
Description=Bluetooth service
Documentation=man:bluetooth(8)
ConditionPathIsDirectory=/sys/class/bluetooth

[Service]
Type=dbus
BusName=org.bluez
ExecStart=/usr/lib/bluetooth/bluetoothd -C
NotifyAccess=main
#WatchdogSec=10
Restart=on-failure
CapabilityBoundingSet=CAP_NET_ADMIN CAP_NET_BIND_SERVICE
LimitNPROC=1
ProtectedHome=true
ProtectSystem=full

[Install]
WantedBy=bluetooth.target
Alias=dbus-org.bluez.service""")
			except IOError:
				return False
			return True

		bluetooth_service_easy_file = io_handles.EasyFile(bluetooth_service_file, True, False)

		if not bluetooth_service_easy_file.can_write or not bluetooth_service_easy_file.get_stream("overwrite", override_bluetooth_service):
			failure.die(failure.Installation.Missing_Perms_Service, "Failed to patch the existing bluetooth service")

		logger.Log("install", "05 / 10 - patched bluetooth service", print = True)



		err = run_command("systemctl daemon-reload")

		if err and len(err):
			failure.die(failure.Installation.Missing_Perms_Service, "Couldn't reload daemon, error message:\n" + err)
			return

		logger.Log("install", "06 / 10 - reloaded daemon after patching and adding services", print = True)



		err = run_command("systemctl restart bluetooth.service")

		if err and len(err):
			failure.die(failure.Installation.Missing_Perms_Service, "Couldn't restart bluetooth service after patch, error message:\n" + err)
			return

		logger.Log("install", "07 / 10 - restarted bluetooth service", print = True)



		err = run_command("systemctl enable HomeSecurity.service")

		if err and len(err) and not err.startswith("Created symlink"):
			failure.die(failure.Installation.Missing_Perms_Service, "Couldn't enable HomeSecurity service, error message:\n" + err)
			return

		logger.Log("install", "08 / 10 - enabled HomeSecurity service so it runs on boot", print = True)



		err = run_command(f"chmod +x {init_file}")

		if err and len(err): # Should basically never fail
			failure.die(failure.Installation.Missing_Perms_File, "Couldn't make the init file executable")
			return

		logger.Log("install", "09 / 10 - Made startup file executable\nTriggering restart after completing installation process successfully", print = True)


		config_file = io_handles.EasyFile(config_file_path, True)
		config_data = io_handles.ConfigFileData()
		config_data.install_type = install_type
		config_data.version = get_current_version()

		def gen_uuid() -> bytes:
			from Crypto.Random import get_random_bytes
			return get_random_bytes(128)

		config_data.uuid = gen_uuid()
		config_data.successful_install = "True"

		io_handles.ConfigFileFormat().save_to(config_file, config_data)



		logger.Log("install", "10 / 10 - wrote config file", print = True)
		logger.Log("install", "If you'd like to cancel the reboot, terminate this process with Ctrl+C within the next 10 seconds", False, True)

		try:
			from time import sleep
			sleep(10)
		except KeyboardInterrupt:
			print("\b\b   \b\b", end="") # Remove ^C from terminal with 2 backspaces, 2 spaces, and then move cursor back 2 characters

			logger.Log("install", "Reboot cancelled, install was successful", False, True)
			failure.die(failure.SystemCode.Success, "Finished installation successfully")
		else:
			from os import system
			failure.die(failure.SystemCode.Success, "Finished installation successfully")
			system("reboot")

	else:
		failure.die(failure.Installation.Missing_Perms_File, "Couldn't delete pre-existing installation config")

import io_handles, failure, logger