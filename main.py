import os
import re
from url_shortener_skipper.Parser import PublicEarn
from telegram import Update

from telegram.ext import Updater, CommandHandler, ContextTypes, ApplicationBuilder, MessageHandler, filters
from dotenv import load_dotenv

load_dotenv()


async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f"hello {update.effective_user.first_name}")


async def welcome_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("welcome to ByPass bot, right now we support only *PublicEarn* website links only \n Send only valid url like \nhttps://publicearn.com/*** ")


app = ApplicationBuilder().token(os.getenv('Telegram_token')).build()


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_message = update.message.text
    print("process start")
    if re.match('^https://', user_message) and "publicearn" in user_message:
        for general_message in ['verified','Started Process','Ads skipping']:
            await context.bot.send_message(chat_id=update.effective_chat.id, text=general_message,reply_to_message_id=update.message.message_id)
        reply_message = PublicEarn(user_message).process()
        print("output",reply_message)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=reply_message)
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="Send only valid url like \nhttps://publicearn.com/*** ")


app.add_handler(CommandHandler("hello", hello))
app.add_handler(CommandHandler("start", welcome_user))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.run_polling()
print("started")
# url = 'https://publicearn.com/R67w'
# PublicEarn(url).process()
