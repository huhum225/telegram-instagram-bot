from app import db
from datetime import datetime
from sqlalchemy import event, ForeignKey
from sqlalchemy.orm import validates, relationship

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    telegram_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    username = db.Column(db.String(100), index=True)
    first_name = db.Column(db.String(100))
    balance = db.Column(db.Float, default=0.0, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    # Relationships
    balance_requests = relationship("BalanceRequest", back_populates="user")
    orders = relationship("Order", back_populates="user")

class BalanceRequest(db.Model):
    __tablename__ = 'balance_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), ForeignKey('users.telegram_id'), nullable=False)
    # ... (diğer alanlar)

    # Relationship
    user = relationship("User", back_populates="balance_requests")

class Order(db.Model):
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), ForeignKey('users.telegram_id'), nullable=False)
    # ... (diğer alanlar)

    # Relationship
    user = relationship("User", back_populates="orders")

# Indexler
event.listen(User.__table__, 'after_create', db.Index('idx_user_telegram_id', User.telegram_id))
