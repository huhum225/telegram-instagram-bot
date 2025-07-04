import logging
from flask import request, render_template, jsonify
from app import app, db
from models import User, BalanceRequest, Order
import telebot
from bot import bot, start_bot_service

@app.route('/')
def status():
    """Status page to monitor bot health"""
    try:
        with app.app_context():
            user_count = User.query.count()
            pending_requests = BalanceRequest.query.filter_by(status="pending").count()
            pending_orders = Order.query.filter_by(status="pending").count()
            completed_orders = Order.query.filter_by(status="completed").count()
            
        stats = {
            'users': user_count,
            'pending_requests': pending_requests,
            'pending_orders': pending_orders,
            'completed_orders': completed_orders,
            'bot_status': 'Active'
        }
        
        return render_template('status.html', stats=stats)
    except Exception as e:
        logging.error(f"Status page error: {e}")
        return render_template('status.html', stats={'bot_status': 'Error'})

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle incoming webhook from Telegram"""
    try:
        if request.headers.get('content-type') == 'application/json':
            json_string = request.get_data().decode('utf-8')
            update = telebot.types.Update.de_json(json_string)
            bot.process_new_updates([update])
            return '', 200
        else:
            return 'Bad Request', 400
    except Exception as e:
        logging.error(f"Webhook error: {e}")
        return 'Error', 500

@app.route('/api/stats')
def api_stats():
    """API endpoint for bot statistics"""
    try:
        with app.app_context():
            user_count = User.query.count()
            pending_requests = BalanceRequest.query.filter_by(status="pending").count()
            pending_orders = Order.query.filter_by(status="pending").count()
            completed_orders = Order.query.filter_by(status="completed").count()
            
        return jsonify({
            'users': user_count,
            'pending_requests': pending_requests,
            'pending_orders': pending_orders,
            'completed_orders': completed_orders,
            'status': 'active'
        })
    except Exception as e:
        logging.error(f"API stats error: {e}")
        return jsonify({'error': 'Database error'}), 500

@app.route('/health')
def health_check():
    """Health check endpoint"""
    try:
        with app.app_context():
            from sqlalchemy import text
            db.session.execute(text('SELECT 1'))
        return jsonify({'status': 'healthy'}), 200
    except Exception as e:
        logging.error(f"Health check error: {e}")
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

# Start bot service on application startup
with app.app_context():
    start_bot_service()
