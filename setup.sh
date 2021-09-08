#!/bin/bash

# Check for root privileges
if (( EUID != 0 ))
then
	echo "This installer must be ran with sudo or as root" 1>&2
	exit 1
fi

InstallFolder=/opt/

apt-get update
apt-get -y upgrade

apt-get -y install python3 python3-pip git

cd /tmp/

git clone https://github.com/5Dev24/HomeSecurity

mv /tmp/HomeSecurity/src/Firmware $InstallFolder

pip3 install -r $InstallFolder/requirements.txt

python3 $InstallFolder/__main__.py --aided