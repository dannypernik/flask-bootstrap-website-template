from __future__ import print_function
import datetime
from dateutil.parser import parse, isoparse
from dateutil import tz
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow, Flow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from app import app
from dotenv import load_dotenv
from app.models import Student
from app.email import send_reminder_email, weekly_report_email
import requests

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

def main():
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """
    flow = Flow.from_client_secrets_file(
                os.path.join(basedir, 'credentials.json'), SCOPES)

    authorization_url, state = flow.authorization_url(
    # Enable offline access so that you can refresh an access token without
    # re-prompting the user for permission. Recommended for web server apps.
    access_type='offline',
    # Enable incremental authorization. Recommended as a best practice.
    include_granted_scopes='true')

    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                os.path.join(basedir, 'credentials.json'), SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('calendar', 'v3', credentials=creds)

    # Call the Calendar API
    now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
    today = datetime.datetime.strptime(now, "%Y-%m-%dT%H:%M:%S.%fZ")
    upcoming_start = (today + datetime.timedelta(hours=44)).isoformat() + 'Z'
    upcoming_end = (today + datetime.timedelta(hours=68)).isoformat() + 'Z'
    print('Getting upcoming events with attendees from ' + upcoming_start + ' to ' + upcoming_end)
    events_result = service.events().list(calendarId='primary', timeMin=upcoming_start,
                                        timeMax=upcoming_end, singleEvents=True,
                                        orderBy='startTime').execute()
    events = events_result.get('items', [])
    students = Student.query.order_by(-Student.id).all()
    reminder_list = []
    quote = requests.get("https://quotes.rest/qod?category=inspire&language=en")

    if quote.status_code is not 200:
        quote = None

    for event in events:
        for student in students:
            if " " + student.student_name + " " in event.get('summary'):
                reminder_list.append(student.student_name)
                send_reminder_email(event, student, quote)

    if len(reminder_list) > 0:
        print("Reminders sent to:\r")
        for name in reminder_list:
            print(name + "\r")
    else:
        print("No reminders sent.")


    day_of_week = datetime.datetime.strftime(parse(now), format="%A")
    week_end = (today + datetime.timedelta(days=7, hours=31)).isoformat() + 'Z'
    week_events_result = service.events().list(calendarId='primary', timeMin=upcoming_start,
                                        timeMax=week_end, singleEvents=True,
                                        orderBy='startTime').execute()
    week_events = week_events_result.get('items', [])
    session_count = 0
    tutoring_hours = 0
    print(day_of_week)
    unscheduled_students = set([])

    if day_of_week == "Friday":
        for e in week_events:
            for s in students:
                if " " + s.student_name + " " in e.get('summary'):
                    session_count += 1
                    start = isoparse(e['start'].get('dateTime'))
                    end = isoparse(e['end'].get('dateTime'))
                    duration = str(end - start)
                    (h, m, s) = duration.split(':')
                    hours = int(h) + int(m) / 60 + int(s) / 3600
                    tutoring_hours += hours
                else:
                    unscheduled_students.add(s.student_name)
        print(upcoming_start, week_end)
        weekly_report_email(str(session_count), str(tutoring_hours), str(len(students)), unscheduled_students, today)


if __name__ == '__main__':
    main()
