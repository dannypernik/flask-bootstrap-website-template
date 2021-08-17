from __future__ import print_function
import datetime
from dateutil.parser import parse
from dateutil import tz
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow, Flow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from app import app
from mailjet_rest import Client
from dotenv import load_dotenv
from app.models import Student

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
    upcoming_start = (today + datetime.timedelta(days=2)).isoformat() + 'Z'
    upcoming_end = (today + datetime.timedelta(days=3)).isoformat() + 'Z'
    print('Getting upcoming events with attendees from ' + upcoming_start + ' to ' + upcoming_end)
    events_result = service.events().list(calendarId='primary', timeMin=upcoming_start,
                                        timeMax=upcoming_end, singleEvents=True,
                                        orderBy='startTime').execute()
    events = events_result.get('items', [])
    students = Student.query.order_by(-Student.id).all()
    reminder_list = []

    for event in events:
        for student in students:
            if " " + student.student_name + " " in event.get('summary'):
                reminder_list.append(student.student_name)
                send_reminder_email(event, student)

    if len(reminder_list) > 0:
        print("Reminders sent to:\r")
        for name in reminder_list:
            print(name + "\r")
    else:
        print("No reminders sent.")


def send_reminder_email(event, student):
    api_key = app.config['MAILJET_KEY']
    api_secret = app.config['MAILJET_SECRET']
    mailjet = Client(auth=(api_key, api_secret), version='v3.1')

    dt = datetime.datetime

    start_date = dt.strftime(parse(event['start'].get('dateTime')), format="%A, %b %-d %Y")
    start_time = event['start'].get('dateTime')
    start_offset = dt.strptime(start_time, "%Y-%m-%dT%H:%M:%S%z") + datetime.timedelta(hours = student.timezone)
    end_time = event['end'].get('dateTime')
    end_offset = dt.strptime(end_time, "%Y-%m-%dT%H:%M:%S%z") + datetime.timedelta(hours = student.timezone)
    start_display = dt.strftime(start_offset, "%-I:%M") + dt.strftime(start_offset, "%p").lower()
    end_display = dt.strftime(end_offset, "%-I:%M") + dt.strftime(end_offset, "%p").lower()

    if student.timezone is -2:
        timezone = "Pacific"
    elif student.timezone is -1:
        timezone = "Mountain"
    elif student.timezone is 0:
        timezone = "Central"
    elif student.timezone is 1:
        timezone = "Eastern"
    else:
        timezone = "your"

    data = {
        'Messages': [
            {
            "From": {
                "Email": app.config['MAIL_USERNAME'],
                "Name": "Danny Pernik"
            },
            "To": [
                {
                "Email": student.student_email
                },
                {
                "Email": student.parent_email
                }
            ],
            "Bcc": [
                {
                "Email": app.config['MAIL_USERNAME']
                }
            ],
            "Subject": "Reminder for " + event.get('summary'),
            "HTMLPart": "Hello, this is an automated reminder that a tutoring session is scheduled on " + \
            start_date + " from  " + start_display + " to " + end_display + " " + \
            timezone + " time. <br/><br/>You are welcome to reply to this email with any questions. " + \
            "Please provide at least 24 hours notice when cancelling or rescheduling " + \
            "in order to avoid losing the session. <br/><br/>Thank you,<br/>Danny"
            }
        ]
    }

    result = mailjet.send.create(data=data)
    print(result.status_code)
    print(result.json())


if __name__ == '__main__':
    main()
