#!/bin/bash

# Check for sudo privileges
if (( EUID != 0 ))
then
	echo "This installer must be ran with sudo" 1>&2
	exit 1
fi

# Declare variables
ServiceFile=/lib/systemd/system/ISM-2019-2020.service
StartFile=/home/pi/ISM-2019-2020/Firmware/start.sh
DataFolder=/home/pi/ISM-2019-2020/Firmware/data/

# Update system
apt update
apt -y upgrade

# Make sure python 3.x is installed
apt -y install python3

# Install pip so we can install requirements
apt -y install python3-pip

# Install pybluez linux dependancies
apt -y install pkg-config libboost-python-dev libboost-thread-dev libbluetooth-dev libglib2.0-dev python-dev

# Install firmware's modules
pip3 install -r /home/pi/ISM-2019-2020/Firmware/requirements.txt

# Clear up excess packages
apt -y autoremove

# Get if this is a server or a client
echo "Is this a server installation?"

read -p "[Y/N]: " ServerInstall
while [ "${ServerInstall,,}" != "y" ] && [ "${ServerInstall,,}" != "n" ]
do
	read -p "[Y/N]: " ServerInstall
done

case "${ServerInstall,,}" in
	"y") ServerInstall="true";;
	"n") ServerInstall="false";;
esac

# Check if service file exists, if it does: delete it
if [ -f "$ServiceFile" ]
then
	chmod 777 "$ServiceFile"
	rm -f "$ServiceFile"
fi

# Create service file
touch "$ServiceFile"

# Allow all access
chmod 777 "$ServiceFile"

# Write to file
echo "[Unit]
Description=ISM-2019-2020

[Service]
ExecStart=/bin/bash $StartFile -server $ServerInstall

[Install]
WantedBy=multi-user.target">> "$ServiceFile"

# Set permissions back
chmod 644 "$ServiceFile"

# Tell systemd to start during boot
systemctl daemon-reload
systemctl enable ISM-2019-2020.service

# Get new device id
DeviceID="$(cat /sys/class/net/eth0/address)"

# Delete old data folder
rm -rf "$DataFolder"

# Create data folder
mkdir "$DataFolder"

# Make start.sh file executable
chmod +x "$StartFile"

# Start start.sh
$StartFile --install -id \'$DeviceID\' -server $ServerInstall

# Restart system
reboot