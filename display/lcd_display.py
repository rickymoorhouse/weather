#!/usr/bin/env python

import os
import time
import requests
import json
import datetime
import time
import socket
import dothat.backlight as backlight
import dothat.lcd as lcd
from dothat import touch

lum = 60

SOIL_ID=os.getenv("SOIL_ID")
AIR_ID=os.getenv("AIR_ID")

LAT=float(os.getenv("LAT","0"))
LON=float(os.getenv("LON","0"))

LIGHT_SERVER=os.getenv("LIGHT_SERVER")
GRAPHITE_SERVER=os.getenv("GRAPHITE_SERVER", None)
WEATHER_SERVER=os.getenv("WEATHER_SERVER")
AIO_KEY = os.getenv("AIO_KEY", None)
WU_STATION_ID = os.getenv("WU_STATION_ID", None)
WU_STATION_KEY = os.getenv("WU_STATION_KEY", None)


wu_upload = True
if WU_STATION_ID == None:
    wu_upload = False
wu_url = "http://weatherstation.wunderground.com/weatherstation/updateweatherstation.php"

def c_to_f(input_temp):
    # convert input_temp from Celsius to Fahrenheit
    return (input_temp * 1.8) + 32

def ms_to_mph(input_speed):
    return input_speed * 2.23694

def publish(air, soil, wind):
    tempf_air = c_to_f(air)
    tempf_soil = c_to_f(soil)
    mph_wind = ms_to_mph(wind)
    # From http://wiki.wunderground.com/index.php/PWS_-_Upload_Protocol
    print "Uploading data to Weather Underground"
    # build a weather data object
    weather_data = {
        "action": "updateraw",
        "ID": WU_STATION_ID,
        "PASSWORD": WU_STATION_KEY,
        "dateutc": "now",
        "tempf": str(tempf_air),
        "soiltempf": str(tempf_soil),
        "windspeedmph": str(mph_wind)
    }
    response = requests.get(wu_url, params=weather_data)
    print("Server response:", response.text)

def publish_graphite(air, soil, wind):
    try:
        sock = socket.socket()
        sock.connect( (GRAPHITE_SERVER, 2003) )
        sock.send("weather.soil-temp %f %d \n" % (soil, time.time()))
        sock.send("weather.air-temp %f %d \n" % (air, time.time()))
        sock.send("weather.wind-speed %f %d \n" % (wind, time.time()))
        sock.close()
    except socket.error:
        print "Failed to send data to graphite" 

def publish_AIO(air, soil, wind):
    publish_AIO_metric('soil-temperature', soil)
    publish_AIO_metric('air-temperature', air)
    publish_AIO_metric('wind-speed', wind)

def publish_AIO_metric(feed, value):
    weather = {
        "value":value,
        "lat":LAT,
        "lon":LON,
        "created_at":datetime.datetime.utcnow().isoformat().split('.')[0]
    }
    
    r = requests.post(
        "https://io.adafruit.com/api/v2/rickymoorhouse/feeds/weather.%s/data" % feed,
        data=json.dumps(weather),
        headers={
            "X-AIO-Key":AIO_KEY,
            "Content-Type":"application/json"
        }
    )
    if 200 != r.status_code:
        print r.text


@touch.on(touch.DOWN)
def light_down(ch, evt):
    requests.get('http://%s/power_off' % LIGHT_SERVER).json()
    # We don't want to turn the backlight off here, so just dim it:
    backlight.rgb(10, 10, 10)

@touch.on(touch.UP)
def light_up(ch, evt):
    obj = requests.get('http://%s/power_on' % LIGHT_SERVER).json()
    backlight.rgb(int(obj['red']), int(obj['green']), int(obj['blue']))

@touch.on(touch.LEFT)
def light_left(ch, evt):
    global lum
    lum = lum - 15
    if lum < 0:
        lum = 0
    obj = requests.get('http://%s/lum/%d' % (LIGHT_SERVER, lum)).json()
    backlight.rgb(int(obj['red']), int(obj['green']), int(obj['blue']))

@touch.on(touch.RIGHT)
def light_right(ch, evt):
    global lum
    lum = lum + 15
    if lum > 100:
        lum = 100
    obj = requests.get('http://%s/lum/%d' % (LIGHT_SERVER, lum)).json()
    backlight.rgb(int(obj['red']), int(obj['green']), int(obj['blue']))

def compare_char(new, old):
    if new < old:
        return "<"
    elif new > old:
        return ">"
    else:
        return "="

backlight.set_graph(0)
backlight.rgb(110,100,80)
lcd.set_contrast(45)
lcd.set_cursor_position(0, 0)
lcd.write("  loading...    ")
lcd.set_cursor_position(0, 1)
lcd.write("  ...sensors    ")

memory = {'air':0.00,'soil':0.00, 'wind':0.00}

while True:
    lcd.set_cursor_position(15, 0)
    lcd.write("*")
    try:
        print "http://%s/temperature.json" % WEATHER_SERVER
        r = requests.get("http://%s/temperature.json" % WEATHER_SERVER)
        s = r.json()[SOIL_ID]
        a = r.json()[AIR_ID]
#012345678012345678
#a:11.0 * s:12.5 *
# air:  11.0
#soil:  11.0
#wind:  12.

        lcd.set_cursor_position(0, 0)
        lcd.write("a{}{:4.1f}".format(compare_char(a, memory['air']), a)+chr(223))
        #lcd.set_cursor_position(0, 1)
        lcd.write(" s{}{:4.1f}".format(compare_char(s, memory['soil']), s)+chr(223))
        memory['air'] = a
        memory['soil'] = s

    except KeyError, ValueError:
        lcd.set_cursor_position(15, 0)
        lcd.write("!")
    lcd.set_cursor_position(15, 2)
    lcd.write("*")
    try:
        r = requests.get("http://%s/wind.json" % WEATHER_SERVER)
        w = r.json()['speed']
        lcd.set_cursor_position(0, 1)
        lcd.write("wind:{:5.1f}".format(w)+"k/h "+compare_char(w,memory['wind'])+" ")
        memory['wind'] = w
        lcd.set_cursor_position(15, 2)
        lcd.write(" ")
    except KeyError, ValueError:
        lcd.set_cursor_position(15, 2)
        lcd.write("!")
    if wu_upload:
        publish(memory['air'], memory['soil'], memory['wind'])
    if None != GRAPHITE_SERVER:
        publish_graphite(memory['air'], memory['soil'], memory['wind'])
    time.sleep(20)
