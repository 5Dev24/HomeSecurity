sudo hciconfig hci0 piscan
sleep 5

sudo python3 ./__main__.py $*
echo HomeSecurity terminated with exit code "$?"