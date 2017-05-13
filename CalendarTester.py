import RPi.GPIO as GPIO

import Adafruit_GPIO.SPI as SPI
import Adafruit_SSD1306

from neopixel import *

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

import traceback

import datetime

import googlecalendar
horizonDelta = 180
calendarHandler = None

import pixelpatterns
pixelFader = None


# Pin Setup:
GPIO.setmode(GPIO.BCM) # Broadcom pin-numbering scheme

# OLED screen config
RST = 24
DC = 23
SPI_PORT = 0
SPI_DEVICE = 0

disp = Adafruit_SSD1306.SSD1306_128_64(rst=RST, dc=DC, spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE, max_speed_hz=8000000))

disp.begin()
disp.clear()
disp.display()

width = disp.width
height = disp.height
padding = 2
top = padding
bottom = height-padding
x = padding

screenTimeout = datetime.timedelta(seconds=5)
buttonTimeout = datetime.timedelta(seconds=10)
lastScreenActivation = None
buttonWasOn = False
buttonActivation = None

image = Image.new('1', (width, height))
draw = ImageDraw.Draw(image)
draw.rectangle((0,0,width,height), outline=0, fill=0)
font = ImageFont.load_default()

# Button
butPin = 25
GPIO.setup(butPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

#LED strip config
LED_COUNT       = 12
LED_PIN         = 18
LED_FREQ_HZ     = 800000
LED_DMA         = 5
LED_BRIGHTNESS  = 20
LED_INVERT      = False

strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS)
strip.begin()
strip.setBrightness(15)
strip.show()


def main():

    global calendarHandler
    calendarHandler = googlecalendar.CalendarService()
    global pixelFader
    pixelFader = pixelpatterns.PixelFader()

    nowUnadjusted = datetime.datetime.now()
    now = nowUnadjusted.isoformat() + '+02:00' # 'Z' indicates UTC time1
    horizon = (nowUnadjusted+datetime.timedelta(minutes=horizonDelta)).isoformat() + '+02:00'
    calendars = calendarHandler.getCalendars()
    allEvents = calendarHandler.getEvents(nowUnadjusted, horizon)
    lastGoogleCall = nowUnadjusted
    global lastScreenActivation
    lastScreenActivation = nowUnadjusted

    print("Here we go! Press CTRL+C to exit")

    try:
        while True:
            #now = datetime.datetime.now() + datetime.timedelta(hours=2)
            # Only check this every 5 minutes
            nowUnadjusted = datetime.datetime.now()

            if datetime.timedelta(minutes=1) < nowUnadjusted - lastGoogleCall:
                horizon = (nowUnadjusted+datetime.timedelta(minutes=horizonDelta)).isoformat() + '+02:00'
                allEvents = calendarHandler.getEvents(nowUnadjusted, horizon)
                lastGoogleCall = nowUnadjusted
                #print(now)
                #print(horizon)

            if screenTimeout < nowUnadjusted - lastScreenActivation:
                clearScreen()

            #pixelFader.update()
            showLeds(allEvents, nowUnadjusted)
            checkButton(allEvents, nowUnadjusted)
            # if screen is timed out, call clearScreen

    except KeyboardInterrupt:
        for i in range(LED_COUNT):
            strip.setPixelColor(i, Color(0, 0, 0))
            strip.show()
        GPIO.cleanup()
        print('Exiting program due to KeyboardInterrupt')
        exit()
    except:
        for i in range(LED_COUNT):
            strip.setPixelColor(i, Color(0, 0, 0))
            strip.show()
        GPIO.cleanup()
        traceback.print_exc()

def showLeds(allEvents, now):
    global horizonDelta
    global calendarHandler
    global pixelFader
    #timeLeft = []
    #print('Showing Leds')

    for i in range(LED_COUNT):
        strip.setPixelColor(i, Color(10, 10, 10))

        for event in allEvents:
            if event.start:
                diffStart = event.start - now
                diffEnd = event.end - now
                firstLed = int(abs(round(diffStart.seconds*LED_COUNT/(horizonDelta*60)) - LED_COUNT))
                lastLed = int(abs(round(diffEnd.seconds*LED_COUNT/(horizonDelta*60)) - LED_COUNT))
                #print(firstLed, lastLed)

                #For other events on the timeline
                for i in range(lastLed, firstLed):
                    #If an event is ongoing
                    if diffStart < datetime.timedelta(minutes=5):
                        fadedColor = pixelFader.fade(colorRGB)
                        #print(fadedColor)
                        strip.setPixelColor(i, Color(fadedColor[1], fadedColor[0], fadedColor[2]))

                    #Other events
                    else:
                        strip.setPixelColor(i, Color(colorRGB[1], colorRGB[0], colorRGB[2]))
    strip.show()

def checkButton(allEvents, nowUnadjusted):
    global lastScreenActivation
    global buttonWasOn
    global buttonActivation
    if not GPIO.input(butPin) and not buttonWasOn:
        lastScreenActivation = nowUnadjusted
        buttonActivation = nowUnadjusted
        showScreen(allEvents, nowUnadjusted)
        buttonWasOn = True

    if not GPIO.input(butPin) and buttonWasOn:
        if buttonTimeout < nowUnadjusted - buttonActivation:
            shutdown()

    if GPIO.input(butPin):
        buttonWasOn = False


def showScreen(allEvents, nowUnadjusted):
    eventTimes = []
    firstEvent = None
    for event in allEvents:
        if not event.start.time():
            break

        #Assembles all events into a list
        else:
            eventTimes.append((event.start, event.end))

        #Find the event in the list with the earliest start time
        if eventStartString:
            if not firstEvent:
                firstEvent = event
            elif eventStart < firstEvent.start:
                firstEvent = event

    if firstEvent:

        if firstEvent.start < now:
            draw.text((x, top + ((0)*15)), firstEvent.summary, font=font, fill=255)
            draw.text((x, top + ((1)*15)), 'Now: ' + firstEvent.start.time() + ' - ' + firstEvent.end.time() , font=font, fill=255)
            if firstEvent.location:
                draw.text((x, top + ((2)*15)), firstEvent.location + ' ', font=font, fill=255)
        else:
            draw.text((x, top + ((0)*15)), firstEvent.summary, font=font, fill=255)
            draw.text((x, top + ((1)*15)), firstEvent.start.time() + ' - ' + firstEvent.end.time(), font=font, fill=255)
            if firstEvent.location:
                draw.text((x, top + ((2)*15)), firstEvent.location + ' ', font=font, fill=255)
    else:
        draw.text((x, top + (0*15)), 'No events in the', font=font, fill=255)
        draw.text((x, top + (1*15)), 'next 3 hours', font=font, fill=255)

    disp.image(image)
    disp.display()


def clearScreen():
    # Draw a black filled box to clear the image.
    draw.rectangle((0,0,width,height), outline=0, fill=0)

    # Display image.
    disp.image(image)
    disp.display()


def shutdown():
    for i in range(LED_COUNT):
        strip.setPixelColor(i, Color(0, 0, 0))
        strip.show()
    GPIO.cleanup()
    print('Shutting down RaspPi')
    os.system("sudo shutdown -h now")

if __name__ == '__main__':
    main()
