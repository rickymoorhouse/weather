#!/usr/bin/env python

import os
import time
import requests
import dothat.backlight as backlight
import dothat.lcd as lcd
from dothat import touch

hue = 60
lum = 60

SOIL_ID="0316453f4eff"
AIR_ID="041643cebdff"

LIGHT_SERVER="192.168.0.13:8004"
WEATHER_SERVER="192.168.0.33"

DARKSKY="https://api.darksky.net/forecast/f72d3f49ab3c9b3a1fd618a437dd0442/50.842,-1.1375?exclude=hourly,minutely,daily&units=si"

wu_upload = True
wu_station_id = os.getenv("WU_STATION_ID", None)
wu_station_key = os.getenv("WU_STATION_KEY", None)
if wu_station_id == None:
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
        "ID": wu_station_id,
        "PASSWORD": wu_station_key,
        "dateutc": "now",
        "tempf": str(tempf_air),
        "soiltempf": str(tempf_soil),
        "windspeedmph": str(mph_wind)
    }
    response = requests.get(wu_url, params=weather_data)
    print("Server response:", response.text)



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
    global hue
    hue = hue - 20
    if hue < 0:
        hue = 360
    obj = requests.get('http://%s/hue/%d' % (LIGHT_SERVER, hue)).json()
    backlight.rgb(int(obj['red']), int(obj['green']), int(obj['blue']))

@touch.on(touch.RIGHT)
def light_right(ch, evt):
    global hue
    hue = hue + 20
    if hue > 360:
        hue = 0
    obj = requests.get('http://%s/hue/%d' % (LIGHT_SERVER, hue)).json()
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
        r = requests.get("http://%s/temperature.json" % WEATHER_SERVER)
        s = r.json()[SOIL_ID]
        a = r.json()[AIR_ID]
#012345678012345678
# air:  11.0
#soil:  11.0
#wind:  12.

        lcd.set_cursor_position(0, 0)
        lcd.write(" air:{:5.1f}".format(a)+chr(223)+"C "+compare_char(a,memory['air'])+"   ")
        lcd.set_cursor_position(0, 1)
        lcd.write("soil:{:5.1f}".format(s)+chr(223)+"C "+compare_char(s,memory['soil'])+"   ")
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
        lcd.set_cursor_position(0, 2)
        lcd.write("wind:{:5.1f}".format(w)+"k/h "+compare_char(w,memory['wind'])+"   ")
        memory['wind'] = w
        lcd.set_cursor_position(15, 2)
        lcd.write(" ")
    except KeyError, ValueError:
        lcd.set_cursor_position(15, 2)
        lcd.write("!")
    if wu_upload:
        publish(memory['air'], memory['soil'], memory['wind'])
    time.sleep(20)
