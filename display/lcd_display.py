#!/usr/bin/env python3

import os
import time
import requests
import json
import simplejson.scanner
import datetime
import time
import socket
import dothat.backlight as backlight
import dothat.lcd as lcd
from dothat import touch
import dateutil.parser

lum = 50

SOIL_ID=os.getenv("SOIL_ID","041643cebdff")
AIR_ID=os.getenv("AIR_ID","0316453f4eff")

LAT=float(os.getenv("LAT","50.842"))
LON=float(os.getenv("LON","-1.1375"))

LIGHT_SERVER=os.getenv("LIGHT_SERVER")
GRAPHITE_SERVER=os.getenv("GRAPHITE_SERVER", "localhost")
WEATHER_SERVER=os.getenv("WEATHER_SERVER", "192.168.0.25")
SOLAR_SERVER=os.getenv("SOLAR_SERVER", "pi.api.me.uk")
AIO_KEY = os.getenv("AIO_KEY", None)
DARKSKY_KEY = os.getenv("DARKSKY_KEY", "f72d3f49ab3c9b3a1fd618a437dd0442")
WU_STATION_ID = os.getenv("WU_STATION_ID", None)
WU_STATION_KEY = os.getenv("WU_STATION_KEY", None)

char_map_south = [
  0b00000,
  0b00000,
  0b00000,
  0b00100,
  0b00100,
  0b10101,
  0b01110,
  0b00100,
]


def tides(filename='/home/rickymoorhouse/tides.json'):
    with open(filename) as tides:
        times = json.load(tides)
    tide_string = ""
    count = 0 
    for instance in times:
        time = datetime.datetime.now()  # Store current datetime
        tide = dateutil.parser.parse(instance['DateTime'])
        if tide > time and count < 2:
            tide_string += "{:.1f}@{:%H:%M}".format(instance['Height'],tide)
            if count == 0:
                tide_string += " "
#        print("{} of {} in {}".format(instance['EventType'], instance['Height'],tide-time))
            count += 1
    return tide_string

def fetch_darksky(DARKSKY_KEY, LAT, LON):
    try:
      darksky_url = "https://api.darksky.net/forecast/{}/{},{}?exclude=minutely,hourly,daily,alerts,flags".format(DARKSKY_KEY, LAT, LON)
      print(darksky_url)
      r = requests.get(darksky_url)
      print(r.text)
      return r.json()
    except simplejson.scanner.JSONDecodeError:
      return {}
    

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
    print("Uploading data to Weather Underground")
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

def publish_graphite(air, soil, wind, dark_sky, wind_ms):
    graphite_string = ""
    graphite_string += "weather.soil-temp %f %d \n" % (soil, time.time())
    graphite_string += "weather.air-temp %f %d \n" % (air, time.time())
    graphite_string += "weather.wind-speed %f %d \n" % (wind, time.time())
    graphite_string += "weather.wind-speed-ms %f %d \n" % (wind_ms, time.time())
    try:
        graphite_string += "weather.wind-bearing %f %d \n" % (dark_sky['currently']['windBearing'], time.time())
        graphite_string += "weather.wind-speed-ds %f %d \n" % (dark_sky['currently']['windSpeed'], time.time())
    except KeyError:
        print("key error on darksky data")
    try:
        sock = socket.socket()
        sock.connect( (GRAPHITE_SERVER, 2003) )
        sock.send(bytes(graphite_string, 'utf-8'))
        print(graphite_string)
        sock.close()
    except socket.error:
        print("Failed to send data to graphite") 

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
        print(r.text)


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
lcd.create_char(7, char_map_south)
lcd.set_cursor_position(0, 0)
lcd.write("  loading...    ")
lcd.set_cursor_position(0, 1)
lcd.write("  ...sensors    ")

memory = {'air':0.00,'soil':0.00, 'wind':0.00}
ds_update = 90
dark_sky = {}
while True:
    lcd.set_cursor_position(15, 0)
    lcd.write("*")
#    if ds_update > 80:
#        dark_sky = fetch_darksky(DARKSKY_KEY, LAT, LON)
#        ds_update = 0
#    else:
#        ds_update += 20
#    print(dark_sky)
    try:
        print("http://%s/temperature.json" % WEATHER_SERVER)
        r = requests.get("http://%s/temperature.json" % WEATHER_SERVER)
        soil = r.json()[SOIL_ID]
        air = r.json()[AIR_ID]
#012345678012345678
#a:11.0 * s:12.5 *
# air:  11.0
#soil:  11.0
#wind:  12.

        lcd.set_cursor_position(0, 0)
        lcd.write("a{}{:4.1f}".format(compare_char(air, memory['air']), air)+chr(223))
        #lcd.set_cursor_position(0, 1)
        lcd.write(" s{}{:4.1f}".format(compare_char(soil, memory['soil']), soil)+chr(223))
        memory['air'] = air
        memory['soil'] = soil
        print(memory)

    #except KeyError as e:
    #    lcd.set_cursor_position(15, 0)
    #    lcd.write("!k")
    except ValueError as e:
        print(e)
        lcd.set_cursor_position(15, 0)
        lcd.write("!v")
    lcd.set_cursor_position(15, 2)
    lcd.write("*")
    try:
        r = requests.get("http://%s/wind.json" % WEATHER_SERVER)
        wind = r.json()['speed']
        w_ms = r.json()['mps']
        lcd.set_cursor_position(0, 1)
        lcd.write("wind:{:5.1f}".format(wind)+"k/h "+compare_char(wind,memory['wind'])+" ")
        memory['wind'] = wind
        lcd.set_cursor_position(15, 2)
        lcd.write(" ")
    except KeyError:
        lcd.set_cursor_position(15, 2)
        lcd.write("!")
    except ValueError:
        lcd.set_cursor_position(15, 2)
        lcd.write("!")
    lcd.set_cursor_position(0, 2)
    lcd.write(tides()[:16])
   # try:
   #     r = requests.get("https://%s/solar.json" % SOLAR_SERVER)
   #     total = r.json()['total_power']
   #     bank1 = r.json()['bank1']['power']
   #     bank2 = r.json()['bank2']['power']
   #     #backlight.set_graph(total / 2800)
   #     lcd.set_cursor_position(0, 2)
   #     lcd.write(chr(7)+"{:5.1f}w ".format(bank1)+ chr(8)+"{:5.1f}w".format(bank2))
   # except KeyError:
   #     lcd.set_cursor_position(15, 2)
   #     lcd.write("!")
   # except ValueError:
   #     lcd.set_cursor_position(15, 2)
   #     lcd.write("!")
    if wu_upload:
        publish(memory['air'], memory['soil'], memory['wind'])
    if None != GRAPHITE_SERVER:
        publish_graphite(air, soil, wind, dark_sky, w_ms)
    time.sleep(20)
