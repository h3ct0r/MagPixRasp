##########################################
#!/usr/bin/env python
# -*- coding: utf-8 -*-
##########################################
#
#  __  __             ____  _      ____
# |  \/  | __ _  __ _|  _ \(_)_  _|  _ \ __ _ ___ _ __
# | |\/| |/ _` |/ _` | |_) | \ \/ / |_) / _` / __| '_ \
# | |  | | (_| | (_| |  __/| |>  <|  _ < (_| \__ \ |_) |
# |_|  |_|\__,_|\__, |_|   |_/_/\_\_| \_\__,_|___/ .__/
#               |___/                            |_|
#
# Authors:
#   - Hector Azpurua
#   - Paulo Rezeck
#
# Changelog:
# - 24 OCT :
#    * Changed system arquitecture, now is more modular!
#    * Support for continuous and cam_trigger modes
# - 28 SEP :
#   changed sampling to 10 measurements per trigger
# - 29 SEP :
#   fixed bug when selecting max int on a string

import signal
import sys
import RPi.GPIO as GPIO
import pigpio # http://abyz.co.uk/rpi/pigpio/python.html
import time
import argparse

from cam_trigger.poller_main import PollerCamTrigger
from continuous.poller_main import PollerContinuous

pi = None
p1 = None


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


def main():
    global pi
    global p1

    parser = argparse.ArgumentParser()
    parser.add_argument('--continuous', dest='continuous', action='store_true')
    parser.add_argument('--trigger_pin', type=int, default=17)
    parser.add_argument('--mag', default='/dev/ttyUSB0')
    parser.add_argument('--pixhawk', default='/dev/ttyAMA0')
    parser.add_argument('--output', default='/home/pi/Documents/sensor_readings/')

    parser.set_defaults(feature=True)
    args = parser.parse_args()

    #signal.signal(signal.SIGINT, signal_handler)

    print '[MAIN]', 'Using output:', args.output
    print '[MAIN]', 'Using pixhawk device:', args.pixhawk
    print '[MAIN]', 'Using magnetic device:', args.mag

    try:
        if args.continuous:
            print '[MAIN]', 'Using CONTINUOUS MODE'
            p1 = PollerContinuous(args.mag, args.pixhawk, args.output)
        else:
            print '[MAIN]', 'Using CAM_TRIGGER MODE'
            print '[MAIN]', 'Using GPIO port for camera trigger:', args.trigger_pin
            print '[MAIN]', 'Starting input logger...'

            pi = pigpio.pi()
            p1 = PollerCamTrigger(pi, args.trigger_pin, args.mag, args.pixhawk, args.output)

        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        GPIO.cleanup()
        if pi and p1:
            print '[MAIN] cancelling poll...'
            p1.cancel()
            pi.stop()
            print '[MAIN] poll cancelled!...'
        elif p1:
            print '[MAIN] cancelling poll...'
            p1.cancel()
            print '[MAIN] poll cancelled!...'

        elif pi:
            print '[MAIN] cancelling poll...'
            pi.stop()
            print '[MAIN] poll cancelled!...'

if __name__ == "__main__":
    main()
