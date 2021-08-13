#!/bin/sh

export FLASK_APP=/home/ubuntu/openpath/tutoring.py
export FLASK_ENV=development
. /home/ubuntu/openpath/venv/bin/activate
python3 reminders.py
echo "reminders.sh done"
