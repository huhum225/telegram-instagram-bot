import logging
from flask import request, render_template, jsonify
from app import app, db
from models import User, BalanceRequest, Order
import telebot
from bot import bot, start_bot_service
from sqlalchemy import text
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.route('/')
def status():
    """Status page to monitor bot health with detailed statistics"""
    try:
        with app.app_context():
            stats = {
                'users': User.query.count(),
                'pending_requests': BalanceRequest.query.filter_by(status="pending").count(),
                'pending_orders': Order.query.filter_by(status="pending").count(),
                'completed_orders': Order.query.filter_by(status="completed").count(),
                'last_updated': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC'),
                'bot_status': 'Active'
            }
        
        return render_template('status.html', stats=stats)
    except Exception as e:
        logger.error(f"Status page error: {e}", exc_info=True)
        return render_template('error.html', error_message="Could not load statistics"), 500

@app.route('/webhook', methods=['POST'])
def webhook():
    """Secure webhook endpoint for Telegram updates"""
    # Verify secret token if needed
    if request.headers.get('X-Telegram-Bot-Api-Secret-Token') != os.environ.get('WEBHOOK_SECRET'):
        logger.warning("Unauthorized webhook attempt")
        return 'Unauthorized', 401
        
    if request.headers.get('content-type') == 'application/json':
        try:
            json_data = request.get_json()
            update = telebot.types.Update.de_json(json_data)
            bot.process_new_updates([update])
            return '', 200
        except Exception as e:
            logger.error(f"Webhook processing error: {e}", exc_info=True)
            return 'Internal Server Error', 500
    return 'Bad Request', 400

@app.route('/api/stats')
def api_stats():
    """API endpoint for bot statistics with caching headers"""
    try:
        with app.app_context():
            data = {
                'users': User.query.count(),
                'pending_requests': BalanceRequest.query.filter_by(status="pending").count(),
                'pending_orders': Order.query.filter_by(status="pending").count(),
                'completed_orders': Order.query.filter_by(status="completed").count(),
                'timestamp': datetime.utcnow().isoformat()
            }
            
        response = jsonify(data)
        response.headers['Cache-Control'] = 'public, max-age=60'
        return response
    except Exception as e:
        logger.error(f"API stats error: {e}", exc_info=True)
        return jsonify({'error': 'Database unavailable'}), 503

@app.route('/health')
def health_check():
    """Comprehensive health check endpoint"""
    try:
        # Database health check
        with app.app_context():
            db.session.execute(text('SELECT 1'))
            
        # Bot health check
        bot_info = bot.get_me() if hasattr(bot, 'get_me') else None
        
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'bot': 'running' if bot_info else 'inactive',
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        logger.critical(f"Health check failed: {e}", exc_info=True)
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@app.before_first_request
def initialize_bot():
    """Initialize bot service on first request"""
    try:
        with app.app_context():
            start_bot_service()
            logger.info("Bot service initialized successfully")
    except Exception as e:
        logger.error(f"Bot initialization failed: {e}", exc_info=True)
        raise RuntimeError("Failed to start bot service")

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('error.html', error_message="Page not found"), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html', error_message="Internal server error"), 500
