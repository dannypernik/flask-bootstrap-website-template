from threading import Thread
from flask_mailman import Message
from app import mail, app
from flask import render_template

def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)

def send_email(subject, sender, recipients, reply_to, text_body, html_body):
    msg = Message(subject, sender=sender, recipients=recipients.split())
    msg.body = text_body
    msg.html = html_body
    Thread(target=send_async_email, args=(app, msg)).start()

def send_inquiry_email(user, subject, message):
    send_email(subject,
               sender=("Ascended Learning", "ascendedlearningtutoring@gmail.com"),
               recipients=app.config['ADMINS'][0],
               reply_to=user.email,
               text_body=render_template('email/inquiry-form.txt',
                                        user=user, message=message),
               html_body=render_template('email/inquiry-form.html',
                                        user=user, message=message))
