"""Flask web application for Bonus Points Dashboard."""

import logging
from typing import Optional

from flask import Flask
from flask_wtf.csrf import CSRFProtect

from flask_session import Session
from web.config import WebConfig
from web.database import Database
from web.middleware import register_middleware
from web.routes.api import api_bp
from web.routes.pages import pages_bp

logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(WebConfig)
Session(app)
CSRFProtect(app)

# Initialize database
db = Database(str(WebConfig.DB_PATH))
logger.info(f"Web dashboard using database: {WebConfig.DB_PATH}")

# Register blueprints
app.register_blueprint(pages_bp)
app.register_blueprint(api_bp)

# Register middleware (logging, session refresh)
register_middleware(app)


@app.teardown_appcontext
def close_db_connection(exception: Optional[BaseException] = None) -> None:
    """Close database connection at the end of each request."""
    db.close_connection()


def run_web() -> None:
    """Run the Flask web server."""
    logger.info("=" * 80)
    logger.info("Starting Bonus Points Web Dashboard...")
    logger.info(f"   Host: {WebConfig.HOST}")
    logger.info(f"   Port: {WebConfig.PORT}")
    logger.info(f"   Database: {WebConfig.DB_PATH}")
    logger.info("=" * 80)

    app.run(
        host=WebConfig.HOST,
        port=WebConfig.PORT,
        debug=WebConfig.DEBUG,
        use_reloader=False,
    )


if __name__ == "__main__":
    run_web()
