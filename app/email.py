from threading import Thread
from app import app
from mailjet_rest import Client
from flask import render_template, url_for
import re
import datetime
from dateutil.parser import parse


def verify_quote(quote):
    # Use fallback quote if request fails
    if quote is not None:
        message = quote.json()[0]['q']
        author = quote.json()[0]['a']
        quote_header = "<strong>Random inspirational quote of the day:</strong><br/>"
    else:
        message = "We don't have to do all of it alone. We were never meant to."
        author = "Brene Brown"
        quote_header = ""
    return message, author, quote_header


def send_contact_email(user, message, subject):
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
                "Subject": "Open Path Tutoring: " + subject + " from " + user.first_name,
                "ReplyTo": { "Email": user.email },
                "TextPart": render_template('email/inquiry-form.txt',
                                         user=user, message=message),
                "HTMLPart": render_template('email/inquiry-form.html',
                                         user=user, message=message)
            }
        ]
    }

    result = mailjet.send.create(data=data)

    if result.status_code is 200:
        send_confirmation_email(user, message)
        print("Confirmation email sent to " + user.email)
    else:
        print("Contact email failed with code " + result.status_code)
    print(result.json())


def send_confirmation_email(user, message):
    api_key = app.config['MAILJET_KEY']
    api_secret = app.config['MAILJET_SECRET']
    mailjet = Client(auth=(api_key, api_secret), version='v3.1')

    data = {
        'Messages': [
            {
                "From": {
                    "Email": app.config['MAIL_USERNAME'],
                    "Name": "Open Path Tutoring"
                },
                "To": [
                    {
                    "Email": user.email
                    }
                ],
                "Subject": "Email confirmation + a quote from Brene Brown",
                "TextPart": render_template('email/confirmation.txt',
                                         user=user, message=message),
                "HTMLPart": render_template('email/confirmation.html',
                                         user=user, message=message)
            }
        ]
    }

    result = mailjet.send.create(data=data)
    if result.status_code is 200:
        print(result.json())
    else:
        print("Confirmation email failed to send with code " + result.status_code, result.reason)


def send_test_strategies_email(user, relation, student):
    api_key = app.config['MAILJET_KEY']
    api_secret = app.config['MAILJET_SECRET']
    mailjet = Client(auth=(api_key, api_secret), version='v3.1')

    filename = 'SAT-ACT-strategies.pdf'

    to_email = []
    sender_name = user.parent_name.title()
    student = student.title()

    if relation == 'student':
        sender_name = student
        to_email.append({ "Email": user.student_email })
    to_email.append({ "Email": user.parent_email })

    link = "https://www.openpathtutoring.com/download/" + filename

    data = {
        'Messages': [
            {
                "From": {
                    "Email": app.config['MAIL_USERNAME'],
                    "Name": "Open Path Tutoring"
                },
                "To": to_email,
                "Bcc": [{"Email": app.config['MAIL_USERNAME']}],
                "Subject": "10 Strategies to Master the SAT & ACT",
                "HTMLPart": render_template('email/test-strategies.html', user=user, relation=relation, sender_name=sender_name, student=student, link=link)
            }
        ]
    }

    result = mailjet.send.create(data=data)
    if result.status_code is 200:
        print(result.json())
    else:
        print("Top 10 email failed to send with code " + str(result.status_code), result.reason)


def send_score_analysis_email(student, school):
    api_key = app.config['MAILJET_KEY']
    api_secret = app.config['MAILJET_SECRET']
    mailjet = Client(auth=(api_key, api_secret), version='v3.1')

    data = {
        'Messages': [
            {
                "From": {
                    "Email": app.config['MAIL_USERNAME'],
                    "Name": "Open Path Tutoring"
                },
                "To": [
                    {
                    "Email": student.parent_email
                    }
                ],
                "Bcc": [{"Email": app.config['MAIL_USERNAME']}],
                "Subject": "Email confirmation + a quote from Brene Brown",
                "TextPart": render_template('email/score-analysis-email.txt',
                                         student=student, school=school),
                "HTMLPart": render_template('email/score-analysis-email.html',
                                         student=student, school=school)
            }
        ]
    }

    result = mailjet.send.create(data=data)
    if result.status_code is 200:
        print(result.json())
    else:
        print("Score analysis confirmation email failed to send with code " + result.status_code, result.reason)



def send_practice_test_email(user, test, relation, student):
    api_key = app.config['MAILJET_KEY']
    api_secret = app.config['MAILJET_SECRET']
    mailjet = Client(auth=(api_key, api_secret), version='v3.1')

    if test == 'sat':
        filename = "SAT-1904.pdf"
        test = test.upper()
    elif test == 'act':
        filename = "ACT-201904.pdf"
        test = test.upper()
    else:
        test = 'test'
        filename = ''

    student = student.title()

    to_email = []
    to_email.append({ "Email": user.parent_email })
    if relation == 'student':
        to_email.append({ "Email": user.student_email })

    link = "https://www.openpathtutoring.com/download/" + filename


    data = {
        'Messages': [
            {
                "From": {
                    "Email": app.config['MAIL_USERNAME'],
                    "Name": "Open Path Tutoring"
                },
                "To": to_email,
                "Bcc": [{"Email": app.config['MAIL_USERNAME']}],
                "Subject": "Practice " + test + " for " + student,
                "HTMLPart": render_template('email/practice-test.html', user=user, test=test, relation=relation, student=student, link=link)
            }
        ]
    }

    result = mailjet.send.create(data=data)
    if result.status_code is 200:
        print(result.json())
    else:
        print("Practice test email failed to send with code " + str(result.status_code), result.reason)



