##########################################
#!/usr/bin/env python
# -*- coding: utf-8 -*-
##########################################

import calendar
import datetime
import glob
import os
import time
import RPi.GPIO as GPIO

from magnetic_poller.mag_poller import MagPoller
from pixhawk.get_drone_gps import GpsGetter


class PollerContinuous:
    def __init__(self, mag_path, usb_path, output_location):
        """
        Init
        :param mag_path:
        :param usb_path:
        :param output_location:
        """
        self.finish = False
        self.gps = None
        self.mag = None

        self.usb_path = usb_path
        self.mag_path = mag_path
        self.output_location = output_location
        self.filename = ''
        self.data_index = 0

        self.led1 = 18
        self.led2 = 24

        self.cooldown_time = 1.5

        self.define_log()
        self.init_leds()
        self.init_usb_connections()
        self.start()
        self.cancel()

    def init_leds(self):
        """
        Initialize the leds on the Rpi
        :return:
        """
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.led1, GPIO.OUT)
        GPIO.setup(self.led2, GPIO.OUT)
        GPIO.output(self.led2, GPIO.HIGH)

    def define_log(self):
        """
        Define new log file filename
        :return:
        """
        files = [os.path.basename(x) for x in glob.glob(self.output_location + "*.txt")]

        exp_size = 0
        if len(files) > 0:
            exp_size = max([int(f.split('.')[0]) for f in files])

        self.filename = self.output_location + str(exp_size + 1) + ".exp_continuous." + \
                        str(datetime.datetime.now().strftime("%Y%m%d.%H%M%S")) + ".txt"

        print '[POLLER] Log file:', self.filename

        file_ = open(self.filename, 'a')
        file_.write("Waypoint;Timestamp;X;Y;Z;T;t;Lat;Lng;Alt\n")
        file_.close()

    def start(self):
        """
        Start polling GPS and MAG data, and save at cooldown_time intervals
        :return:
        """
        while not self.finish:
            self.acquire_mag_info()
            time.sleep(self.cooldown_time)
            pass

    def init_usb_connections(self):
        """
        Start usb connections with the Pixhawk and Mag
        :return:
        """
        print '[POLLER] Starting gps getter...'
        self.gps = GpsGetter(self.usb_path)
        self.gps.connect()
        print '[POLLER] Gps OK'

        print '[POLLER] Starting magnetometer getter...'
        self.mag = MagPoller(device=self.mag_path, is_continuous=True)
        self.mag.start()
        time.sleep(1)
        print '[POLLER] Magnetometer OK'

    def acquire_mag_info(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.led1, GPIO.OUT)
        GPIO.setup(self.led2, GPIO.OUT)

        GPIO.output(self.led2, GPIO.LOW)
        GPIO.output(self.led1, GPIO.HIGH)

        print "[POLLER] Taking sample..."
        file_ = open(self.filename, 'a')

        pos = self.gps.get_pos()
        alt = self.gps.get_alt()
        timestamp = calendar.timegm(time.gmtime())

        v = self.mag.get()
        line = "{0};{1};{2};{3};{4};{5};{6};{7};{8};{9};\n".format(
            self.data_index, timestamp, v[0], v[1], v[2], v[3], v[4], pos[0], pos[1], alt)
        file_.write(line)

        self.data_index += 1
        file_.close()
        
        print '[POLLER] Recorded sample at:', pos, 'alt:', alt

        file_.close()
        GPIO.output(self.led2, GPIO.HIGH)
        GPIO.output(self.led1, GPIO.LOW)

        print '\n\n[POLLER] Ready for new trigger!\n\n'

    def cancel(self):
        self.finish = True
        self.mag.stop()
        self.mag.close()

if __name__ == "__main__":
    print '[MAIN] Starting input logger...'
    p1 = PollerContinuous('/dev/tty/USB0', '/dev/ttyAMA0', '/home/pi/Documents/sensor_readings/')
