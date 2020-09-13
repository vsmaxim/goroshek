import json

import telegram

from goroshek.config import ADMINS, STUDENTS, BASE_DIR


def is_admin(nickname: str) -> bool:
    return any(admin["username"] == f"@{nickname}" for admin in ADMINS)


def save_chat_id(chat_id: str, user: telegram.User):
    for student in STUDENTS:
        if student["telegram"] == f"@{user.username}":
            student["chat_id"] = chat_id
            break

    with open(BASE_DIR / "students.json", "w") as out:
        json.dump(STUDENTS, out)
