##########################################
#!/usr/bin/env python
# -*- coding: utf-8 -*-
##########################################

#from multiprocessing import Pool
# CHANGELOG:
# - 28 SEP - changed sampling to 10 measurements per trigger
# - 29 SEP - fixed bug when selecting max int on a string

import sys
import RPi.GPIO as GPIO
import os, sys, numpy, glob
import time, calendar
import argparse
import datetime
import signal
from mag import Mag
import time
import pigpio # http://abyz.co.uk/rpi/pigpio/python.html
import threading


sys.path.insert(0, '../')
from get_drone_gps import GpsGetter


def signal_handler(signal, frame):
    global pi, p1

    print '[MAG] sig received, ', pi, p1

    if pi != None and p1 != None:
        print '[MAG] cancelling poll...'
        p1.cancel()
        pi.stop()
        print '[MAG] poll cancelled!...'
        print '[MAG] Exiting!'
        sys.exit(0)
    elif p1 != None:
        print '[MAG] cancelling poll...'
        p1.cancel()
        print '[MAG] poll cancelled!...'

    elif pi != None:
        print '[MAG] cancelling poll...'
        pi.stop()
        print '[MAG] poll cancelled!...'
        
    sys.exit(1)
    print '[MAG] sighandler received but no GPIO has been defined, please kill by PID'

class PWM_read:
    def __init__(self, pi, gpio, usb_path):
        self.pi = pi
        self.gpio = gpio
        self.finish = False

        self._high_tick = None
        self._p = None
        self._hp = None
        
        self.usb_path = usb_path
        files = [os.path.basename(x) for x in glob.glob("/home/pi/Documents/sensor_readings/*.txt")]
        print files
        if files == []:
            exps = 0
        else:
            exps = max([int(file.split('.')[0]) for file in files])
        self.filename = '/home/pi/Documents/sensor_readings/' + str(exps+1) +".exp." + str(datetime.datetime.now().strftime("%Y%m%d.%H%M%S")) + ".txt"
        self.wp_index = 0
        print self.filename
        file_ = open(self.filename, 'a')
        file_.write("Waypoint;Timestamp;X;Y;Z;T;t;Lat;Lng\n")
        file_.close()

        self.led1 = 18
        self.led2 = 24

        self.num_samples = 10 # number of samples per trigger
        self.cooldown_seconds = 2 # seconds to wait for the next trigger

        self.init_usb_connections()

        self._cb = self.pi.callback(gpio, pigpio.EITHER_EDGE, self._cbf)
        
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.led1, GPIO.OUT)
        GPIO.setup(self.led2, GPIO.OUT)
        GPIO.output(self.led2, GPIO.HIGH)
        
        self.dc_trigger = False

        while not self.finish:
            time.sleep(0.01)
            pass

        self.cancel()

    def init_usb_connections(self):
        print '[MAG] Starting gps getter...'
        self.gps = GpsGetter(self.usb_path)
        self.gps.connect()
        print '[MAG] Gps OK'

        print '[MAG] Starting magnetometer getter...'
        self.mag = Mag()
        self.mag.start()
        time.sleep(1)
        print '[MAG] Magnetometer OK'

    def log_mag_info(self):
        time.sleep(self.cooldown_seconds)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.led1, GPIO.OUT)
        GPIO.output(self.led1, GPIO.HIGH)
        print "[MAG] Trigger registered, taking samples..."
        file_ = open(self.filename, 'a')
        #v = numpy.array([0.0, 0.0, 0.0, 0.0, 0.0])
        pos = self.gps.get_pos()
        timestamp = calendar.timegm(time.gmtime())

        for i in xrange(self.num_samples):
            #v += self.mag.get()
            v = self.mag.get()
            line = str(self.wp_index) + ";" + str(timestamp) + ";" + str(v[0]) + ";" + str(v[1]) + ";" + str(v[2]) + ";" + str(v[3]) + ";" + str(v[4]) + ";" + str(pos[0]) +";"+ str(pos[1])+ "\n"
            file_.write(line)
            time.sleep(0.2)
            pass
        self.wp_index += 1 
        #v = v/float(self.num_samples)
        #line = str(timestamp) + ";" + str(v[0]) + ";" + str(v[1]) + ";" + str(v[2]) + ";" + str(v[3]) + ";" + str(v[4]) + ";" + str(pos[0]) +";"+ str(pos[1])+ "\n"
        #line = str(v[0]) + " " + str(v[1]) + " " + str(v[2]) + " " + str(v[3]) + " " + str(v[4]) + " " + str(pos) + "\n"
        file_.close()
        
        print '[MAG] Recorded', self.num_samples, 'samples at:', pos
        print '[MAG] Cool down... (', self.cooldown_seconds, ')'

        time.sleep(self.cooldown_seconds)
        file_.close()
        
        GPIO.output(self.led1, GPIO.LOW)
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
        self._cb.cancel()
        self.mag.stop()
        self.mag.close()

pi = None
p1 = None

if __name__ == "__main__":
    pi = None
    p1 = None

    camTrigger = 17

    print '[MAG] Using GPIO port:', camTrigger
    print '[MAG] Starting input logger...'

    signal.signal(signal.SIGINT, signal_handler)
    pi = pigpio.pi()
    p1 = PWM_read(pi, camTrigger, "/dev/ttyAMA0")
