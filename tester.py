import time

import RPi.GPIO as GPIO

import Adafruit_GPIO.SPI as SPI
import Adafruit_SSD1306

from neopixel import *

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

# Pin Setup:
GPIO.setmode(GPIO.BCM) # Broadcom pin-numbering scheme

#OLED screen config
RST = 24
DC = 23
SPI_PORT = 0
SPI_DEVICE = 0

disp = Adafruit_SSD1306.SSD1306_128_64(rst=RST, dc=DC, spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE, max_speed_hz=8000000))

#LED strip config
LED_COUNT       = 1
LED_PIN         = 18
LED_FREQ_HZ     = 800000
LED_DMA         = 5
LED_BRIGHTNESS  = 20
LED_INVERT      = False

#Button
butPin = 25

GPIO.setup(butPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

disp.begin()
disp.clear()
disp.display()

width = disp.width
height = disp.height
padding = 2
top = padding
bottom = height-padding

image = Image.new('1', (width, height))
draw = ImageDraw.Draw(image)
draw.rectangle((0,0,width,height), outline=0, fill=0)
font = ImageFont.load_default()

if __name__ == '__main__':
    strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS)
    strip.begin()

    print("Here we go! Press CTRL+C to exit")
    while True:
        if GPIO.input(butPin):
            ## White LED
            for i in range(strip.numPixels()):
                strip.setPixelColor(i, Color(255, 255, 255))
                strip.show()
                draw.rectangle((0,0,width,height), outline=0, fill=0)
                disp.image(image)
                disp.display()
        else:
            ## Button presses, red LED, text on screen
            for i in range(strip.numPixels()):
                strip.setPixelColor(i, Color(0, 255, 0))
                strip.show()

                draw.text((x, top), 'Next meeting in 20 min.', font=font, fill=255)
                draw.text((x, top+20), 'Coach meeting in 0.35', font=font, fill=255)
                disp.image(image)
                disp.display()

GPIO.cleanup()
