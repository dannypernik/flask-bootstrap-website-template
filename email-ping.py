from app import app
from mailjet_rest import Client

def send_email_ping():
    api_key = app.config['MAILJET_KEY']
    api_secret = app.config['MAILJET_SECRET']
    mailjet = Client(auth=(api_key, api_secret), version='v3.1')

    data = {
        'Messages': [
            {
            "From": {
                "Email": app.config['MAIL_USERNAME']
            },
            "To": [
                {
                "Email": app.config['GMAIL_USERNAME']
                }
            ],
            "Subject": "email-ping.py",
            "TextPart": "This automated email increases the frequency with which Gmail checks Gmail."
            }
        ]
    }

    result = mailjet.send.create(data=data)
    print(result.status_code)
    print(result.json())

send_email_ping()
