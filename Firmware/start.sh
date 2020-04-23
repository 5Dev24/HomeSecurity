cd /home/pi/ISM-2019-2020/Firmware/
sudo hciconfig hci0 piscan
echo "Waiting 5 seconds to let bluetooth start properly"
sleep 5s
sudo python3 ./__main__.py $*
Out=$?
echo Process exited with code "$Out"