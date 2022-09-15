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

    if result.status_code == 200:
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
    if result.status_code == 200:
        print(result.json())
    else:
        print("Confirmation email failed to send with code " + result.status_code, result.reason)


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

    if student.timezone == -2:
        timezone = "Pacific"
    elif student.timezone == -1:
        timezone = "Mountain"
    elif student.timezone == 0:
        timezone = "Central"
    elif student.timezone == 1:
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
    
    reply_email = student.tutor.email
    if reply_email == '':
        reply_email = app.config['MAIL_USERNAME']

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
                "ReplyTo": { "Email": reply_email },
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

    if result.status_code == 200:
        print(student.student_name, student.last_name, start_display, timezone)
    else:
        print("Error for " + student.student_name + "\'s reminder email with code " + str(result.status_code), result.reason)


def send_registration_reminder_email(student, test_date):
    with app.app_context():
        api_key = app.config['MAILJET_KEY']
        api_secret = app.config['MAILJET_SECRET']
        mailjet = Client(auth=(api_key, api_secret), version='v3.1')

        cc_email = [{ "Email": student.parent_email }]
        if student.secondary_email:
            cc_email.append({ "Email": student.secondary_email })

        td = test_date.date.strftime('%B %-d')
        reg_dl = test_date.reg_date.strftime('%A, %B %-d')
        reg_dl_day = test_date.reg_date.strftime('%A')
        
        if test_date.late_date is not None:
            late_dl = test_date.late_date.strftime('%A, %B %-d')
        else:
            late_dl = None

        data = {
            'Messages': [
                {
                    "From": {
                        "Email": app.config['MAIL_USERNAME'],
                        "Name": "Open Path Tutoring"
                    },
                    "To": [
                        { "Email": student.student_email }
                    ],
                    "Cc": cc_email,
                    "ReplyTo": { "Email": app.config['MAIL_USERNAME'] },
                    "Subject": "Registration deadline for the " + td + " " + test_date.test.upper() + " is this " + reg_dl_day,
                    "HTMLPart": render_template('email/registration-reminder.html', \
                        student=student, test_date=test_date, td=td, reg_dl=reg_dl, late_dl=late_dl),
                    "TextPart": render_template('email/registration-reminder.txt', \
                        student=student, test_date=test_date, td=td, reg_dl=reg_dl, late_dl=late_dl)
                }
            ]
        }
        
        result = mailjet.send.create(data=data)

        if result.status_code == 200:
            print("Registration reminder for", td, test_date.test.upper(), "sent to", student.student_name, student.last_name)
        else:
            print("Error for " + student.student_name + "\'s registration reminder with code " + str(result.status_code), result.reason)


def send_late_registration_reminder_email(student, test_date):
    with app.app_context():
        api_key = app.config['MAILJET_KEY']
        api_secret = app.config['MAILJET_SECRET']
        mailjet = Client(auth=(api_key, api_secret), version='v3.1')

        cc_email = [{ "Email": student.parent_email }]
        if student.secondary_email:
            cc_email.append({ "Email": student.secondary_email })

        td = test_date.date.strftime('%B %-d')
        late_dl = test_date.late_date.strftime('%A, %B %-d')
        late_dl_day = test_date.late_date.strftime('%A')

        data = {
            'Messages': [
                {
                    "From": {
                        "Email": app.config['MAIL_USERNAME'],
                        "Name": "Open Path Tutoring"
                    },
                    "To": [
                        { "Email": student.student_email }
                    ],
                    "Cc": cc_email,
                    "ReplyTo": { "Email": app.config['MAIL_USERNAME'] },
                    "Subject": "Late registration deadline for the " + td + " " + test_date.test.upper() + " is this " + late_dl_day,
                    "HTMLPart": render_template('email/late-registration-reminder.html', \
                        student=student, test_date=test_date, td=td, late_dl=late_dl),
                    "TextPart": render_template('email/late-registration-reminder.txt', \
                        student=student, test_date=test_date, td=td, late_dl=late_dl)
                }
            ]
        }
        
        result = mailjet.send.create(data=data)

        if result.status_code == 200:
            print("Late registration reminder for", td, test_date.test.upper(), "sent to", student.student_name, student.last_name)
        else:
            print("Error for " + student.student_name + "\'s late registration reminder with code " + str(result.status_code), result.reason)


