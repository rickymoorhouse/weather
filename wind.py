from gpiozero import DigitalInputDevice
from time import sleep
import time
import math
import json


count = 0
radius_cm = 9.0     # Radius of the anemometer
interval = 5        # How often to report speed
ADJUSTMENT = 1.18   # Adjustment for weight of cups
CM_IN_A_KM = 100000.0
SECS_IN_AN_HOUR = 3600

DEBUG = False

def calculate_speed(time_sec):
    global count
    circumference_cm = (2 * math.pi) * radius_cm
    rotations = count / 2.0

    dist_km = (circumference_cm * rotations) / CM_IN_A_KM

    km_per_sec = dist_km / time_sec
    km_per_hour = km_per_sec * SECS_IN_AN_HOUR
    with open('/var/www/html/wind.json', 'w') as outfile:
        json.dump({"sample_time":time.time(), "speed":km_per_hour * ADJUSTMENT}, outfile)

    return km_per_hour * ADJUSTMENT

def spin():
    global count
    count = count + 1
    if DEBUG:
        print (count)

wind_speed_sensor = DigitalInputDevice(22)
wind_speed_sensor.when_activated = spin

while True:
    count = 0
    sleep(interval)
    calculate_speed(interval)
