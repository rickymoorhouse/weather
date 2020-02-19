#!/usr/bin/python
from gpiozero import DigitalInputDevice
from w1thermsensor import W1ThermSensor
import threading
from time import sleep
import logging
import time
import socket
import math
import json
import os
try:
    from smbus2 import SMBus
except ImportError:
    from smbus import SMBus
from bme280 import BME280

count = 0
radius_cm = 9.0     # Radius of the anemometer
interval = 5        # How often to report speed
ADJUSTMENT = 1.18   # Adjustment for weight of cups
CM_IN_A_KM = 100000.0
SECS_IN_AN_HOUR = 3600

logger = logging.getLogger("weather")
level = getattr(logging, os.getenv("LOG_LEVEL","INFO").upper(), 20)
logging.basicConfig(format='%(levelname)s:%(message)s', level=level)


consoleHandler = logging.StreamHandler()
consoleHandler.setLevel(level)

temperatures = {"sensors":{}, "sample_time":0}

# Load environment variables
gpio_pin = int(os.getenv("WIND_PIN","22"))
output_file = os.getenv("OUTPUT_FILE_WIND", "/tmp/wind.json")
output_file = os.getenv("OUTPUT_FILE_TEMP", "/tmp/temp.json")
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

def read_temperature():
    global temperatures
    try:
        while True:
            temperatures["sample_time"] = time.time()
            for sensor in W1ThermSensor.get_available_sensors():
                logger.debug("Sensor %s has temperature %.2f" % (sensor.id, sensor.get_temperature()))
                temperatures['sensors'][sensor.id] = sensor.get_temperature()
            with open(output_file, 'w') as outfile:
                json.dump(temperatures, outfile)
    except KeyboardInterrupt:
        thread.exit()


def spin():
    global count
    count = count + 1
    logger.debug(count)


# Initialise the BME280
use_bme280 = False
try:
    bus = SMBus(1)
    bme280 = BME280(i2c_dev=bus)
    use_bme280 = True
except IOError:
    logger.warning("BME280 not found, de-activating")

# Set up count function on pulse for anenometer
wind_speed_sensor = DigitalInputDevice(gpio_pin)
wind_speed_sensor.when_activated = spin

temperature = threading.Thread(target=read_temperature)
temperature.start()



try:
    while True:
        count = 0
        sleep(interval)
        km_per_hour = calculate_speed(interval)
        logger.info("Wind speed is {} km/h. {} temperature readings".format(km_per_hour, len(temperatures['sensors'])))
        logger.debug(temperatures)
        if graphite_host:
            try:
                sock = socket.socket()
                sock.connect( (graphite_host, 2003) )
                sock.send(("%s.wind-speed %f %d \n" % (graphite_prefix, km_per_hour, time.time())).encode())
                logger.debug("%s.wind-speed %f %d \n" % (graphite_prefix, km_per_hour, time.time()))
                if use_bme280:
                    temperature = bme280.get_temperature()
                    pressure = bme280.get_pressure()
                    humidity = bme280.get_humidity()
                    logger.info("BME280 reports temperature: {}, humidity: {}, pressure: {}".format(temperature, humidity, pressure))
                    sock.send(("%s.indoor-temp %f %d \n" % (graphite_prefix, temperature, time.time())).encode())
                    sock.send(("%s.pressure %f %d \n" % (graphite_prefix, pressure, time.time())).encode())
                    sock.send(("%s.humidity %f %d \n" % (graphite_prefix, humidity, time.time())).encode())
                for sensor in temperatures['sensors']:
                    if temperatures['sensors'][sensor]>-55 and temperatures['sensors'][sensor] < 125:
                        sock.send(("%s.%s %f %d \n" % (graphite_prefix, sensor, temperatures['sensors'][sensor], time.time())).encode())
                        logger.debug("%s.%s %f %d \n" % (graphite_prefix, sensor, km_per_hour, time.time()))                        
                    else:
                        logger.info("outside of range (-55 - 125): {}".format(temperatures['sensors'][sensor]))
                sock.close()
            except socket.error:
                logger.error("Failed to send data to graphite")
except KeyboardInterrupt:
    temperature.join()
    exit()
