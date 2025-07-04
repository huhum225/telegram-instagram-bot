from flask import Blueprint, request, jsonify
from app import app, db
from models import User, BalanceRequest, Order
from sqlalchemy import text
from datetime import datetime
import logging

bp = Blueprint('main', __name__)
logger = logging.getLogger(__name__)

def init_routes(app):
    app.register_blueprint(bp)

@bp.route('/health')
def health_check():
    try:
        db.session.execute(text('SELECT 1'))
        return jsonify({'status': 'healthy'}), 200
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({'status': 'unhealthy'}), 500

# Diğer route'lar...
