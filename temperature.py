from w1thermsensor import W1ThermSensor
import json
import time

data = {"sample_time":time.time()}
for sensor in W1ThermSensor.get_available_sensors():
    #print("Sensor %s has temperature %.2f" % (sensor.id, sensor.get_temperature()))
    data[sensor.id] = sensor.get_temperature()
with open('/var/www/html/temperature.json', 'w') as outfile:
    json.dump(data, outfile)

