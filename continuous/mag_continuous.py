#!/usr/bin/python

import serial, time
from threading import Thread
import re, numpy
from collections import deque

class MagContinuous(Thread):
    def __init__(self, port="/dev/ttyUSB0"):
        self.ser = serial.Serial(port, 9600)
        if self.ser is None:
            print "[MAG] Magnetometer is not connected!"
        else:
            print "[MAG] Magnetometer is connected..."

        self.window_size = 5

        self.X = deque()
        self.Y = deque()
        self.Z = deque()
        self.T = deque()
        self.Temp = deque()

        self.is_running = True
        self.is_stopped = False
        Thread.__init__(self)
    
    def get(self):
        return numpy.array([
            Mag.get_avg_deque(self.X),
            Mag.get_avg_deque(self.Y),
            Mag.get_avg_deque(self.Z),
            Mag.get_avg_deque(self.T),
            Mag.get_avg_deque(self.Temp)])
        
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
                print '[MAG]', 'Updated mag values ...'
                print '[MAG]', 'X:', len(self.X), 'Y:', len(self.Y), 'Z:', len(self.Z), 'T:', len(self.T)
            except Exception as e:
                print '[ERROR]', e, l_clean, 'Original input:', line
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
        print 'Serial port closed!'


if __name__ == "__main__":
    m = Mag()
    m.start()
    for i in range(10):
       print m.get()
       time.sleep(0.5)
    m.stop()
    m.close()
