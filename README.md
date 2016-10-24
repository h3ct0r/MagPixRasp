# MagPixRasp

Raspberry Pi script to log magnetic data at cam triggers from a Pixhawk.
This script is executed inside a Raspberry Pi 2 mounted on a X8+ drone from 3DR.
A magnetic sensor that communicates via


## Install modules

pip install pyusb
pip install pyserial
sudo apt-get install python-dev
pip install dronekit
pip install MAVProxy

## Usage

Connect the Rpi to the Pixhawk using the GpIO ports as seen on: http://ardupilot.org/dev/docs/raspberry-pi-via-mavlink.html

## Crontab

Execute those commands:

	$ sudo su
	# crontab -e

And add this on your root crontab:    
    
`@reboot         /usr/bin/python /home/pi/Documents/magsensor/cam_trigger/PWM_gather_gps.py > /tmp/mag_log.log &`
