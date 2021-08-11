#!/usr/bin/python
import smtplib
import time
from email.mime.text import MIMEText

to_email = app.config['MAIL_USERNAME']  # add recipient (your remote account) here
from_email = app.config['MAIL_USERNAME']  # email from which the e-mail is sent; must be accepted by SMTP

s = smtplib.SMTP_SSL(app.config['MAIL_USERNAME'])  # SMTP address
s.login(app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])  # ('smtp login', 'smtp password')

for to in to_list:
    msg = MIMEText('server status: OK')
    msg['Subject'] = 'Server status '+time.ctime()
    msg['From'] = from_email
    msg['To'] = to_email
    print msg.as_string()
    s.sendmail(from_email, to_email, msg.as_string())
