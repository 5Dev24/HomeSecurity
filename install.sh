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
BluetoothService=/lib/systemd/system/bluetooth.service

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

# Allow all access
touch "$ServiceFile"
chmod 777 "$ServiceFile"

# Write to file
echo "[Unit]
Description=ISM-2019-2020

[Service]
ExecStart=/bin/bash $StartFile

[Install]
WantedBy=multi-user.target">> "$ServiceFile"

# Set permissions back
chmod 644 "$ServiceFile"

# Start Bluez patch
if [ -f "$BluetoothService" ]
then
	chmod 777 "$BluetoothService"
	rm -f "$BluetoothService"
fi

touch "$BluetoothService"
chmod 777 "$BluetoothService"

echo "[Unit]
Description=Bluetooth service
Documentation=man:bluetooth(8)
ConditionPathIsDirectory=/sys/class/bluetooth

[Service]
Type=dbus
BusName=org.bluez
ExecStart=/usr/lib/bluetooth/bluetooth --compat --noplugin=sap
NotifyAccess=main
#WatchdogSec=10
#Restart=on-failure
CapabilityBoundingSet=CAP_NET_ADMIN CAP_NET_BIND_SERVICE
LimitNPROC=1
ProtectHome=true
ProtectSystem=full

[Install]
WantedBy=bluetooth.target
Alias=dbus-org.bluez.service
">> "$BluetoothService"

chmod 644 "$BluetoothService"
# End Bluez Patch

# Tell systemd to start during boot
systemctl daemon-reload
systemctl restart bluetooth.service
systemctl enable ISM-2019-2020.service

# Get new device id
DeviceMAC="$(cat /sys/class/net/wlan0/address)"

# Delete old data folder
rm -rf "$DataFolder"

# Create data folder
mkdir "$DataFolder"

# Make start.sh file executable
chmod +x "$StartFile"

# Start start.sh
$StartFile --install -mac \'$DeviceMAC\' -server $ServerInstall

# Restart system
reboot