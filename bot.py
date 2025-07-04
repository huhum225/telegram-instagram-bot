import os
import logging
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from app import app, db
from models import User, BalanceRequest, Order
from datetime import datetime

# Bot configuration
BOT_TOKEN = os.environ.get("BOT_TOKEN", "7943298261:AAF6cXs8se-_5g4TD4kCR0IiuzT7bcHwrbk")
ADMIN_IDS = [int(x.strip()) for x in os.environ.get("ADMIN_IDS", "7235030800").split(",")]
INSTAGRAM_FEE = 2500
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")

# Follower prices
FOLLOWER_PRICES = {
    "1k": 100, "2k": 200, "3k": 300, "4k": 400, "5k": 500,
    "6k": 600, "7k": 700, "8k": 800, "9k": 900, "10k": 1000
}

bot = telebot.TeleBot(BOT_TOKEN)

def is_admin(user_id):
    return int(user_id) in ADMIN_IDS

def get_or_create_user(telegram_user):
    """Get or create user in database"""
    with app.app_context():
        user = User.query.filter_by(telegram_id=str(telegram_user.id)).first()
        if not user:
            user = User(
                telegram_id=str(telegram_user.id),
                username=telegram_user.username,
                first_name=telegram_user.first_name,
                balance=0.0
            )
            db.session.add(user)
            db.session.commit()
        return user

def create_menu(user_id):
    """Create main menu keyboard"""
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    
    buttons = [
        ["📷 Instagram Hesap Kapat"],
        ["📈 Instagram Takipçi Satın Al"],
        ["💰 Bakiye Yükle"],
        ["💳 Bakiye Sorgula"]
    ]
    
    if is_admin(user_id):
        buttons.append(["🔐 Tüm Bakiyeler"])
        buttons.append(["📊 Bakiye Talepleri"])
        buttons.append(["🔄 Bekleyen İşlemler"])
    
    for btn_row in buttons:
        markup.add(*btn_row)
    
    return markup

def create_follower_menu():
    """Create follower package menu"""
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = []
    
    for k, price in FOLLOWER_PRICES.items():
        buttons.append(f"{k} Takipçi - {price}₺")
    
    buttons.append("🎯 Özel Miktar")
    buttons.append("❌ İptal")
    
    markup.add(*buttons)
    return markup

# Message handlers
@bot.message_handler(commands=['start'])
def start(message):
    try:
        get_or_create_user(message.from_user)
        bot.send_message(
            message.chat.id,
            "🤖 Hoşgeldiniz! Aşağıdaki butonlardan işleminizi seçin",
            reply_markup=create_menu(message.from_user.id)
        )
    except Exception as e:
        logging.error(f"Start command error: {e}")
        bot.send_message(message.chat.id, "❌ Bir hata oluştu, lütfen tekrar deneyin")

@bot.message_handler(func=lambda m: m.text == "💳 Bakiye Sorgula")
def show_balance(message):
    try:
        with app.app_context():
            user = User.query.filter_by(telegram_id=str(message.from_user.id)).first()
            balance = user.balance if user else 0
            bot.send_message(
                message.chat.id,
                f"💰 Bakiyeniz: {balance}₺",
                reply_markup=create_menu(message.from_user.id)
            )
    except Exception as e:
        logging.error(f"Balance query error: {e}")
        bot.send_message(message.chat.id, "❌ Bakiye sorgulanırken hata oluştu")

@bot.message_handler(func=lambda m: m.text == "💰 Bakiye Yükle")
def request_balance(message):
    try:
        msg = bot.send_message(
            message.chat.id,
            "💵 Yüklemek istediğiniz miktarı ₺ olarak girin:\n\nÖrnek: 1000\n\nTR730001200924400066000156\nad soyad: burak beleç",
            reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).row("❌ İptal")
        )
        bot.register_next_step_handler(msg, ask_for_receipt)
    except Exception as e:
        logging.error(f"Balance request error: {e}")

def ask_for_receipt(message):
    try:
        if message.text == "❌ İptal":
            bot.send_message(
                message.chat.id,
                "İşlem iptal edildi",
                reply_markup=create_menu(message.from_user.id)
            )
            return

        amount = float(message.text)
        if amount <= 0:
            raise ValueError("Invalid amount")

        bot.send_message(
            message.chat.id,
            "📤 Lütfen dekontunuzu fotoğraf olarak gönderin:",
            reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).row("❌ İptal")
        )
        bot.register_next_step_handler(message, lambda m: process_receipt(m, amount))

    except ValueError:
        msg = bot.send_message(
            message.chat.id,
            "❌ Geçersiz miktar! Lütfen pozitif bir sayı girin (Örnek: 500)",
            reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).row("❌ İptal")
        )
        bot.register_next_step_handler(msg, ask_for_receipt)
    except Exception as e:
        logging.error(f"Receipt request error: {e}")
        bot.send_message(message.chat.id, "❌ İşlem sırasında hata oluştu")

def setup_webhook():
    """Setup webhook for the bot"""
    if WEBHOOK_URL and WEBHOOK_URL.startswith('http'):
        try:
            bot.remove_webhook()
            bot.set_webhook(url=f"{WEBHOOK_URL}/webhook")
            logging.info(f"Webhook set to: {WEBHOOK_URL}/webhook")
        except Exception as e:
            logging.error(f"Webhook setup error: {e}")
    else:
        logging.warning("WEBHOOK_URL not set or invalid, webhook not configured")

def start_polling():
    """Start polling mode for development/testing"""
    try:
        bot.remove_webhook()
        logging.info("Starting bot in polling mode...")
        bot.infinity_polling(none_stop=True, interval=1)
    except Exception as e:
        logging.error(f"Polling error: {e}")

def start_bot_service():
    """Start bot service - webhook if URL available, otherwise polling"""
    if WEBHOOK_URL and WEBHOOK_URL.startswith('http'):
        setup_webhook()
        logging.info("Bot configured for webhook mode")
    else:
        logging.info("Starting bot in polling mode (no valid webhook URL)")
        import threading
        bot_thread = threading.Thread(target=start_polling, daemon=True)
        bot_thread.start()
