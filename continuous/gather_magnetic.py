##########################################
#!/usr/bin/env python
# -*- coding: utf-8 -*-
##########################################

#from multiprocessing import Pool
# CHANGELOG:
# - 28 SEP - changed sampling to 10 measurements per trigger
# - 29 SEP - fixed bug when selecting max int on a string

import RPi.GPIO as GPIO
import os, sys, numpy, glob
import time, calendar
import argparse
import datetime
import signal
from mag_continuous import MagContinuous
import time
import threading

sys.path.insert(0, '../')
from get_drone_gps import GpsGetter


def signal_handler(sig, frame_r):
    global pi, p1

    print '[SIG] sig received, ', pi, p1

    if pi and p1:
        print '[SIG] cancelling poll...'
        p1.cancel()
        pi.stop()
        print '[SIG] poll cancelled!...'
        print '[SIG] Exiting!'
        sys.exit(0)
    elif p1:
        print '[SIG] cancelling poll...'
        p1.cancel()
        print '[SIG] poll cancelled!...'

    elif pi:
        print '[SIG] cancelling poll...'
        pi.stop()
        print '[SIG] poll cancelled!...'
        
    sys.exit(1)


class SensorRead:
    def __init__(self, usb_path, output_location):
        """
        Init
        :param usb_path:
        :param output_location:
        """
        self.finish = False

        self.usb_path = usb_path
        self.output_location = output_location
        self.filename = ""
        self.data_index = 0

        self.define_log()

        self.led1 = 18
        self.led2 = 24

        self.cooldown_time = 1.5

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

        self.filename = '/home/pi/Documents/sensor_readings/' + str(exp_size + 1) + ".exp." + \
                        str(datetime.datetime.now().strftime("%Y%m%d.%H%M%S")) + ".txt"

        print '[SENSOR] Log file:', self.filename

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
        print '[SENSOR] Starting gps getter...'
        self.gps = GpsGetter(self.usb_path)
        self.gps.connect()
        print '[SENSOR] Gps OK'

        print '[SENSOR] Starting magnetometer getter...'
        self.mag = MagContinuous()
        self.mag.start()
        time.sleep(1)
        print '[SENSOR] Magnetometer OK'

    def acquire_mag_info(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.led1, GPIO.OUT)
        GPIO.setup(self.led2, GPIO.OUT)

        GPIO.output(self.led2, GPIO.LOW)
        GPIO.output(self.led1, GPIO.HIGH)

        print "[SENSOR] Taking sample..."
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
        
        print '[SENSOR] Recorded sample at:', pos, 'alt:', alt

        file_.close()
        GPIO.output(self.led2, GPIO.HIGH)
        GPIO.output(self.led1, GPIO.LOW)

        print '\n\n[SENSOR] Ready for new trigger!\n\n'

    def cancel(self):
        self.finish = True
        self.mag.stop()
        self.mag.close()

pi = None
p1 = None

if __name__ == "__main__":
    pi = None
    p1 = None

    camTrigger = 17

    print '[MAIN] Starting input logger...'

    signal.signal(signal.SIGINT, signal_handler)
    p1 = SensorRead("/dev/ttyAMA0", "/home/pi/Documents/sensor_readings/")
