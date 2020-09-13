import datetime
import re
from typing import Sequence, Set

from telegram.ext import CommandHandler, ConversationHandler, Filters, MessageHandler

from goroshek.bot import bot
from goroshek.config import ADMINS, MAIN_ADMIN_HANDLE, TELEGRAM_CHANNEL_ID
from goroshek.parser import parse_dates, parse_persons, Person
from goroshek.tasks import add_event_to_google_calendar, notify_students_from_list
from goroshek.utils import is_admin

(
    START_POST,
    PARSE_POST,
    ASK_TAGS,
    MAKE_CALENDAR_NOTIFICATIONS,
    ADD_TO_CALENDAR,
    NOTIFY_USERS_IN_PM,
) = range(6)


# TODO: Move to db or config
MAIN_TAG = "#общее"
COURSE_TAG = "#курс"
COURSE_NAME_TAGS = ["#спглмат", "#моипис", "#битис", "#коммнир", "#сппр", "#иняз"]


TAG_PRIORITY = {
    0: {MAIN_TAG, COURSE_TAG},
    1: {*COURSE_NAME_TAGS},
}


def start_post(update, context):
    course_tags = "\n".join([f"- {tag}" for tag in COURSE_NAME_TAGS])

    # Check if user has rights
    if not is_admin(update.effective_user.username):
        update.message.reply_text(f"У тебя нет прав, чтобы постить в канал, попроси разрешение у {MAIN_ADMIN_HANDLE}")
        return ConversationHandler.END

    update.message.reply_text(
        "Я помогу тебе написать что-то очень важное в канал! "
        "Отправь мне пост, который нужно опубликовать в канале. "
        "Отправка нескольких файлов или фото на данный момент не поддерживается, если очень нужно, то можно "
        "это сделать вручную, или вспользоваться Google Drive.\n\n"
        "Пост должен содержать один главный тег:\n"
        "  #общее - информация не относящаяся к читаемым курсам\n"
        "  #курс - информация относящаяся к читаемым курсам\n\n"
        f"Информация о читаемых нам курсах должна также иметь тег с названием курса:\n{course_tags}\n\n"
        "Примеры правильных тегов:\n"
        "#общее #расписание\n"
        f"#курс {COURSE_NAME_TAGS[0]} #дз\n"
    )
    return PARSE_POST


def validate_tags(tags: Set[str]) -> Sequence[str]:
    errors = []

    if MAIN_TAG in tags:
        pass
    elif COURSE_TAG in tags:
        if not any(course_name_tag in tags for course_name_tag in COURSE_NAME_TAGS):
            available_course_name_tags = ", ".join(COURSE_NAME_TAGS)
            errors.append(f"- Отсутствует тег с названием курса (возможные значения: {available_course_name_tags})")
    else:
        errors.append(f"- Отсутствует главный тег (возможные значения {MAIN_TAG}, {COURSE_TAG})")

    return errors


def parse_tags_from_tagline(tagline: str) -> Set[str]:
    return {f"#{tag}" for tag in re.split(r"\s?#", tagline) if tag}


# TODO: Rename to parsing step
def parse_post_info(update, context):
    def parse_tags_and_message():
        if update.message.text:
            message = update.message.text
        else:
            message = update.message.caption

        tags, *text_lines = message.split("\n")

        if "#" in tags:
            context.user_data["message_text"] = "\n".join(text_lines)
            context.user_data["tags"] = {f"#{tag.strip()}" for tag in re.split(r"\s?#", tags) if tag}
        else:
            context.user_data["message_text"] = "\n".join([tags, *text_lines])
            context.user_data["tags"] = set()

        context.user_data["message"] = update.message

    def parse_dates_and_users():
        context.user_data["dates"] = list(parse_dates(context.user_data["message_text"]))
        context.user_data["users"] = [
            p
            for p in parse_persons(context.user_data["message_text"])
            if p.is_full and p.telegram_handle
        ]

    parse_tags_and_message()
    parse_dates_and_users()

    errors = validate_tags(context.user_data["tags"])

    if errors:
        errors_desc = "\n".join(errors)
        update.message.reply_text(f"Обнаружены следующие ошибки в тегах:\n{errors_desc}")
        return ASK_TAGS

    return ask_calendar_notification(update, context)


