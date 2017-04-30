#!/usr/bin/env python

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


@touch.on(touch.DOWN)
def light_down(ch, evt):
    obj = requests.get('http://%s/power_off' % LIGHT_SERVER).json()
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

backlight.set_graph(0)
backlight.rgb(110,100,80)
lcd.set_contrast(45)
lcd.set_cursor_position(0, 0)
lcd.write("  loading...    ")
lcd.set_cursor_position(0, 1)
lcd.write("  ...sensors    ")

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
        lcd.write(" air:{:5.1f}".format(a)+chr(223)+"C    ")
        lcd.set_cursor_position(0, 1)
        lcd.write("soil:{:5.1f}".format(s)+chr(223)+"C    ")
    except KeyError, ValueError:
        lcd.set_cursor_position(15, 0)
        lcd.write("!")
    lcd.set_cursor_position(15, 2)
    lcd.write("*")
    try:
        r = requests.get("http://%s/wind.json" % WEATHER_SERVER)
        w = r.json()['speed']
        lcd.set_cursor_position(0, 2)
        lcd.write("wind:{:5.1f}".format(w)+"k/h    ")
        lcd.set_cursor_position(15, 2)
        lcd.write(" ")
    except KeyError, ValueError:
        lcd.set_cursor_position(15, 2)
        lcd.write("!")
    time.sleep(20)
