from app import app
from routes import *  # noqa: F401, F403
import logging
import os

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app():
    """Application factory pattern"""
    # Additional configuration can be added here
    return app

if __name__ == "__main__":
    try:
        port = int(os.environ.get("PORT", 5000))
        app = create_app()
        
        # Production/development environment check
        debug_mode = os.environ.get("FLASK_ENV", "development") == "development"
        
        logger.info(f"Starting server on port {port} (Debug: {debug_mode})")
        app.run(
            host="0.0.0.0",
            port=port,
            debug=debug_mode,
            use_reloader=debug_mode
        )
    except Exception as e:
        logger.critical(f"Failed to start application: {str(e)}")
        raise
