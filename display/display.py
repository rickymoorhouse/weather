import json
import os
import socket
import board
import time
import displayio
from i2cdisplaybus import I2CDisplayBus
import terminalio
from adafruit_display_text import label,bitmap_label
from adafruit_bitmap_font import bitmap_font

import adafruit_displayio_ssd1306


USE_LEDSHIM=False
if USE_LEDSHIM:
    import ledbar

import logging
from logging.handlers import SysLogHandler

class ContextFilter(logging.Filter):
    hostname = os.getenv('BALENA_DEVICE_NAME_AT_INIT', socket.gethostname())

    def filter(self, record):
        record.hostname = ContextFilter.hostname
        return True


logger = logging.getLogger("display")
level = getattr(logging, os.getenv("LOG_LEVEL","INFO").upper(), 20)
logging.basicConfig(format='%(levelname)s:%(message)s', level=level)



displayio.release_displays()

i2c = board.I2C()  # uses board.SCL and board.SDA
display_bus = I2CDisplayBus(i2c, device_address=0x3C)
display = adafruit_displayio_ssd1306.SSD1306(display_bus, width=128, height=64)

# Load some proportional fonts
fontFile = "plex.bdf"
fontToUse = bitmap_font.load_font(fontFile)

def update_temp(temp):
    # Make the display context
    logger.info("Updating temperature display to %f", temp)
    splash = displayio.Group()
    display.root_group = splash

    # Draw a label

    temp_str = f"{temp:.1f} C"
    temp_label = bitmap_label.Label(fontToUse, color=0xFFFF00, text=temp_str)
    temp_label.x = 10
    temp_label.y = 40
    splash.append(temp_label)
    text = "Temperature"
    text_area = label.Label(terminalio.FONT, text=text, color=0xFFFF00, x=5, y=5)
    splash.append(text_area)

def update_wind(wind_speed):
    # Make the display context
    logger.info("Updating wind speed display to %f", wind_speed)

    splash = displayio.Group()
    display.root_group = splash

    # Draw a label

    temp_str = f"{wind_speed:.1f} km/h"
    temp_label = bitmap_label.Label(fontToUse, color=0xFFFF00, text=temp_str)
    temp_label.x = 10
    temp_label.y = 40
    splash.append(temp_label)
    text = "Wind Speed"
    text_area = label.Label(terminalio.FONT, text=text, color=0xFFFF00, x=5, y=5)
    splash.append(text_area)

while True:


    # Load data from json
    with open('/data/w1.json') as f:
        data = json.load(f)
        print(data['max'])
        temperature = data['max']
        update_temp(temperature)
    time.sleep(3)
    logger.info("Slept for 3 seconds")
    with open('/data/wind.json') as f:
        data = json.load(f)
        print(data['speed'])
        wind_speed = data['speed']
        update_wind(wind_speed)
    time.sleep(3)
    logger.info("Slept for 3 seconds")


