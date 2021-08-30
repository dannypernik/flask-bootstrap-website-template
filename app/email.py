from threading import Thread
from app import app
from mailjet_rest import Client
from flask import render_template
import re
import datetime
from dateutil.parser import parse

def send_contact_email(user, message):
    api_key = app.config['MAILJET_KEY']
    api_secret = app.config['MAILJET_SECRET']
    mailjet = Client(auth=(api_key, api_secret), version='v3.1')

    data = {
        'Messages': [
            {
            "From": {
                "Email": app.config['MAIL_USERNAME'],
                "Name": "Danny Pernik"
            },
            "To": [
                {
                "Email": app.config['MAIL_USERNAME']
                }
            ],
            "Subject": "Open Path Tutoring: Message from " + user.first_name,
            "ReplyTo": { "Email": user.email },
            "HTMLPart": render_template('email/inquiry-form.txt',
                                     user=user, message=message)
            }
        ]
    }

    result = mailjet.send.create(data=data)
    print(result.status_code)
    print(result.json())


def send_reminder_email(event, student, quote):
    api_key = app.config['MAILJET_KEY']
    api_secret = app.config['MAILJET_SECRET']
    mailjet = Client(auth=(api_key, api_secret), version='v3.1')

    dt = datetime.datetime

    start_date = dt.strftime(parse(event['start'].get('dateTime')), format="%A, %b %-d, %Y")
    start_time = event['start'].get('dateTime')
    start_time_formatted = re.sub(r'([-+]\d{2}):(\d{2})(?:(\d{2}))?$', r'\1\2\3', start_time)
    start_offset = dt.strptime(start_time_formatted, "%Y-%m-%dT%H:%M:%S%z") + datetime.timedelta(hours = student.timezone)
    end_time = event['end'].get('dateTime')
    end_time_formatted = re.sub(r'([-+]\d{2}):(\d{2})(?:(\d{2}))?$', r'\1\2\3', end_time)
    end_offset = dt.strptime(end_time_formatted, "%Y-%m-%dT%H:%M:%S%z") + datetime.timedelta(hours = student.timezone)
    start_display = dt.strftime(start_offset, "%-I:%M") + dt.strftime(start_offset, "%p").lower()
    end_display = dt.strftime(end_offset, "%-I:%M") + dt.strftime(end_offset, "%p").lower()

    # Use fallback quote if request fails
    if quote is not None:
        message = quote.json()['contents']['quotes'][0]['quote']
        author = quote.json()['contents']['quotes'][0]['author']
        quote_header = "<strong>Random inspirational quote of the day:</strong><br/>"
    else:
        quote_header = ""
        message = "We don't have to do all of it alone. We were never meant to."
        author = "Brene Brown"

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
                "Subject": "Reminder for " + event.get('summary') + " + a quote from " + author,
                "HTMLPart": "Hi " + student.student_name + " and " + student.parent_name + \
                    ", this is an automated reminder that " + student.student_name + \
                    " is scheduled for a tutoring session on " + start_date + " from  " + \
                    start_display + " to " + end_display + " " + timezone + " time. <br/><br/>" + \
                    "Location: " + student.location + "<br/><br/>" + \
                    "You are welcome to reply to this email with any questions. " + \
                    "Please provide at least 24 hours notice when cancelling or rescheduling " + \
                    "in order to avoid losing the session. Note that you will not receive a " + \
                    "reminder email for sessions scheduled less than 2 days in advance.<br/><br/>" + \
                    "Thank you,<br/>Danny <br/><br/><br/>" + \
                    quote_header + '"' + message + '"' + "<br/>&mdash; " + author
            }
        ]
    }

    result = mailjet.send.create(data=data)
    print(result.status_code)
    print(result.json())


def weekly_report_email(sessions, hours, students, unscheduled, now):
    api_key = app.config['MAILJET_KEY']
    api_secret = app.config['MAILJET_SECRET']
    mailjet = Client(auth=(api_key, api_secret), version='v3.1')

    dt = datetime.datetime
    start = (now + datetime.timedelta(hours=39)).isoformat() + 'Z'
    start_date = dt.strftime(parse(start), format="%b %-d")
    end = (now + datetime.timedelta(days=7, hours=31)).isoformat() + 'Z'
    end_date = dt.strftime(parse(end), format="%b %-d")
    unscheduled_students = ', '.join(unscheduled)

    data = {
        'Messages': [
            {
                "From": {
                    "Email": app.config['MAIL_USERNAME'],
                    "Name": "Danny Pernik"
                },
                "To": [
                    {
                    "Email": app.config['MAIL_USERNAME']
                    },
                    {
                    "Email": app.config['MOM_EMAIL']
                    },
                    {
                    "Email": app.config['DAD_EMAIL']
                    }
                ],
                "Subject": "Tutoring schedule summary for " + start_date + " to " + end_date,
                "HTMLPart": "Scheduled sessions: " + sessions + "<br/>" + \
                    "Scheduled hours: " + hours + \
                    "<br/>Active students: " + students + \
                    "<br/>Unscheduled students: " + unscheduled_students
            }
        ]
    }

    result = mailjet.send.create(data=data)
    print(result.status_code)
    print(result.json())
