#!/usr/bin/env python
# -*- coding: utf-8 -*-

#from dronekit import connect, VehicleMode
import dronekit
import time, sys
#from threading import Thread

class GpsGetter():
    def __init__ (self, usb_dev):
        #Thread.__init__(self)

        self.usb_dev = usb_dev
        self.vehicle = None
        self.lat = 0
        self.lon = 0
        self.alt = 0
        self.last_global_frame_cache = None

    def get_vehicle(self):
        return self.vehicle

    def connect(self):
        print "[GPS] Connecting to vehicle on: %s" % self.usb_dev
        self.vehicle = dronekit.connect(self.usb_dev, wait_ready=True, baud=57600)
        self.vehicle.wait_ready('autopilot_version')
        print "[GPS] Connection ready!"
        self.vehicle.add_attribute_listener('location', self.location_callback)
        print "[GPS] Listener defined!"
        
    def location_callback(self, vehicle, name, location):
        # `attr_name` - the observed attribute (used if callback is used for multiple attributes)
        # `self` - the associated vehicle object (used if a callback is different for multiple vehicles)
        # `value` is the updated attribute value.

        if location.global_frame != self.last_global_frame_cache:
            #print "[GPS] CALLBACK: Global frame changed to:", location.global_frame
            self.lat = location.global_frame.lat
            self.lon = location.global_frame.lon
            self.alt = location.global_frame.alt
            self.last_global_frame_cache = location.global_frame

    def get_pos(self):
        return self.lat, self.lon


#gps = GpsGetter("/dev/ttyAMA0")
#gps.connect()

#while True:
#    pos = gps.get_pos()
#    if pos[0] != None:
#        print "------------->", gps.get_pos()
#    
#    time.sleep(0.5)
