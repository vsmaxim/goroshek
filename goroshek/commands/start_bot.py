from telegram.ext import CommandHandler

from goroshek.utils import save_chat_id


def collect_user_info(update, message):
    save_chat_id(update.message.chat_id, update.effective_user)
    update.message.reply_text(
        "Добро пожаловать, список доступных команд:\n"
        "- /start - выводит это сообщение и добавляет вас в список оповещаемых\n"
        "- /make_post - помогает создать пост\n"
        "Для того, чтобы перестать получать оповещения просто отпишитесь от бота."
    )


handler = CommandHandler("start", collect_user_info)
