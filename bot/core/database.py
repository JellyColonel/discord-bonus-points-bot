# bonus_points_bot/bot/core/database.py
"""Database operations module."""

import logging
import sqlite3
from datetime import datetime
from typing import List, Optional

import pytz

logger = logging.getLogger(__name__)


class Database:
    """Handles all database operations for the bot."""

    def __init__(self, db_path: str = "bonus_points.db"):
        self.db_path = db_path
        logger.info(f"Initializing database at: {db_path}")
        self.init_db()
        logger.info("Database initialization complete")

    def get_connection(self):
        """Get a database connection."""
        return sqlite3.connect(self.db_path)

    def init_db(self):
        """Initialize database tables."""
        logger.info("Creating/verifying database tables...")
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Users table with bp_balance column
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    vip_status INTEGER DEFAULT 0,
                    bp_balance INTEGER DEFAULT 0
                )
            """)
            logger.debug("Users table created/verified")

            # Try to add bp_balance column to existing users table
            try:
                cursor.execute(
                    "ALTER TABLE users ADD COLUMN bp_balance INTEGER DEFAULT 0"
                )
                logger.info("Added bp_balance column to users table")
            except sqlite3.OperationalError:
                # Column already exists
                logger.debug("bp_balance column already exists")

            # Activities table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS activities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    activity_id TEXT,
                    completed INTEGER DEFAULT 0,
                    date TEXT,
                    UNIQUE(user_id, activity_id, date)
                )
            """)
            logger.debug("Activities table created/verified")

            # Settings table for persistent config
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)
            logger.debug("Settings table created/verified")

            # Add index for faster activity queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_activities_lookup 
                ON activities(user_id, date, activity_id)
            """)
            logger.debug("Activity index created/verified")

            conn.commit()
        logger.info("Database tables ready")

    # User VIP methods
    def get_user_vip_status(self, user_id: int) -> bool:
        """Get user's VIP status."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT vip_status FROM users WHERE user_id = ?", (str(user_id),)
            )
            result = cursor.fetchone()
            vip = bool(result[0]) if result else False
            logger.debug(f"User {user_id} VIP status: {vip}")
            return vip

    def set_user_vip_status(self, user_id: int, vip_status: bool):
        """Set user's VIP status."""
        logger.info(f"Setting VIP status for user {user_id}: {vip_status}")
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO users (user_id, vip_status) VALUES (?, ?)
                ON CONFLICT(user_id) DO UPDATE SET vip_status = ?
            """,
                (str(user_id), int(vip_status), int(vip_status)),
            )
            conn.commit()

    # BP Balance methods
    def get_user_bp_balance(self, user_id: int) -> int:
        """Get user's current BP balance."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT bp_balance FROM users WHERE user_id = ?", (str(user_id),)
            )
            result = cursor.fetchone()
            balance = result[0] if result else 0
            logger.debug(f"User {user_id} balance: {balance} BP")
            return balance

    def set_user_bp_balance(self, user_id: int, balance: int):
        """Set user's BP balance."""
        logger.info(f"Setting balance for user {user_id}: {balance} BP")
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO users (user_id, bp_balance) VALUES (?, ?)
                ON CONFLICT(user_id) DO UPDATE SET bp_balance = ?
            """,
                (str(user_id), int(balance), int(balance)),
            )
            conn.commit()

    def add_user_bp(self, user_id: int, amount: int) -> int:
        """Add BP to user's balance."""
        current_balance = self.get_user_bp_balance(user_id)
        new_balance = current_balance + amount
        self.set_user_bp_balance(user_id, new_balance)
        logger.info(
            f"User {user_id} earned {amount} BP (Balance: {current_balance} → {new_balance})"
        )
        return new_balance

    def subtract_user_bp(self, user_id: int, amount: int) -> int:
        """Subtract BP from user's balance."""
        current_balance = self.get_user_bp_balance(user_id)
        new_balance = current_balance - amount
        self.set_user_bp_balance(user_id, new_balance)
        logger.info(
            f"User {user_id} lost {amount} BP (Balance: {current_balance} → {new_balance})"
        )
        return new_balance

    # Activity methods
    def get_activity_status(self, user_id: int, activity_id: str, date: str) -> bool:
        """Check if an activity is completed."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT completed FROM activities 
                WHERE user_id = ? AND activity_id = ? AND date = ?
            """,
                (str(user_id), activity_id, date),
            )
            result = cursor.fetchone()
            completed = bool(result[0]) if result else False
            logger.debug(
                f"Activity status for user {user_id}, activity {activity_id}, date {date}: {completed}"
            )
            return completed

    def set_activity_status(
        self, user_id: int, activity_id: str, date: str, completed: bool
    ):
        """Set activity completion status."""
        logger.info(
            f"User {user_id} {'completed' if completed else 'uncompleted'} activity {activity_id} on {date}"
        )
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO activities (user_id, activity_id, date, completed)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id, activity_id, date) 
                DO UPDATE SET completed = ?
            """,
                (str(user_id), activity_id, date, int(completed), int(completed)),
            )
            conn.commit()

    def get_user_completed_activities(self, user_id: int, date: str) -> List[str]:
        """Get list of completed activities for a user on a specific date."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT activity_id FROM activities 
                WHERE user_id = ? AND date = ? AND completed = 1
            """,
                (str(user_id), date),
            )
            results = cursor.fetchall()
            activity_list = [row[0] for row in results]
            logger.debug(
                f"User {user_id} completed {len(activity_list)} activities on {date}"
            )
            return activity_list

    # Settings methods
    def get_setting(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get a setting value from database."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
            result = cursor.fetchone()
            value = result[0] if result else default
            logger.debug(f"Get setting {key}: {value}")
            return value

    def set_setting(self, key: str, value: str):
        """Set a setting value in database."""
        logger.info(f"Setting {key} = {value}")
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO settings (key, value) VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value = ?
            """,
                (key, str(value), str(value)),
            )
            conn.commit()


def get_today_date() -> str:
    """Get today's date in Moscow timezone."""
    moscow_tz = pytz.timezone("Europe/Moscow")
    date = datetime.now(moscow_tz).strftime("%Y-%m-%d")
    return date
