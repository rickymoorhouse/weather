import board
import displayio
from i2cdisplaybus import I2CDisplayBus
import terminalio
from adafruit_display_text import label
from adafruit_bitmap_font import bitmap_font

import adafruit_displayio_ssd1306

displayio.release_displays()

i2c = board.I2C()  # uses board.SCL and board.SDA
display_bus = I2CDisplayBus(i2c, device_address=0x3C)
display = adafruit_displayio_ssd1306.SSD1306(display_bus, width=128, height=64)

# Load some proportional fonts
fontFile = "helv.bdf"
fontToUse = bitmap_font.load_font(fontFile)

def update(temp, humidity):
    # Make the display context
    splash = displayio.Group()
    display.root_group = splash

    color_bitmap = displayio.Bitmap(128, 64, 1)
    color_palette = displayio.Palette(1)
    color_palette[0] = 0xFFFFFF  # White

    # Draw a label
    text = "Temperature: {}".format(temp)
    text_area = label.Label(terminalio.FONT, text=text, color=0xFFFF00, x=5, y=5)
    splash.append(text_area)

    text2 = "Humidity: {}%".format(humidity)
    text2_area = label.Label(fontToUse, text=text, color=0xFFFF00, x=5, y=25)
    splash.append(text2_area)
