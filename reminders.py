from __future__ import print_function
import datetime
from dateutil.parser import parse, isoparse
from dateutil import tz
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow, Flow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from app import app, db
from dotenv import load_dotenv
from app.models import Student, Tutor, TestDate
from app.email import send_reminder_email, send_weekly_report_email, \
    send_registration_reminder_email, send_late_registration_reminder_email, \
    send_spreadsheet_report_email, send_test_reminders_email
import requests

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/spreadsheets.readonly']

# ID and ranges of a sample spreadsheet.
SPREADSHEET_ID = app.config['SPREADSHEET_ID']
SUMMARY_RANGE = 'Student summary!A1:Q'

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
    service_cal = build('calendar', 'v3', credentials=creds)

    # Call the Sheets API
    service_sheets = build('sheets', 'v4', credentials=creds)
    sheet = service_sheets.spreadsheets()
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
                                range=SUMMARY_RANGE).execute()
    summary_data = result.get('values', [])

    now  = datetime.datetime.strptime(datetime.datetime.utcnow().isoformat(), "%Y-%m-%dT%H:%M:%S.%f")
    today = datetime.date.today()
    day_of_week = datetime.datetime.strftime(now, format="%A")
    upcoming_start = (now + datetime.timedelta(hours=39)).isoformat() + 'Z'
    upcoming_end = (now + datetime.timedelta(hours=63)).isoformat() + 'Z'
    week_end = (now + datetime.timedelta(days=7, hours=31)).isoformat() + 'Z'
    bimonth_end = (now + datetime.timedelta(days=60, hours=31)).isoformat() + 'Z'
    calendars = ['primary', "n6dbnktn1mha2t4st36h6ljocg@group.calendar.google.com"]

    upcoming_events = []
    week_events = []
    week_events_list = []
    bimonth_events = []
    bimonth_events_list = []
    unscheduled_list = []
    outsourced_unscheduled_list = []
    paused_list = []
    scheduled_students = set()
    future_schedule = set()
    outsourced_scheduled_students = set()
    low_active_students = []

    tutoring_hours = 0
    session_count = 0
    outsourced_hours = 0
    outsourced_session_count = 0

    reminder_list = []
    active_students = Student.query.filter_by(status='active')
    paused_students = Student.query.filter_by(status='paused')
    students = Student.query.all()

    # Use fallback quote if request fails
    quote = None
    quote = requests.get("https://zenquotes.io/api/today")


    def full_name(student):
        if student.last_name == "":
            name = student.student_name
        else:
            name = student.student_name + " " + student.last_name
        return name
    
### Test date reminders
    test_dates = TestDate.query.all()
    # for d in test_dates:
    #     print("test", d.id)
    #     for s in students:
    #         print(s.student_name)
    #         for t in s.test_dates:
    #             print(t.date, t.id)
    #             if d.id == t.id:
    #                 print(d.id, t.id)
    
    for s in students:
        for d in s.get_dates():
            if d.reg_date == today + datetime.timedelta(days=5):
                send_registration_reminder_email(s, d)
            elif d.late_date == today + datetime.timedelta(days=5):
                send_late_registration_reminder_email(s, d)
            elif d.date == today + datetime.timedelta(days=6):
                send_test_reminders_email(s, d)

            # mark test dates as past
            if d.date == today:
                d.status = 'past'
                db.session.add(d)
                db.session.commit()
                print('Test date', d.date, 'marked as past')


    for id in calendars:
        bimonth_cal_events = service_cal.events().list(calendarId=id, timeMin=upcoming_start,
            timeMax=bimonth_end, singleEvents=True, orderBy='startTime').execute()
        bimonth_events_result = bimonth_cal_events.get('items', [])

        for e in range(len(bimonth_events_result)):
            if bimonth_events_result[e]['start'].get('dateTime'):
                bimonth_events.append(bimonth_events_result[e])

    for e in range(len(bimonth_events)):
        event_start = bimonth_events[e]['start'].get('dateTime')
        if event_start < week_end:
            week_events.append(bimonth_events[e])
            if event_start < upcoming_end:
                upcoming_events.append(bimonth_events[e])

    upcoming_start_formatted = datetime.datetime.strftime(parse(upcoming_start), format="%A, %b %-d")
    print("Session reminders for " + upcoming_start_formatted + ":")

### Send reminder email to students ~2 days in advance
    for event in upcoming_events:
        for student in active_students:
            name = full_name(student)
            tutor = Tutor.query.get_or_404(student.tutor_id)
            if name in event.get('summary'):
                reminder_list.append(name)
                send_reminder_email(event, student, tutor, quote)

    # get list of event names for the bimonth
    for e in bimonth_events:
        bimonth_events_list.append(e.get('summary'))

    # get list of event names and durations for the week
    for e in week_events:
        if e['start'].get('dateTime'):
            start = isoparse(e['start'].get('dateTime'))
            end = isoparse(e['end'].get('dateTime'))
            duration = str(end - start)
            (h, m, s) = duration.split(':')
            hours = int(h) + int(m) / 60 + int(s) / 3600
            event_details = [e.get('summary'), hours]
            week_events_list.append(event_details)

    # check for students who should be listed as active
    for student in students:
        name = full_name(student)

        if student.status != 'active' and any(name in nest[0] for nest in week_events_list):
            print(name + ' is listed as ' + student.status + ' and is on the schedule.')

    if len(reminder_list) == 0:
        print("No reminders sent.")
    print("\n\n" + quote.json()[0]['q'] + " - " + quote.json()[0]['a'] + "\n\n")

### send weekly reports
    if day_of_week == "Friday":
        # Get number of active students, number of sessions, and list of unscheduled students
        for student in active_students:
            name = full_name(student)
            if any(name in nest[0] for nest in week_events_list):
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
            elif any(name in nest for nest in bimonth_events_list):
                future_schedule.add(name)
            elif student.tutor_id == 1:
                unscheduled_list.append(name)
            else:
                outsourced_unscheduled_list.append(name)

        for student in paused_students:
            name = full_name(student)
            paused_list.append(name)

        send_weekly_report_email(str(session_count), str(tutoring_hours), str(len(scheduled_students)), \
            future_schedule, unscheduled_list, str(outsourced_session_count), \
            str(outsourced_hours), str(len(outsourced_scheduled_students)), \
            outsourced_unscheduled_list, paused_list, now, quote)

### Generate spreadsheet report
        if not summary_data:
            print('No summary data found.')
            return

        # Get list of students with low hours
        for row in summary_data:
            if row[14] == 'Active':
                if float(row[1]) <= 1.5:
                    low_active_students.append([row[0], row[1]])
        
        spreadsheet_data = {'low_active_students': low_active_students}

        send_spreadsheet_report_email(now, spreadsheet_data)

if __name__ == '__main__':
    main()
