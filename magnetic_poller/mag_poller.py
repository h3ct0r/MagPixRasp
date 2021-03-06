#!/usr/bin/python

import re
import time
import numpy
import serial
from collections import deque
from threading import Thread


class MagPoller(Thread):
    def __init__(self, device="/dev/ttyUSB0", is_continuous=True, window_size=5, debug=True):
        self.ser = serial.Serial(device, 9600)
        if self.ser is None:
            print "[MAG] Magnetometer is not connected!"
        else:
            print "[MAG] Magnetometer is connected..."

        if is_continuous:
            self.window_size = window_size
        else:
            self.window_size = 1

        self.is_debug = debug

        self.X = deque()
        self.Y = deque()
        self.Z = deque()
        self.T = deque()
        self.Temp = deque()

        self.is_running = True
        self.is_stopped = False
        Thread.__init__(self)
    
    def get_values(self):
        return numpy.array([
            MagPoller.get_avg_deque(self.X),
            MagPoller.get_avg_deque(self.Y),
            MagPoller.get_avg_deque(self.Z),
            MagPoller.get_avg_deque(self.T),
            MagPoller.get_avg_deque(self.Temp)])
        
    def run(self):
        while self.is_running:
            serial_line = self.ser.readline()
            self.parser(serial_line)
        self.is_stopped = True
        
    def parser(self, line):
        l_clean = ''.join([x for x in line if ord(x) < 128])
        l_clean = re.split("\s+", l_clean)
        l_clean = [re.sub("\s|;", "", elem).translate(None, '\x00') for elem in l_clean]
        
        if len(l_clean) == 11:
            try:
                self.add_elem_to_deque(self.X, float(l_clean[1]))
                self.add_elem_to_deque(self.Y, float(l_clean[3]))
                self.add_elem_to_deque(self.Z, float(l_clean[5]))
                self.add_elem_to_deque(self.T, float(l_clean[7]))
                self.add_elem_to_deque(self.Temp, float(l_clean[9]))

                if self.is_debug:
                    print '[MAG]', 'Updated mag values ...'
                    print '[MAG]', 'Values:', self.get_values()
                    print '[MAG]', 'Length: X:{0}, Y:{1}, Z:{2}, T:{3}'.format(
                        len(self.X), len(self.Y), len(self.Z), len(self.T))
            except Exception as e:
                print '[MAG] [ERROR]', e, l_clean, 'Original input:', line
                pass

    def add_elem_to_deque(self, d, v):
        d.append(v)
        if len(d) > self.window_size:
            d.popleft()
        pass

    @staticmethod
    def get_avg_deque(d):
        return sum(d) / float(len(d))
  
    def stop(self):
        self.is_running = False
            
    def close(self):
        while not self.is_stopped:
            pass
        self.ser.close()
        print '[MAG] [ERROR] Serial port closed!'


if __name__ == "__main__":
    m = MagPoller()
    m.start()
    for i in range(10):
        print m.get_values()
        time.sleep(0.5)
    m.stop()
    m.close()
