from __future__ import print_function
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import datetime
from dotenv import load_dotenv
from app import app
from flask import render_template
from app.email import send_spreadsheet_report

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

# The ID and range of a sample spreadsheet.
SPREADSHEET_ID = '1M6Xs6zLR_QdPpOJYO0zaZOwJZ6dxdXsURD2PkpP2Vis'
SUMMARY_RANGE_NAME = 'Student summary!A1:Q'


def main():
    """Shows basic usage of the Sheets API.
    Prints values from a sample spreadsheet.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token2.json'):
        creds = Credentials.from_authorized_user_file('token2.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token2.json', 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('sheets', 'v4', credentials=creds)
        # Call the Sheets API
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
                                    range=SUMMARY_RANGE_NAME).execute()

        summary = result.get('values', [])
        now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
        now_str = datetime.datetime.strptime(now, "%Y-%m-%dT%H:%M:%S.%fZ")
        low_active_students = []

        if not summary:
            print('No data found.')
            return

        for row in summary:
            # Print columns A and E, which correspond to indices 0 and 4.
            if row[14] == 'Active':
                if float(row[1]) <= 1.5:
                    low_active_students.append([row[0], row[1]])

        spreadsheet_data = dict(low_active_students=low_active_students)

        send_spreadsheet_report(now_str, spreadsheet_data)

    except HttpError as err:
        print(err)


if __name__ == '__main__':
    main()