def send_reminder_email(event, student, tutor, quote):
    api_key = app.config['MAILJET_KEY']
    api_secret = app.config['MAILJET_SECRET']
    mailjet = Client(auth=(api_key, api_secret), version='v3.1')

    dt = datetime.datetime

    start_time = event['start'].get('dateTime')
    start_date = dt.strftime(parse(start_time), format="%A, %b %-d, %Y")
    start_time_formatted = re.sub(r'([-+]\d{2}):(\d{2})(?:(\d{2}))?$', r'\1\2\3', start_time)

    tz_difference = student.timezone - tutor.timezone

    start_offset = dt.strptime(start_time_formatted, "%Y-%m-%dT%H:%M:%S%z") + datetime.timedelta(hours = tz_difference)
    end_time = event['end'].get('dateTime')
    end_time_formatted = re.sub(r'([-+]\d{2}):(\d{2})(?:(\d{2}))?$', r'\1\2\3', end_time)
    end_offset = dt.strptime(end_time_formatted, "%Y-%m-%dT%H:%M:%S%z") + datetime.timedelta(hours = tz_difference)
    start_display = dt.strftime(start_offset, "%-I:%M%p").lower()
    end_display = dt.strftime(end_offset, "%-I:%M%p").lower()

    message, author, quote_header = verify_quote(quote)

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

    location = event.get('location')
    if location is None:
        location = student.location

    cc_email = [{ "Email": student.parent_email }]
    if student.secondary_email:
        cc_email.append({ "Email": student.secondary_email })
    if tutor.email:
        cc_email.append({ "Email": tutor.email })

    data = {
        'Messages': [
            {
                "From": {
                    "Email": app.config['MAIL_USERNAME'],
                    "Name": "Open Path Tutoring"
                },
                "To": [
                    {
                    "Email": student.student_email
                    }
                ],
                "Cc": cc_email,
                "Subject": "Reminder for " + event.get('summary') + " + a quote from " + author,
                "HTMLPart": "Hi " + student.student_name + ", this is an automated reminder " + \
                    " that you are scheduled for a tutoring session with " + tutor.first_name + " " + \
                    tutor.last_name + " on " + start_date + " from  " + start_display + " to " + \
                    end_display + " " + timezone + " time. <br/><br/>" + "Location: " + location + \
                    "<br/><br/>" + "You are welcome to reply to this email with any questions. " + \
                    "Please provide at least 24 hours notice when cancelling or rescheduling " + \
                    "in order to avoid being charged for the session. Note that you will not receive " + \
                    "a reminder email for sessions scheduled less than 2 days in advance. Thank you!" + \
                    "<br/><br/><br/>" + \
                    quote_header + '"' + message + '"' + "<br/>&ndash; " + author
            }
        ]
    }

    result = mailjet.send.create(data=data)

    if result.status_code is 200:
        print(student.student_name, student.last_name, start_display, timezone)
    else:
        print("Error for " + student.student_name + " with code " + str(result.status_code), result.reason)


def weekly_report_email(scheduled_session_count, scheduled_hours, scheduled_student_count, \
    unscheduled_list, outsourced_session_count, outsourced_hours, \
    outsourced_scheduled_student_count, outsourced_unscheduled_list, \
    paused, now, quote):

    api_key = app.config['MAILJET_KEY']
    api_secret = app.config['MAILJET_SECRET']
    mailjet = Client(auth=(api_key, api_secret), version='v3.1')

    dt = datetime.datetime
    start = (now + datetime.timedelta(hours=39)).isoformat() + 'Z'
    start_date = dt.strftime(parse(start), format="%b %-d")
    end = (now + datetime.timedelta(days=7, hours=31)).isoformat() + 'Z'
    end_date = dt.strftime(parse(end), format="%b %-d")
    unscheduled_students = ', '.join(unscheduled_list)
    if unscheduled_students == '':
        unscheduled_students = "None"
    outsourced_unscheduled_students = ', '.join(outsourced_unscheduled_list)
    if outsourced_unscheduled_students == '':
        outsourced_unscheduled_students = "None"
    paused_students = ', '.join(paused)
    if paused_students == '':
        paused_students = "None"

    message, author, quote_header = verify_quote(quote)

    data = {
        'Messages': [
            {
                "From": {
                    "Email": app.config['MAIL_USERNAME'],
                    "Name": "Open Path Tutoring"
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
                "Subject": "Weekly tutoring report for " + start_date + " to " + end_date,
                "HTMLPart": "A total of " + scheduled_hours + " hours (" + scheduled_session_count + " sessions) " + \
                    "are scheduled with Danny for " + scheduled_student_count + " students next week. <br/><br/>" + \
                    "An additional " + outsourced_hours + " hours (" + outsourced_session_count + " sessions) " + \
                    "are scheduled with other tutors for " + outsourced_scheduled_student_count + " students. " + \
                    "<br/><br/>Unscheduled active students for Danny: " + unscheduled_students + \
                    "<br/>Unscheduled active students for other tutors: " + outsourced_unscheduled_students + \
                    "<br/>Paused students: " + paused_students + \
                    "<br/><br/><br/>" + quote_header + '"' + message + '"' + "<br/>&ndash; " + author
            }
        ]
    }

    result = mailjet.send.create(data=data)
    if result.status_code is 200:
        print("\nWeekly report email sent.\n")
    else:
        print("\nWeekly report email error:", str(result.status_code), result.reason, "\n")
    print(result.json())
