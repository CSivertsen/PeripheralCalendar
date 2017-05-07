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
    global pixelFader = pixelpatterns.pixelFader()

    nowUnadjusted = datetime.datetime.now()
    now = nowUnadjusted.isoformat() + '+02:00' # 'Z' indicates UTC time1
    horizon = (nowUnadjusted+datetime.timedelta(minutes=horizonDelta)).isoformat() + '+02:00'

    calendars = calendarHandler.getCalendars()
    allEvents = calendarHandler.getEvents(now, horizon)
    lastGoogleCall = nowUnadjusted
    global lastScreenActivation
    lastScreenActivation = nowUnadjusted

    print("Here we go! Press CTRL+C to exit")

    try:
        while True:
            #now = datetime.datetime.now() + datetime.timedelta(hours=2)
            # Only check this every 5 minutes
            nowUnadjusted = datetime.datetime.now()
            now = nowUnadjusted.isoformat() + '+02:00' # 'Z' indicates UTC time1

            if datetime.timedelta(minutes=1) < nowUnadjusted - lastGoogleCall:
                allEvents = calendarHandler.getEvents(now, horizon)
                lastGoogleCall = nowUnadjusted
                #print(now)
                #print(horizon)

            if screenTimeout < nowUnadjusted - lastScreenActivation:
                clearScreen()

            showLeds(allEvents, now)
            checkButton(allEvents, nowUnadjusted)
            pixelFader.update()

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

def showLeds(allEvents, now ):
    global horizonDelta
    global calendarHandler
    global pixelFader
    #timeLeft = []
    #print('Showing Leds')


    for i in range(LED_COUNT):
        strip.setPixelColor(i, Color(10, 10, 10))

        for calendarId in allEvents.keys():
            for event in allEvents[calendarId]:

                start = event['start'].get('dateTime', event['start'].get('dateTime'))
                end = event['end'].get('dateTime', event['end'].get('dateTime'))
                if start:
                    colorId = event.get('colorId')
                    colorRGB = calendarHandler.getEventColor(colorId, calendarId)

                    startTime = datetime.datetime.strptime(start, "%Y-%m-%dT%H:%M:%S+02:00")
                    endTime = datetime.datetime.strptime(end, "%Y-%m-%dT%H:%M:%S+02:00")
                    nowTime = datetime.datetime.strptime(now, "%Y-%m-%dT%H:%M:%S.%f+02:00")
                    diffStart = startTime - nowTime
                    diffEnd = endTime - nowTime
                    firstLed = int(abs(round(diffStart.seconds*LED_COUNT/(horizonDelta*60)) - LED_COUNT))
                    lastLed = int(abs(round(diffEnd.seconds*LED_COUNT/(horizonDelta*60)) - LED_COUNT))
                    #print(firstLed, lastLed)

                    #For other events on the timeline
                    for i in range(lastLed, firstLed):
                            #If an event is ongoing
                            if diffStart < datetime.timedelta(minutes=5):
                                fadedColor = pixelFader.fade(colorRGB)
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
    i = 0
    for calendarId in allEvents.keys():
        for event in allEvents[calendarId]:
            eventStart = event['start'].get('dateTime', event['start'].get('dateTime'))
            if eventStart:
                eventStart = datetime.datetime.strptime(eventStart, "%Y-%m-%dT%H:%M:%S+02:00")
                now = nowUnadjusted.isoformat() + '+02:00'
                now = datetime.datetime.strptime(now, "%Y-%m-%dT%H:%M:%S.%f+02:00")
                diff = eventStart - now
                draw.text((x, top + (i*15)), 'Event in ' + str(round(diff.seconds/60)) + ' minutes', font=font, fill=255)
                draw.text((x, top + ((i+1)*15)), event['summary'], font=font, fill=255)
                i += 2

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
