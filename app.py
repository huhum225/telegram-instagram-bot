import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Logging Configuration
logging.basicConfig(level=logging.INFO)
app_logger = logging.getLogger(__name__)

# SQLAlchemy 2.x Base Class
class Base(DeclarativeBase):
    pass

# Database Setup
db = SQLAlchemy(model_class=Base)

# Flask Application
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "fallback-dev-key-123")

# PostgreSQL URL Fix for Render
database_url = os.environ.get("DATABASE_URL", "").replace("postgres://", "postgresql://")
app.config["SQLALCHEMY_DATABASE_URI"] = database_url or "postgresql://localhost/telegram_bot"
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
    "connect_args": {"options": "-c timezone=utc"}
}

# ProxyFix for Render
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

# Initialize DB
db.init_app(app)

# Import Models and Create Tables
with app.app_context():
    try:
        from models import *  # noqa: F401, F403
        db.create_all()
        app_logger.info("Database tables created successfully.")
    except Exception as e:
        app_logger.error(f"Failed to create database tables: {str(e)}")
        raise

# Health Check Endpoint
@app.route("/")
def health_check():
    return "Server is running", 200

# Gunicorn Entry Point
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
