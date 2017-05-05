from __future__ import print_function
import httplib2
import os

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

import RPi.GPIO as GPIO

import Adafruit_GPIO.SPI as SPI
import Adafruit_SSD1306

from neopixel import *

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

import datetime

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/calendar-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/calendar.readonly'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Google Calendar API Python Quickstart'

horizon = 240

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
lastScreenActivation = None
buttonWasOn = False

image = Image.new('1', (width, height))
draw = ImageDraw.Draw(image)
draw.rectangle((0,0,width,height), outline=0, fill=0)
font = ImageFont.load_default()

# Button
butPin = 25
GPIO.setup(butPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

#LED strip config
LED_COUNT       = 13
LED_PIN         = 18
LED_FREQ_HZ     = 800000
LED_DMA         = 5
LED_BRIGHTNESS  = 20
LED_INVERT      = False

strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS)
strip.begin()
strip.setBrightness(15)
strip.show()

def authenticate():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,'calendar-python-quickstart.json')
    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)

    http = credentials.authorize(httplib2.Http())
    service = discovery.build('calendar', 'v3', http=http)
    return service


def main():
    service = authenticate()

    nowUnadjusted = datetime.datetime.now()
    now = nowUnadjusted.isoformat() + '+02:00' # 'Z' indicates UTC time1
    events = getEvents(service, now)
    lastGoogleCall = nowUnadjusted
    global lastScreenActivation
    lastScreenActivation = nowUnadjusted

    print("Here we go! Press CTRL+C to exit")

    while True:
        #now = datetime.datetime.now() + datetime.timedelta(hours=2)
        # Only check this every 5 minutes
        nowUnadjusted = datetime.datetime.now()
        now = nowUnadjusted.isoformat() + '+02:00' # 'Z' indicates UTC time1

        if datetime.timedelta(minutes=1) < nowUnadjusted - lastGoogleCall:
            events = getEvents(service, now)
            lastGoogleCall = nowUnadjusted

        if screenTimeout < nowUnadjusted - lastScreenActivation:
            clearScreen()

        showLeds(events, now)
        checkButton(events, nowUnadjusted)

        # if screen is timed out, call clearScreen

    for i in range(LED_COUNT):
        strip.setPixelColor(i, Color(0, 0, 0))
        strip.show()
    GPIO.cleanup()


def showLeds(events, now ):
    global horizon
    timeLeft = []
    #print('Showing Leds')
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('dateTime'))
        if start:
            startTime = datetime.datetime.strptime(start, "%Y-%m-%dT%H:%M:%S+02:00")
            nowTime = datetime.datetime.strptime(now, "%Y-%m-%dT%H:%M:%S.%f+02:00")
            diff = startTime - nowTime
            #print(diff)
            if diff < datetime.timedelta(minutes=horizon):
                timeLeft.append(diff)

    for i in range(LED_COUNT):
        strip.setPixelColor(i, Color(255, 255, 255))

    for i in range(len(timeLeft)):
        onLed = abs(round(timeLeft[i].seconds*LED_COUNT/(horizon*60)) - LED_COUNT)
        if onLed == LED_COUNT:
            for i in range(LED_COUNT):
                strip.setPixelColor(i, Color(0, 150, 255))
        else:
            for i in range(LED_COUNT):
                if i == onLed:
                    strip.setPixelColor(i, Color(0, 150, 255))
    strip.show()

def checkButton(events, nowUnadjusted):
    global lastScreenActivation
    global buttonWasOn
    if not GPIO.input(butPin) and not buttonWasOn:
        lastScreenActivation = nowUnadjusted
        showScreen(events, nowUnadjusted)
        buttonWasOn = True

    if GPIO.input(butPin):
        buttonWasOn = False


def showScreen(events, nowUnadjusted):
    i = 0
    for event in events:
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


def getEvents( service , now):
    """Shows basic usage of the Google Calendar API.

    Creates a Google Calendar API service object and outputs a list of the next
    10 events on the user's calendar.
    """

    print('Getting the upcoming 5 events')
    eventsResult = service.events().list(
        calendarId='primary', timeMin=now, maxResults=5, singleEvents=True,
        orderBy='startTime').execute()
    newEvents = eventsResult.get('items', [])

    if not newEvents:
        print('No upcoming events found.')
    for event in newEvents:
        start = event['start'].get('dateTime', event['start'].get('date'))
        print(start, event['summary'])

    return newEvents

if __name__ == '__main__':
    main()
