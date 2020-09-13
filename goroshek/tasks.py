import datetime
import pickle
from typing import Sequence

import telegram
from telegram import Message

from goroshek.bot import bot
from goroshek.parser import Person
from goroshek.config import BASE_DIR, GOOGLE_CALENDAR_ID
from googleapiclient.discovery import build, Resource
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request


def build_google_service():
    scopes = ["https://www.googleapis.com/auth/calendar.events"]
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    creds_pickle = BASE_DIR / "token.pickle"
    app_credentials = BASE_DIR / "credentials.json"

    if creds_pickle.exists():
        with open(creds_pickle, "rb") as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(app_credentials), scopes)
            creds = flow.run_local_server(port=0)

        # Save the credentials for the next run
        with open(creds_pickle, 'wb') as token:
            pickle.dump(creds, token)

    return build('calendar', 'v3', credentials=creds)


calendar_service = build_google_service()


def add_event_to_google_calendar(title: str, date: datetime.date) -> str:
    payload = {
        "start": {"date": str(date)},
        "end": {"date": str(date + datetime.timedelta(days=1))},
        "summary": title,
        "description": "Событие сгенерировано ботом",
    }

    event = calendar_service.events().insert(calendarId=GOOGLE_CALENDAR_ID, body=payload).execute()
    return event.get("htmlLink")


# TODO: Implement with json
# TODO: Reimplement with database
def notify_students_from_list(students: Sequence[Person], message: Message) -> Sequence[Person]:
    unnotified_users = []

    for student in students:
        try:
            bot.forward_message(student.chat_id, message.chat_id, message.message_id)
        except telegram.TelegramError as e:
            unnotified_users.append(student)

    return unnotified_users
