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

    # If modifying these scopes, delete your previously saved credentials
    # at ~/.credentials/calendar-python-quickstart.json
    SCOPES = 'https://www.googleapis.com/auth/calendar.readonly'
    CLIENT_SECRET_FILE = 'client_secret.json'
    APPLICATION_NAME = 'Google Calendar API Python Quickstart'

    def __init__(self):
        self.service = self.authenticate()
        self.calendarIds = self.getCalendars()

    def getEvents(self, now, horizon):
        allEvents = []

        print('Getting events within time horizon')
        for calendarId in self.calendarIds:
            eventsResult = self.service.events().list(
                calendarId=calendarId, timeMin=now, timeMax=horizon, singleEvents=True,
                orderBy='startTime').execute()
            allEvents.append(eventsResult.get('items', []))
            #print(eventsResult.get('items', []))

        if not allEvents:
            print('No upcoming events found.')
        for events in allEvents:
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                print(start, event['summary'])

        return allEvents

    def getCalendars(self):
        page_token = None
        calendarIDs = []
        while True:
          calendar_list = self.service.calendarList().list(pageToken=page_token).execute()
          for calendar_list_entry in calendar_list['items']:
              print(calendar_list_entry.get('summary'))
              calendarIDs.append(calendar_list_entry.get('id'))
          page_token = calendar_list.get('nextPageToken')
          if not page_token:
            return calendarIDs

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
