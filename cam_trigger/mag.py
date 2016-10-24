#!/usr/bin/python

import serial, time
from threading import Thread
import re, numpy

class Mag(Thread):
    def __init__(self, port="/dev/ttyUSB0"):
        self.ser = serial.Serial(port, 9600)
        if self.ser is None:
            print "Magnetometer is not connected!"
        else:
            print "Magnetometer is connected..."
        self.X = 0.0
        self.Y = 0.0
        self.Z = 0.0
        self.T = 0.0
        self.Temp = 0
        self.is_running = True
        self.is_stopped = False
        Thread.__init__(self)

    def read(self):
        serial_line = self.ser.readline()
        self.parser(serial_line)
        return numpy.array([self.X, self.Y, self.Z, self.T, self.Temp])
    
    def get(self):
        return numpy.array([self.X, self.Y, self.Z, self.T, self.Temp])
        
    def run(self):
        while self.is_running:
            serial_line = self.ser.readline()
            self.parser(serial_line)
        self.is_stopped = True
        
    def parser(self, line):
        l_clean =  ''.join([x for x in line if ord(x) < 128])
        l_clean = re.split("\s+", l_clean)
        l_clean = [re.sub("\s|;", "", elem).translate(None, '\x00') for elem in l_clean]
        
        if(len(l_clean) == 11):
            try:
                self.X = float(l_clean[1])
                self.Y = float(l_clean[3])
                self.Z = float(l_clean[5])
                self.T = float(l_clean[7])
                self.Temp = float(l_clean[9])
            except Exception as e: 
                self.X = 0
                self.Y = 0
                self.Z = 0
                self.T = 0
                self.Temp = 0

                print '[ERROR]', e, l_clean, 'Original input:', line
  
    def stop(self):
        self.is_running = False
            
    def close(self):
        while not self.is_stopped:
            pass
        self.ser.close()
        print 'Serial port closed!'
        
#m = Mag()
#m.start()
#for i in range(10):
#    print m.get()
#    time.sleep(0.5)
#m.stop()
#m.close()