def send_test_reminders_email(student, test_date):
    with app.app_context():
        api_key = app.config['MAILJET_KEY']
        api_secret = app.config['MAILJET_SECRET']
        mailjet = Client(auth=(api_key, api_secret), version='v3.1')

        cc_email = [{ "Email": student.parent_email }]
        if student.secondary_email:
            cc_email.append({ "Email": student.secondary_email })

        td = test_date.date.strftime('%B %-d')
        td_day = test_date.date.strftime('%A')

        data = {
            'Messages': [
                {
                    "From": {
                        "Email": app.config['MAIL_USERNAME'],
                        "Name": "Open Path Tutoring"
                    },
                    "To": [
                        { "Email": student.student_email }
                    ],
                    "Cc": cc_email,
                    "ReplyTo": { "Email": app.config['MAIL_USERNAME'] },
                    "Subject": "Things to remember for your " + test_date.test.upper() + " on " + td_day + ", " + td,
                    "HTMLPart": render_template('email/test-reminders.html', \
                        student=student, test_date=test_date, td=td),
                    "TextPart": render_template('email/test-reminders.txt', \
                        student=student, test_date=test_date, td=td)
                }
            ]
        }
        
        result = mailjet.send.create(data=data)

        if result.status_code == 200:
            print(td, test_date.test.upper(), "reminder sent to", student.student_name, student.last_name)
        else:
            print("Error for " + student.student_name + "\'s test reminder with code " + str(result.status_code), result.reason)


def send_password_reset_email(user):
    token = user.get_reset_password_token()
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
                "Subject": "Reset your password",
                "ReplyTo": { "Email": user.email },
                "TextPart": render_template('email/reset-password.txt',
                                         user=user, token=token),
                "HTMLPart": render_template('email/reset-password.html',
                                         user=user, token=token)
            }
        ]
    }

    result = mailjet.send.create(data=data)
    if result.status_code == 200:
        print(result.json())
    else:
        print("Password reset email failed to send with code " + str(result.status_code), result.reason)


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
                "HTMLPart": render_template('email/test-strategies.html', user=user, relation=relation, sender_name=sender_name, student=student, link=link),
                "TextPart": render_template('email/test-strategies.txt', user=user, relation=relation, sender_name=sender_name, student=student, link=link)
            }
        ]
    }

    result = mailjet.send.create(data=data)
    if result.status_code == 200:
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
                "Subject": "Your score analysis will soon be on its way",
                "TextPart": render_template('email/score-analysis-email.txt',
                                         student=student, school=school),
                "HTMLPart": render_template('email/score-analysis-email.html',
                                         student=student, school=school)
            }
        ]
    }

    result = mailjet.send.create(data=data)
    if result.status_code == 200:
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
    if result.status_code == 200:
        print(result.json())
    else:
        print("Practice test email failed to send with code " + str(result.status_code), result.reason)


def send_weekly_report_email(scheduled_session_count, scheduled_hours, scheduled_student_count, \
    future_list, unscheduled_list, outsourced_session_count, outsourced_hours, \
    outsourced_scheduled_student_count, outsourced_unscheduled_list, \
    paused, now, quote):

    api_key = app.config['MAILJET_KEY']
    api_secret = app.config['MAILJET_SECRET']
    mailjet = Client(auth=(api_key, api_secret), version='v3.1')

    dt = datetime.datetime
    start = (now + datetime.timedelta(hours=40)).isoformat() + 'Z'
    start_date = dt.strftime(parse(start), format="%b %-d")
    end = (now + datetime.timedelta(days=7, hours=40)).isoformat() + 'Z'
    end_date = dt.strftime(parse(end), format="%b %-d")
    future_students = ', '.join(future_list)
    if future_students == '':
        future_students = "None"
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
                    "<br/>Active students scheduled after next week: " + future_students + \
                    "<br/>Paused students: " + paused_students + \
                    "<br/><br/><br/>" + quote_header + '"' + message + '"' + "<br/>&ndash; " + author
            }
        ]
    }

    result = mailjet.send.create(data=data)
    if result.status_code == 200:
        print("Weekly report email sent.\n")
    else:
        print("Weekly report email error:", str(result.status_code), result.reason, "\n")


def send_spreadsheet_report_email(now, spreadsheet_data):
    api_key = app.config['MAILJET_KEY']
    api_secret = app.config['MAILJET_SECRET']
    mailjet = Client(auth=(api_key, api_secret), version='v3.1')

    dt = datetime.datetime
    start = (now + datetime.timedelta(hours=40)).isoformat() + 'Z'
    start_date = dt.strftime(parse(start), format="%b %-d")
    end = (now + datetime.timedelta(days=7, hours=40)).isoformat() + 'Z'
    end_date = dt.strftime(parse(end), format="%b %-d")

    low_active_students = []

    for s in spreadsheet_data['low_active_students']:
        low_active_students.append('<br>' + str(s[0]) + ": " + str(s[1]) + ' hrs')
    
    low_hours_list = ', '.join(low_active_students)
    

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
                    }
                ],
                "Subject": "Spreadsheet data report for " + start_date + " to " + end_date,
                "HTMLPart": "Active students with low hours:<br>" + low_hours_list
            }
        ]
    }

    result = mailjet.send.create(data=data)
    if result.status_code == 200:
        print("Spreadsheet report email sent.\n")
    else:
        print("Spreadsheet report email error:", str(result.status_code), result.reason, "\n")