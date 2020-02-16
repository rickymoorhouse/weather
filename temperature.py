from w1thermsensor import W1ThermSensor
import json
import logging
import time
import os
import socket

logger = logging.getLogger("temperature")

graphite_host = os.getenv("GRAPHITE_HOST", None)
graphite_prefix = os.getenv("GRAPHITE_PREFIX", "weather")
output_file = os.getenv("OUTPUT_FILE", "/tmp/temperature.json")


data = {"sample_time":time.time()}
for sensor in W1ThermSensor.get_available_sensors():
    logger.debug("Sensor %s has temperature %.2f" % (sensor.id, sensor.get_temperature()))
    data[sensor.id] = sensor.get_temperature()
with open(output_file, 'w') as outfile:
    json.dump(data, outfile)
try:
    sock = socket.socket()
    sock.connect( (graphite_host, 2003) )

    if data['0316453f4eff']>-55 and data['0316453f4eff'] < 125:
        sock.send("%s.soil-temp %f %d \n" % (graphite_prefix, data['0316453f4eff'], time.time()))
    else:
        logger.info("outside of range (-55 - 125): {}".format(data['0316453f4eff']))

    if data['041643cebdff']>-55 and data['041643cebdff'] < 125:
        sock.send("%s.air-temp %f %d \n" % (graphite_prefix, data['041643cebdff'], time.time()))
    else:
        logger.info("outside of range (-55 - 125): {}".format(data['041643cebdff']))
    sock.close()
except socket.error:
    logger.error("Failed to send data to graphite")

