from threading import Thread
from app import app
from mailjet_rest import Client
from flask import render_template

def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)

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
