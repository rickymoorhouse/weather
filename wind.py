#!/usr/bin/python
from gpiozero import DigitalInputDevice
from time import sleep
import logging
import time
import socket
import math
import json
import os


count = 0
radius_cm = 9.0     # Radius of the anemometer
interval = 5        # How often to report speed
ADJUSTMENT = 1.18   # Adjustment for weight of cups
CM_IN_A_KM = 100000.0
SECS_IN_AN_HOUR = 3600

logger = logging.getLogger("wind-speed")
level = getattr(logging, os.getenv("LOG_LEVEL","INFO").upper(), 20)
logging.basicConfig(format='%(levelname)s:%(message)s', level=level)

consoleHandler = logging.StreamHandler()
consoleHandler.setLevel(level)

# Load environment variables
gpio_pin = int(os.getenv("WIND_PIN","22"))
output_file = os.getenv("OUTPUT_FILE", "/tmp/wind.json")
graphite_host = os.getenv("GRAPHITE_HOST", None)
graphite_prefix = os.getenv("GRAPHITE_PREFIX", "weather")

def calculate_speed(time_sec):
    global count
    circumference_cm = (2 * math.pi) * radius_cm
    rotations = count / 2.0

    dist_km = (circumference_cm * rotations) / CM_IN_A_KM

    km_per_sec = dist_km / time_sec
    km_per_hour = km_per_sec * SECS_IN_AN_HOUR
    with open(output_file, 'w') as outfile:
        json.dump({
            "sample_time":time.time(), 
            "mps":km_per_sec * 1000 * ADJUSTMENT,
            "speed":km_per_hour * ADJUSTMENT
        }, outfile)

    return km_per_hour * ADJUSTMENT

def spin():
    global count
    count = count + 1
    logger.debug(count)

wind_speed_sensor = DigitalInputDevice(gpio_pin)
wind_speed_sensor.when_activated = spin

while True:
    count = 0
    sleep(interval)
    km_per_hour = calculate_speed(interval)
    if graphite_host:
        try:
            sock = socket.socket()
            sock.connect( (graphite_host, 2003) )
            sock.send(("%s.wind-speed %f %d \n" % (graphite_prefix, km_per_hour, time.time())).encode())
            logger.debug("%s.wind-speed %f %d \n" % (graphite_prefix, km_per_hour, time.time()))
            sock.close()
        except socket.error:
            logger.error("Failed to send data to graphite")
