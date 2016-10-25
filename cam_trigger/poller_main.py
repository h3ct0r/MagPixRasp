##########################################
#!/usr/bin/env python
# -*- coding: utf-8 -*-
##########################################

import calendar
import datetime
import glob
import os
import threading
import time

import RPi.GPIO as GPIO
import pigpio # http://abyz.co.uk/rpi/pigpio/python.html

from magnetic_poller.mag_poller import MagPoller
from pixhawk.get_drone_gps import GpsGetter


class PollerCamTrigger:
    def __init__(self, pi, gpio, mag_path, usb_path, output_location):
        """
        Init
        :param pi:
        :param gpio:
        :param mag_path:
        :param usb_path:
        """
        self.finish = False
        self.gps = None
        self.mag = None

        self.pi = pi
        self.gpio = gpio

        self.usb_path = usb_path
        self.mag_path = mag_path
        self.output_location = output_location
        self.filename = ''

        self._high_tick = None
        self._p = None
        self._hp = None

        self.wp_index = 0

        self.led1 = 18
        self.led2 = 24

        self.num_samples = 10  # number of samples per trigger
        self.cooldown_seconds = 0.5
        self.dc_trigger = False

        self.define_log()
        self.init_leds()
        self.init_usb_connections()
        self._cb = self.pi.callback(gpio, pigpio.EITHER_EDGE, self._cbf)

        while not self.finish:
            time.sleep(0.01)
            pass

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

    def init_usb_connections(self):
        """
        Start usb connections with the Pixhawk and Mag
        :return:
        """
        print '[MAG] Starting gps getter...'
        self.gps = GpsGetter(self.usb_path)
        self.gps.connect()
        print '[MAG] Gps OK'

        print '[MAG] Starting magnetometer getter...'
        self.mag = MagPoller(device=self.mag_path, is_continuous=False)
        self.mag.start()
        time.sleep(1)
        print '[MAG] Magnetometer OK'

    def define_log(self):
        """
        Define new log file filename
        :return:
        """
        files = [os.path.basename(x) for x in glob.glob(self.output_location + "*.txt")]

        exp_size = 0
        if len(files) > 0:
            exp_size = max([int(f.split('.')[0]) for f in files])

        self.filename = self.output_location + str(exp_size + 1) + ".exp_cam_trigger." + \
                        str(datetime.datetime.now().strftime("%Y%m%d.%H%M%S")) + ".txt"

        print '[SENSOR] Log file:', self.filename

        file_ = open(self.filename, 'a')
        file_.write("Waypoint;Timestamp;X;Y;Z;T;t;Lat;Lng;Alt\n")
        file_.close()

    def log_mag_info(self):
        time.sleep(self.cooldown_seconds)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.led1, GPIO.OUT)
        GPIO.setup(self.led2, GPIO.OUT)

        GPIO.output(self.led2, GPIO.LOW)
        GPIO.output(self.led1, GPIO.HIGH)

        print "[MAG] Trigger registered, taking samples..."
        file_ = open(self.filename, 'a')
        pos = self.gps.get_pos()
        timestamp = calendar.timegm(time.gmtime())

        for i in xrange(self.num_samples):
            v = self.mag.get_values()
            line = str(self.wp_index) + ";" + str(timestamp) + ";" + str(v[0]) + ";" + str(v[1]) + ";" + str(v[2]) + ";" + str(v[3]) + ";" + str(v[4]) + ";" + str(pos[0]) +";"+ str(pos[1])+ "\n"
            file_.write(line)
            time.sleep(0.2)
            pass

        self.wp_index += 1
        file_.close()
        
        print '[MAG] Recorded', self.num_samples, 'samples at:', pos
        print '[MAG] Cool down... (', self.cooldown_seconds, ')'

        file_.close()
        
        GPIO.output(self.led1, GPIO.LOW)
        GPIO.output(self.led2, GPIO.HIGH)
        print '\n\n[MAG] Ready for new trigger!\n\n'

    def _cbf(self, gpio, level, tick):
        if level == 1:
            if self._high_tick is not None:
                self._p = pigpio.tickDiff(self._high_tick, tick)
            self._high_tick = tick
                
        elif level == 0:
            if self._high_tick is not None:
                self._hp = pigpio.tickDiff(self._high_tick, tick)

        if (self._p is not None) and (self._hp is not None):
            g = gpio
            f = 1000000.0/self._p
            dc = 100.0 * self._hp/self._p
            #print("[DEBUG] g={} f={:.1f} dc={:.1f}".format(g, f, dc))

            if dc > 9:
                if not self.dc_trigger:
                    thr = threading.Thread(target=self.log_mag_info, args=(), kwargs={})
                    thr.start()
                    #print '[MAG] RESULT:', result
                    self.dc_trigger = True
            else:
                self.dc_trigger = False

    def cancel(self):
        self.finish = True
        GPIO.output(self.led2, GPIO.LOW)
        GPIO.cleanup()
        self._cb.cancel()
        self.mag.stop()
        self.mag.close()

if __name__ == "__main__":
    camTrigger = 17

    print '[MAG] Using GPIO port:', camTrigger
    print '[MAG] Starting input logger...'

    pi = pigpio.pi()
    p1 = PollerCamTrigger(pi, camTrigger, "/dev/ttyAMA0")
