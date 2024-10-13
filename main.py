import os
import re
import sqlite3

from url_shortener_skipper.Parser import PublicEarn
from telegram import Update

from telegram.ext import Updater, CommandHandler, ContextTypes, ApplicationBuilder, MessageHandler, filters
from dotenv import load_dotenv

# Create a SQLite database connection
conn = sqlite3.connect("telegram_data.db",check_same_thread=False)
cursor = conn.cursor()

# Create the user_messages table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        message TEXT,
        chat_id INTEGER,
        message_id INTEGER,
        update_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
""")
conn.commit()
conn.close()

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

async def store_message(update):
    conn = sqlite3.connect("telegram_data.db")
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO user_messages (
                user_id,
                message,
                chat_id,
                message_id,
                update_id
            ) VALUES (?, ?, ?, ?, ?)
        """, (
            update.effective_user.id,
            update.message.text,
            update.message.chat_id,
            update.message.message_id,
            update.update_id
        ))
        conn.commit()
        conn.close()
    except sqlite3.OperationalError as e:
        print(e)
        conn.close()
        return



async def handle_text_message(update, context):
    await store_message(update)
    await handle_message(update, context)

app.add_handler(CommandHandler("hello", hello))
app.add_handler(CommandHandler("start", welcome_user))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
# app.add_handler(MessageHandler(filters.TEXT, store_message))
app.run_polling()
print("started")
# url = 'https://publicearn.com/R67w'
# PublicEarn(url).process()
