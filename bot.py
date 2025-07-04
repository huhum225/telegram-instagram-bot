import os
import logging
from app import app, db
from models import User
from telebot import TeleBot, apihelper

# Logging config
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Config
BOT_TOKEN = os.environ['BOT_TOKEN']
bot = TeleBot(BOT_TOKEN)

@app.before_first_request
def init_bot():
    try:
        if os.environ.get('WEBHOOK_MODE', 'false').lower() == 'true':
            set_webhook()
        else:
            start_polling()
    except Exception as e:
        logger.error(f"Bot init failed: {e}")

def set_webhook():
    webhook_url = f"{os.environ['WEBHOOK_URL']}/webhook"
    bot.remove_webhook()
    bot.set_webhook(url=webhook_url)
    logger.info(f"Webhook set to: {webhook_url}")

def start_polling():
    logger.info("Starting bot in polling mode")
    bot.infinity_polling()

# Bot handlers...
