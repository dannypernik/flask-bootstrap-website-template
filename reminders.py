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
from app.models import Student, Tutor
from app.email import send_reminder_email, weekly_report_email
import requests

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
            #, 'https://www.googleapis.com/auth/spreadsheets.readonly']

def main():
    """
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

    # Call the Calendar API
    service = build('calendar', 'v3', credentials=creds)

    now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
    today = datetime.datetime.strptime(now, "%Y-%m-%dT%H:%M:%S.%fZ")
    upcoming_start = (today + datetime.timedelta(hours=44)).isoformat() + 'Z'
    upcoming_end = (today + datetime.timedelta(hours=68)).isoformat() + 'Z'
    upcoming_start_formatted = datetime.datetime.strftime(parse(upcoming_start), format="%A, %b %-d")
    calendars = ['primary', "n6dbnktn1mha2t4st36h6ljocg@group.calendar.google.com"]

    events = []

    for id in calendars:
        cal_events = service.events().list(calendarId=id,
            timeMin=upcoming_start, timeMax=upcoming_end,
            singleEvents=True, orderBy='startTime').execute()
        events_result = cal_events.get('items', [])

        for e in range(len(events_result)):
            events.append(events_result[e])

    reminder_list = []
    active_students = Student.query.filter_by(status='active')
    paused_students = Student.query.filter_by(status='paused')

    # Use fallback quote if request fails
    quote = None
    quote = requests.get("https://zenquotes.io/api/today")

    def full_name(student):
        if student.last_name == "":
            name = student.student_name
        else:
            name = student.student_name + " " + student.last_name
        return name

    print("Session reminders for " + upcoming_start_formatted + ":")

    # Send reminder email to students ~2 days in advance
    for event in events:
        for student in active_students:
            name = full_name(student)
            tutor = Tutor.query.get_or_404(student.tutor_id)
            if " " + name + " and" in event.get('summary'):
                reminder_list.append(name)
                send_reminder_email(event, student, tutor, quote)

    if len(reminder_list) is 0:
        print("No reminders sent.")
    print("\n\n" + quote.json()[0]['q'] + " - " + quote.json()[0]['a'] + "\n\n")


    day_of_week = datetime.datetime.strftime(parse(now), format="%A")
    week_end = (today + datetime.timedelta(days=7, hours=31)).isoformat() + 'Z'
    week_events = []

    for id in calendars:
        cal_week_events = service.events().list(calendarId=id, timeMin=upcoming_start,
            timeMax=week_end, singleEvents=True, orderBy='startTime').execute()
        week_events_result = cal_week_events.get('items', [])

        for e in range(len(week_events_result)):
            week_events.append(week_events_result[e])

    week_events_list = []
    unscheduled_list = []
    outsourced_unscheduled_list = []
    paused_list = []
    scheduled_students = set()
    outsourced_scheduled_students = set()

    tutoring_hours = 0
    session_count = 0
    outsourced_hours = 0
    outsourced_session_count = 0

    if day_of_week == "Friday":
        for e in week_events:
            if e['start'].get('dateTime'):
                start = isoparse(e['start'].get('dateTime'))
                end = isoparse(e['end'].get('dateTime'))
                duration = str(end - start)
                (h, m, s) = duration.split(':')
                hours = int(h) + int(m) / 60 + int(s) / 3600
                event_details = [e.get('summary'), hours]
                week_events_list.append(event_details)

        #Get number of active students, number of sessions, and list of unscheduled students
        for student in active_students:
            name = full_name(student)
            name_check = " " + name + " and"
            if any(name_check in nest[0] for nest in week_events_list):
                print(name + " scheduled with " + student.tutor.first_name)
                for x in week_events_list:
                    count = 0
                    hours = 0
                    if name_check in x[0]:
                        count += 1
                        hours += x[1]
                        if student.tutor_id == 1:
                            scheduled_students.add(name)
                            session_count += count
                            tutoring_hours += hours
                        else:
                            outsourced_scheduled_students.add(name)
                            outsourced_session_count += count
                            outsourced_hours += hours
            elif student.tutor_id == 1:
                unscheduled_list.append(name)
                print(name + " unscheduled with Danny")
            else:
                outsourced_unscheduled_list.append(name)
                print(name + " unscheduled with " + student.tutor.first_name)

        for student in paused_students:
            name = full_name(student)
            paused_list.append(name)

        weekly_report_email(str(session_count), str(tutoring_hours), str(len(scheduled_students)), \
            unscheduled_list, str(outsourced_session_count), str(outsourced_hours), \
            str(len(outsourced_scheduled_students)), outsourced_unscheduled_list, \
            paused_list, today, quote)


        # Call the Sheets API
        #OPT_SS_ID = '1M6Xs6zLR_QdPpOJYO0zaZOwJZ6dxdXsURD2PkpP2Vis'
        #STUDENT_SUMMARY_RANGE = 'Student summary!A1:Q'
        #sheets_service = build('sheets', 'v4', credentials=creds)

        #sheet = sheets_service.spreadsheets()
        #result = sheet.values().get(spreadsheetId=OPT_SS_ID,
        #                            range=STUDENT_SUMMARY_RANGE).execute()
        #values = result.get('values', [])

        #if not values:
        #    print('No data found.')
        #else:
        #    for row in values:
        #        print('%s, %s' % (row[0],row[1]))

if __name__ == '__main__':
    main()
