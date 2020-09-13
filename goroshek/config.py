import json
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")
GOOGLE_CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID")


with open(BASE_DIR / "admins.json", "r") as admin_json:
    ADMINS = json.load(admin_json)


with open(BASE_DIR / "students.json", "r") as students_json:
    STUDENTS = json.load(students_json)

MAIN_ADMIN_HANDLE = os.getenv("MAIN_ADMIN_HANDLE")
