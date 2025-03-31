from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext
import sqlite3
import base64
from flask import Flask, render_template, request
import threading

# Replace these with your actual Bot Token and Telegram User ID
TOKEN = "YOUR_BOT_TOKEN"
ADMIN_ID = "YOUR_TELEGRAM_ID"

bot = Bot(token=TOKEN)

# Flask Admin Panel Setup
app = Flask(__name__)

def encrypt_text(text):
    return base64.b64encode(text.encode()).decode()

def decrypt_text(text):
    return base64.b64decode(text.encode()).decode()

# SQLite Database for storing channel IDs
conn = sqlite3.connect("bot_data.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS channels (id TEXT)")
conn.commit()

@app.route("/")
def index():
    cursor.execute("SELECT * FROM channels")
    channels = cursor.fetchall()
    return render_template("index.html", channels=channels)

@app.route("/add_channel", methods=["POST"])
def add_channel():
    channel_id = request.form.get("channel_id")
    cursor.execute("INSERT INTO channels (id) VALUES (?)", (channel_id,))
    conn.commit()
    return "Channel Added!"

@app.route("/post_message", methods=["POST"])
def post_message():
    text = request.form.get("message")
    button_text = request.form.get("button_text")
    button_url = request.form.get("button_url")
    encrypted_text = encrypt_text(text)

    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton(button_text, url=button_url)]])
    
    cursor.execute("SELECT id FROM channels")
    channels = cursor.fetchall()
    for channel in channels:
        bot.send_message(chat_id=channel[0], text=encrypted_text, reply_markup=keyboard)
    
    return "Message Sent!"

# Telegram Bot Command Handlers
def start(update: Update, context: CallbackContext):
    if str(update.message.chat_id) == ADMIN_ID:
        update.message.reply_text("Welcome Admin! Use /post <message> to send messages.")

def post(update: Update, context: CallbackContext):
    if str(update.message.chat_id) == ADMIN_ID:
        message = " ".join(context.args)
        encrypted_text = encrypt_text(message)
        
        cursor.execute("SELECT id FROM channels")
        channels = cursor.fetchall()
        for channel in channels:
            bot.send_message(chat_id=channel[0], text=encrypted_text)
        
        update.message.reply_text("Message sent successfully!")

# Setting Up the Telegram Bot
updater = Updater(token=TOKEN, use_context=True)
dp = updater.dispatcher
dp.add_handler(CommandHandler("start", start))
dp.add_handler(CommandHandler("post", post, pass_args=True))

# Run the Flask admin panel and the Telegram bot concurrently
def run_flask():
    app.run(host='0.0.0.0', port=5000)

threading.Thread(target=run_flask).start()
updater.start_polling()
