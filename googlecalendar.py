from __future__ import print_function
import httplib2
import os

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

import dateutil.parser

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

class CalendarService:
    service = None
    calendarColors = {}

    # If modifying these scopes, delete your previously saved credentials
    # at ~/.credentials/calendar-python-quickstart.json
    SCOPES = 'https://www.googleapis.com/auth/calendar.readonly'
    CLIENT_SECRET_FILE = 'client_secret.json'
    APPLICATION_NAME = 'Google Calendar API Python Quickstart'

    def __init__(self):
        self.service = self.authenticate()
        self.calendarIds = self.getCalendars()
        self.colors = self.service.colors().get().execute()

    def getEvents(self, nowUnadjusted, horizon):
        allEvents = {}
        filteredEventObjects = []
        now = nowUnadjusted.isoformat() + '+02:00' # 'Z' indicates UTC time1
        print(now)

        print('Getting events within time horizon')
        for calendarId in self.calendarIds:
            eventsResult = self.service.events().list(
                calendarId=calendarId, timeMin=now, timeMax=horizon, singleEvents=True,
                orderBy='startTime').execute()
            allEvents[calendarId]= eventsResult.get('items', [])


        if not allEvents:
            print('You have no events in the next 3 hours')
        for calendarId in allEvents.keys():
            for event in allEvents[calendarId]:

                filteredEventObjects.append(CalendarEvent(
                    event['start'].get('dateTime', event['start'].get('date')),
                    event['end'].get('dateTime', event['end'].get('date')),
                    event.get('summary'),
                    event.get('location'),
                    self.getEventColor(event.get('colorId'), calendarId),
                    calendarId
                    ))

                #start = event['start'].get('dateTime', event['start'].get('date'))
                #print(start, event['summary'], self.getEventColor(event.get('colorId'),calendarId))

        return filteredEventObjects

    def getCalendars(self):
        page_token = None
        calendarIDs = []
        while True:
            calendar_list = self.service.calendarList().list(pageToken=page_token).execute()

            for calendar_list_entry in calendar_list.get('items'):
              #print(calendar_list_entry.get('summary'))
              calendarId = calendar_list_entry.get('id')
              #Insert specific calendars here
              if True:
                  calendarIDs.append(calendarId)
                  self.calendarColors[calendarId] = calendar_list_entry.get('colorId')
            page_token = calendar_list.get('nextPageToken')
            if not page_token:
                #print(self.calendarColors)
                return calendarIDs

    def getEventColor(self, colorId, calendarId):
        if colorId:
            colorHex = self.colors['event'][colorId].get('background')
        else:
            colorId = self.calendarColors.get(calendarId)
            try:
                colorHex = self.colors['event'][colorId]['background']
            except:
                #print("Color not recognized using Red")
                colorHex = '#FF0000'

        #print(colorId)
        #print(colorHex)
        colorRGB = self.hex_to_rgb(colorHex)
        return colorRGB

    def hex_to_rgb(self, value):
        """Return (red, green, blue) for the color given as #rrggbb."""
        value = value.lstrip('#')
        lv = len(value)
        return tuple(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))

    def authenticate(self):
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
            flow = client.flow_from_clientsecrets(self.CLIENT_SECRET_FILE, self.SCOPES)
            flow.user_agent = self.APPLICATION_NAME
            if flags:
                credentials = tools.run_flow(flow, store, flags)
            else: # Needed only for compatibility with Python 2.6
                credentials = tools.run(flow, store)
            print('Storing credentials to ' + credential_path)

        http = credentials.authorize(httplib2.Http())
        service = discovery.build('calendar', 'v3', http=http)
        return service

class CalendarEvent:
    startTime = None
    endTime = None
    colorRGB = None
    summary = None
    location = None
    calendarId = None

    def __init__(self, start, end, summary, location, color, calendarId):
        self.startTime = dateutil.parser.parse(start)
        self.endTime = dateutil.parser.parse(end)
        self.summary = summary
        self.location = location
        self.calendarId = calendarId
        self.color = color
