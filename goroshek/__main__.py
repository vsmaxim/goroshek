from telegram.ext import Updater

from goroshek.commands.make_post import handler as make_post_handler
from goroshek.commands.start_bot import handler as start_handler
from goroshek.config import TELEGRAM_BOT_TOKEN

updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)

dispatcher = updater.dispatcher

dispatcher.add_handler(make_post_handler)
dispatcher.add_handler(start_handler)

updater.start_polling()
updater.idle()
