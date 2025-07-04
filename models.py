from app import db
from datetime import datetime
from sqlalchemy import event
from sqlalchemy.orm import validates

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
    balance_requests = db.relationship('BalanceRequest', backref='user', lazy=True)
    orders = db.relationship('Order', backref='user', lazy=True)
    
    @validates('balance')
    def validate_balance(self, key, balance):
        if balance < 0:
            raise ValueError("Balance cannot be negative")
        return balance
    
    def __repr__(self):
        return f'<User {self.telegram_id}>'

class BalanceRequest(db.Model):
    __tablename__ = 'balance_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.String(100), unique=True, nullable=False, index=True)
    user_id = db.Column(db.String(50), db.ForeignKey('users.telegram_id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    receipt_photo_id = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(20), default='pending', nullable=False)  # pending, approved, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    processed_at = db.Column(db.DateTime)
    admin_notes = db.Column(db.Text)
    
    @validates('amount')
    def validate_amount(self, key, amount):
        if amount <= 0:
            raise ValueError("Amount must be positive")
        return amount
    
    @validates('status')
    def validate_status(self, key, status):
        if status not in ['pending', 'approved', 'rejected']:
            raise ValueError("Invalid status")
        return status
    
    def __repr__(self):
        return f'<BalanceRequest {self.request_id}>'

class Order(db.Model):
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.String(100), unique=True, nullable=False, index=True)
    user_id = db.Column(db.String(50), db.ForeignKey('users.telegram_id'), nullable=False)
    order_type = db.Column(db.String(50), nullable=False)  # instagram_close, followers
    target_account = db.Column(db.String(100))
    follower_count = db.Column(db.String(20))
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending', nullable=False)  # pending, completed, cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    completed_at = db.Column(db.DateTime)
    admin_notes = db.Column(db.Text)
    
    @validates('amount')
    def validate_amount(self, key, amount):
        if amount <= 0:
            raise ValueError("Amount must be positive")
        return amount
    
    @validates('status')
    def validate_status(self, key, status):
        if status not in ['pending', 'completed', 'cancelled']:
            raise ValueError("Invalid status")
        return status
    
    def __repr__(self):
        return f'<Order {self.order_id}>'

# Indexes
event.listen(User.__table__, 'after_create', db.Index('idx_user_telegram_id', User.telegram_id))
event.listen(BalanceRequest.__table__, 'after_create', db.Index('idx_balance_request_status', BalanceRequest.status))
event.listen(Order.__table__, 'after_create', db.Index('idx_order_status', Order.status))
