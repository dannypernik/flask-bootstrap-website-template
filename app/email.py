from threading import Thread
from flask_mailman import EmailMessage
from app import mail, app
from flask import render_template

def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)

def send_email(subject, text_body, from_email, to, reply_to):
    msg = EmailMessage(subject=subject, body=text_body, from_email=from_email, to=to.split(), reply_to=reply_to)
    Thread(target=send_async_email, args=(app, msg)).start()

def send_inquiry_email(user, message):
    send_email(subject="Contact Form Submission: " + user.first_name,
               from_email=("OpenPath Tutoring", app.config['MAIL_USERNAME']),
               to=app.config['ADMINS'][0],
               reply_to=[user.email],
               text_body=render_template('email/inquiry-form.txt',
                                        user=user, message=message))
