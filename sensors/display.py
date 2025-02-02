import board
import time
import displayio
from i2cdisplaybus import I2CDisplayBus
import terminalio
from adafruit_display_text import label,bitmap_label
from adafruit_bitmap_font import bitmap_font

import adafruit_displayio_ssd1306

displayio.release_displays()

i2c = board.I2C()  # uses board.SCL and board.SDA
display_bus = I2CDisplayBus(i2c, device_address=0x3C)
display = adafruit_displayio_ssd1306.SSD1306(display_bus, width=128, height=64)

# Load some proportional fonts
fontFile = "plex.bdf"
fontToUse = bitmap_font.load_font(fontFile)

def update(temp, wind_speed):
    update_temp(temp)
    time.sleep(3000)
    update_wind(wind_speed)
    time.sleep(3000)

def update_temp(temp):
    # Make the display context
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
