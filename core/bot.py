import telebot
import os
from dotenv import load_dotenv

load_dotenv()

def create_bot():
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN not set")
    return telebot.TeleBot(token)