def rewrite_tags_and_validate_step(update, context):
    context.user_data["tags"] |= parse_tags_from_tagline(update.message.text)
    errors = validate_tags(context.user_data["tags"])

    if errors:
        errors_desc = "\n".join(errors)
        update.message.reply_text(f"Обнаружены следующие ошибки в тегах:\n{errors_desc}")
        return ASK_TAGS

    return ask_calendar_notification(update, context)


def ask_calendar_notification(update, context):
    if context.user_data["dates"]:
        date: datetime.date = context.user_data["dates"].pop(0)
        context.user_data["current_date"] = date
        pretty_date = date.strftime("%d.%m.%y")
        update.message.reply_text(f"В тексте найдена дата: {pretty_date}, добавить событие в Google Calendar (да/нет)?")
        return MAKE_CALENDAR_NOTIFICATIONS

    return ask_notify_users(update, context)


def ask_calendar_title(update, context):
    update.message.reply_text("Как назовем событие?")
    return ADD_TO_CALENDAR


def notify_users(update, context):
    make_post(update, context)
    not_notified_users = notify_students_from_list(context.user_data["users"], context.user_data["sent_message"])
    update.message.reply_text(f"Следующие люди не были оповещены:\n{pretty_users_list(not_notified_users)}")
    return ConversationHandler.END


def add_to_calendar(update, context):
    event_link = add_event_to_google_calendar(update.message.text, context.user_data["current_date"])
    update.message.reply_text(f"Событие успешно создано {event_link}")
    return ask_calendar_notification(update, context)


def ask_notify_users(update, context):
    if context.user_data["users"]:
        parsed_users = pretty_users_list(context.user_data["users"])

        update.message.reply_text(
            "В тексте найдены следующие имена известных студентов:\n"
            f"{parsed_users}\n\nОповестить их?"
        )

        return NOTIFY_USERS_IN_PM

    return make_post(update, context)


def pretty_users_list(users: Sequence[Person]):
    return "\n".join(
        f"- {user} ({user.telegram_handle or 'n/a'})"
        for user in users
        if user.is_full
    )


def make_post(update, context):
    tags = context.user_data["tags"]
    message_text = context.user_data["message_text"]
    message = context.user_data["message"]

    body = f"{' '.join(tags)}\n\n{message_text}"

    # TODO: A weird bug with multiple photos: only first is sent with caption
    if message.photo:
        sent_message = bot.send_photo(TELEGRAM_CHANNEL_ID, message.photo[0].file_id, caption=body)
    elif message.document:
        sent_message = bot.send_document(TELEGRAM_CHANNEL_ID, message.effective_attachment.file_id, caption=body)
    else:
        sent_message = bot.send_message(TELEGRAM_CHANNEL_ID, body)

    context.user_data["sent_message"] = sent_message

    # TODO: Possible clean user_data
    return ConversationHandler.END


def cancel(update, context):
    # TODO: Possible clean user_data
    return ConversationHandler.END


handler = ConversationHandler(
    entry_points=[CommandHandler("make_post", start_post)],
    states={
        PARSE_POST: [MessageHandler(Filters.all & ~Filters.command, parse_post_info)],
        ASK_TAGS: [MessageHandler(Filters.all & ~Filters.command, rewrite_tags_and_validate_step)],
        MAKE_CALENDAR_NOTIFICATIONS: [
            MessageHandler(Filters.regex(r"(да|\+|lf)"), ask_calendar_title),
            MessageHandler(Filters.all, ask_calendar_notification),
        ],
        NOTIFY_USERS_IN_PM: [
            MessageHandler(Filters.regex(r"(да|\+|lf)"), notify_users),
            MessageHandler(Filters.all, make_post),
        ],
        ADD_TO_CALENDAR: [MessageHandler(Filters.text & ~Filters.command, add_to_calendar)]
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)
