from __future__ import print_function
import httplib2
import os

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

import datetime

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

    def getEvents(self, now, horizon):
        allEvents = {}

        print('Getting events within time horizon')
        for calendarId in self.calendarIds:
            eventsResult = self.service.events().list(
                calendarId=calendarId, timeMin=now, timeMax=horizon, singleEvents=True,
                orderBy='startTime').execute()
            allEvents[calendarId]= eventsResult.get('items', [])
            #print(eventsResult.get('items', []))

        if not allEvents:
            print('You have no events in the next 4 hours')
        for calendarId in allEvents.keys():
            for event in allEvents[calendarId]:
                start = event['start'].get('dateTime', event['start'].get('date'))
                print(start, event['summary'])

        return allEvents

    def getCalendars(self):
        page_token = None
        calendarIDs = []
        while True:
            calendar_list = self.service.calendarList().list(pageToken=page_token).execute()

            for calendar_list_entry in calendar_list['items']:
              #print(calendar_list_entry.get('summary'))
              calendarId = calendar_list_entry.get('id')
              calendarIDs.append(calendarId)
              self.calendarColors[calendarId] = calendar_list_entry.get('foregroundColor')
            page_token = calendar_list.get('nextPageToken')
            if not page_token:
                return calendarIDs

    def getEventColor(self, colorId, calendarId):
        if colorId:
            colorHex = self.colors['event'][colorId]['foreground']
        else:
            colorHex = self.calendarColors[calendarId]

        print(colorId)
        print(colorHex)
        colorRGB = self.hex_to_rgb(colorHex)
        return colorRGB

        #try:
        #    colorHex = self.colors.get('event').get(colorId).get('foreground')
        #    colorRGB = hex_to_rgb(colorHex)
        #except:
        #    print("Colors not loaded")
        #    colorRGB = (255,255,255)
        #return colorRGB

    def hex_to_rgb(value):
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
