import RPi.GPIO as GPIO
import time
from neopixel import *

# Pin Setup:
GPIO.setmode(GPIO.BCM) # Broadcom pin-numbering scheme

#LED strip config
LED_COUNT       = 1
LED_PIN         = 18
LED_FREQ_HZ     = 800000
LED_DMA         = 5
LED_BRIGHTNESS  = 20
LED_INVERT      = False

#Button
butPin = 23
GPIO.setup(butPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

if __name__ == '__main__':
    strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS)
    strip.begin()

    print("Here we go! Press CTRL+C to exit")
    while True:
        if GPIO.input(butPin):
            ## White LED
            for i in range(strip.numPixels()):
                strip.setPixelColor(i, Color(255, 255, 255))
        else:
            ## Orange Led
            for i in range(strip.numPixels()):
                strip.setPixelColor(i, Color(255, 0, 0))
except KeyboardInterrupt:
    GPIO.cleanup()
