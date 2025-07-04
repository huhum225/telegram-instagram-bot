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
