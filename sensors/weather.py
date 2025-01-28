#!/usr/bin/python
import threading
from time import sleep
import logging
from logging.handlers import SysLogHandler
import time
import socket
import math
import json
import os
import graphiteQueue
import adafruit
import prometheus_client 
from gpiozero import DigitalInputDevice
import gpiozero
from w1thermsensor import W1ThermSensor
from bme280 import BME280
prometheus_client.REGISTRY.unregister(prometheus_client.GC_COLLECTOR)
prometheus_client.REGISTRY.unregister(prometheus_client.PLATFORM_COLLECTOR)
prometheus_client.REGISTRY.unregister(prometheus_client.PROCESS_COLLECTOR)

try:
    from smbus2 import SMBus
except ImportError:
    from smbus import SMBus

count = 0
RADIUS_CM = 9.0     # Radius of the anemometer
interval = int(os.getenv("INTERVAL", "30"))       # How often to report speed
ADJUSTMENT = 1.18   # Adjustment for weight of cups
CM_IN_A_KM = 100000.0
SECS_IN_AN_HOUR = 3600


class ContextFilter(logging.Filter):
    hostname = os.getenv('BALENA_DEVICE_NAME_AT_INIT', socket.gethostname())

    def filter(self, record):
        record.hostname = ContextFilter.hostname
        return True


logger = logging.getLogger("weather")
level = getattr(logging, os.getenv("LOG_LEVEL","INFO").upper(), 20)
logging.basicConfig(format='%(levelname)s:%(message)s', level=level)

consoleHandler = logging.StreamHandler()
consoleHandler.setLevel(level)
syslog_target = os.getenv('SYSLOG_TARGET', None)

if syslog_target:
    (syslog_host, syslog_port) = syslog_target.split(':')
    syslog = SysLogHandler(address=(syslog_host, int(syslog_port)))
    syslog.addFilter(ContextFilter())
    log_format = '%(asctime)s %(hostname)s weather: %(message)s'
    formatter = logging.Formatter(log_format, datefmt='%b %d %H:%M:%S')
    syslog.setFormatter(formatter)
    logger.addHandler(syslog)
    logger.info('Set up logging')


# Load environment variables
gpio_pin = int(os.getenv("WIND_PIN","22"))
graphite_prefix = os.getenv("GRAPHITE_PREFIX", "weather")
use_bme280 = os.getenv('USE_BME280', 'false').lower() == "true"


def calculate_speed(time_sec, output_file=None):
    global count
    circumference_cm = (2 * math.pi) * RADIUS_CM
    rotations = count / 2.0
    logger.debug("Calculating speed based on {} rotations of {} circumference".format(rotations, circumference_cm))
    dist_km = (circumference_cm * rotations) / CM_IN_A_KM

    km_per_sec = dist_km / time_sec
    km_per_hour = km_per_sec * SECS_IN_AN_HOUR
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as outfile:
            json.dump({
                "sample_time": time.time(),
                "mps": km_per_sec * 1000 * ADJUSTMENT,
                "speed": km_per_hour * ADJUSTMENT
            }, outfile)

    return km_per_hour * ADJUSTMENT


def read_temperature():
    global graphite
    global temperature_gauge
    global a
    try:
        while True:
            summary = ""
            for sensor in W1ThermSensor.get_available_sensors():
                temperature = sensor.get_temperature()
                logger.debug("Sensor %s has temperature %.2f" % (sensor.id, sensor.get_temperature()))
                if temperature-55 and temperature < 125:
                    temperature_gauge.labels(sensor=sensor.id).set(temperature)
                    graphite.stage(sensor.id, temperature)
                    summary += " {}: {} ".format(sensor.id, temperature)
                    a.store('weather.air-temperature', temperature)
                else:
                    logger.info("{} outside of range (-55 - 125): {}".format(sensor.id, temperature))
            if summary != "":
                logger.info("W1: " + summary)
    except KeyboardInterrupt:
        thread.exit()


def spin():
    global count
    count = count + 1
    logger.debug(count)


# Initialise the BME280
if use_bme280:
    try:
        bus = SMBus(1)
        bme280 = BME280(i2c_dev=bus)
        use_bme280 = True
    except IOError:
        logger.warning("BME280 not found, de-activating")


graphite = graphiteQueue.graphite(prefix=graphite_prefix)
a = adafruit.adafruitIO()
prometheus_client.start_http_server(80)
wind_speed_gauge = prometheus_client.Gauge('wind_speed', 'Speed of wind')
temperature_gauge = prometheus_client.Gauge('temperature', 'Temperature', ['sensor'])
humidity_gauge = prometheus_client.Gauge('humidity', 'Humidity')
pressure_gauge = prometheus_client.Gauge('pressure', 'Pressure')

# Set up count function on pulse for anenometer
wind_speed_sensor = DigitalInputDevice(gpio_pin)
wind_speed_sensor.when_activated = spin

temperature = threading.Thread(target=read_temperature)
temperature.start()


previous_metric_count = 0
try:
    while True:
        count = 0
        sleep(interval)
        km_per_hour = calculate_speed(interval)
        logger.info("Wind speed is {} km/h.".format(km_per_hour))
        graphite.stage('wind-speed', km_per_hour)
        a.store('weather.wind-speed', km_per_hour)
        wind_speed_gauge.set(km_per_hour)
        graphite.stage('pi.cpu-temp', gpiozero.CPUTemperature().temperature)
        graphite.stage('pi.disk-usage', gpiozero.DiskUsage().usage)
        graphite.stage('pi.load-average-5m', 
                       gpiozero.LoadAverage().load_average)
        if use_bme280:
            temperature = bme280.get_temperature()
            pressure = bme280.get_pressure()
            humidity = bme280.get_humidity()
            logger.info("BME280 reports temperature: {}, humidity: {}, pressure: {}".format(temperature, humidity, pressure))
            # Set Prometheus gauges
            temperature_gauge.labels(sensor='bme280').set(temperature)
            pressure_gauge.set(pressure)
            humidity_gauge.set(humidity)
            # Send to graphite
            graphite.stage('indoor-temp', temperature)
            graphite.stage('pressure', pressure)
            graphite.stage('humidity', humidity)
        graphite.debug()
        metric_count = graphite.store()
        logger.info("Metrics stored: %d",metric_count)
        if metric_count < previous_metric_count:
            exit()
        previous_metric_count = metric_count
except KeyboardInterrupt:
    temperature.join()
    exit()
