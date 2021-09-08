cd $(dirname $(readlink -f $0))/src/Firmware/
rsync -auv --exclude="logs/" --exclude="data/" --exclude="__pycache__/" $(pwd) pi@raspberrypi.local:/opt/