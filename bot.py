import os
import logging
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from app import app, db
from models import User, BalanceRequest, Order
from datetime import datetime

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Bot configuration
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
ADMIN_IDS = [int(x.strip()) for x in os.environ.get("ADMIN_IDS", "").split(",") if x.strip()]
INSTAGRAM_FEE = 2500
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")

# Validate required environment variables
if not BOT_TOKEN:
    logger.error("BOT_TOKEN environment variable is not set!")
    raise ValueError("BOT_TOKEN is required")

if not ADMIN_IDS:
    logger.warning("No ADMIN_IDS specified, admin features will be disabled")

# Follower prices
FOLLOWER_PRICES = {
    "1k": 100, "2k": 200, "3k": 300, "4k": 400, "5k": 500,
    "6k": 600, "7k": 700, "8k": 800, "9k": 900, "10k": 1000
}

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

def is_admin(user_id):
    """Check if user is admin"""
    return int(user_id) in ADMIN_IDS

def get_or_create_user(telegram_user):
    """Get or create user in database"""
    try:
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
                logger.info(f"Created new user: {telegram_user.id}")
            return user
    except Exception as e:
        logger.error(f"Error in get_or_create_user: {e}")
        raise

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
        markup.add(*[KeyboardButton(btn) for btn in btn_row])
    
    return markup

def create_follower_menu():
    """Create follower package menu"""
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = []
    
    for k, price in FOLLOWER_PRICES.items():
        buttons.append(KeyboardButton(f"{k} Takipçi - {price}₺"))
    
    buttons.append(KeyboardButton("🎯 Özel Miktar"))
    buttons.append(KeyboardButton("❌ İptal"))
    
    markup.add(*buttons)
    return markup

@bot.message_handler(commands=['start', 'help'])
def start(message):
    try:
        user = get_or_create_user(message.from_user)
        bot.send_message(
            message.chat.id,
            "🤖 Hoşgeldiniz! Aşağıdaki butonlardan işleminizi seçin",
            reply_markup=create_menu(message.from_user.id)
        )
        logger.info(f"User {user.telegram_id} started the bot")
    except Exception as e:
        logger.error(f"Start command error: {e}")
        bot.send_message(message.chat.id, "❌ Bir hata oluştu, lütfen tekrar deneyin")

@bot.message_handler(func=lambda m: m.text == "💳 Bakiye Sorgula")
def show_balance(message):
    try:
        with app.app_context():
            user = User.query.filter_by(telegram_id=str(message.from_user.id)).first()
            if not user:
                raise ValueError("User not found")
            
            bot.send_message(
                message.chat.id,
                f"💰 Bakiyeniz: {user.balance}₺",
                reply_markup=create_menu(message.from_user.id)
            )
            logger.info(f"Balance checked for user {user.telegram_id}")
    except Exception as e:
        logger.error(f"Balance query error: {e}")
        bot.send_message(message.chat.id, "❌ Bakiye sorgulanırken hata oluştu")

def process_receipt(message, amount):
    """Process payment receipt"""
    try:
        if message.text == "❌ İptal":
            bot.send_message(
                message.chat.id,
                "İşlem iptal edildi",
                reply_markup=create_menu(message.from_user.id)
            )
            return

        if not message.photo:
            raise ValueError("No photo provided")

        # Save receipt information
        with app.app_context():
            request = BalanceRequest(
                user_id=str(message.from_user.id),
                amount=amount,
                photo_id=message.photo[-1].file_id,
                status="pending"
            )
            db.session.add(request)
            db.session.commit()

        # Notify admins
        for admin_id in ADMIN_IDS:
            try:
                bot.send_photo(
                    admin_id,
                    message.photo[-1].file_id,
                    caption=f"Yeni bakiye talebi!\n\nKullanıcı: @{message.from_user.username}\nMiktar: {amount}₺\nID: {request.id}"
                )
            except Exception as e:
                logger.error(f"Could not notify admin {admin_id}: {e}")

        bot.send_message(
            message.chat.id,
            "✅ Dekontunuz alındı! En kısa sürede işleme alınacaktır.",
            reply_markup=create_menu(message.from_user.id)
        )
        logger.info(f"New balance request from {message.from_user.id} for {amount}₺")
    except Exception as e:
        logger.error(f"Receipt processing error: {e}")
        bot.send_message(message.chat.id, "❌ İşlem sırasında hata oluştu")

def setup_webhook():
    """Setup webhook for the bot"""
    if not WEBHOOK_URL:
        logger.warning("WEBHOOK_URL not set, skipping webhook setup")
        return False

    try:
        bot.remove_webhook()
        webhook_url = f"{WEBHOOK_URL.rstrip('/')}/webhook"
        bot.set_webhook(url=webhook_url)
        logger.info(f"Webhook successfully set to: {webhook_url}")
        return True
    except Exception as e:
        logger.error(f"Webhook setup failed: {e}")
        return False

def run_bot():
    """Main function to run the bot"""
    try:
        if WEBHOOK_URL:
            if setup_webhook():
                logger.info("Bot running in webhook mode")
                return
        
        logger.info("Bot running in polling mode")
        bot.infinity_polling()
    except Exception as e:
        logger.critical(f"Bot failed to start: {e}")
        raise

if __name__ == '__main__':
    run_bot()
