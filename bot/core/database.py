# bonus_points_bot/bot/core/database.py
"""Database operations module - FIXED with smart date handling."""

import logging
import sqlite3
from datetime import datetime, time, timedelta, timezone
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)


class Database:
    """Handles all database operations for the bot."""

    def __init__(self, db_path: str = "bonus_points.db"):
        self.db_path = db_path
        logger.info(f"Initializing database at: {db_path}")
        self.init_db()
        logger.info("Database initialization complete")

    def get_connection(self):
        """Get a database connection with performance optimizations."""
        conn = sqlite3.connect(self.db_path)

        # Write-Ahead Logging mode - better concurrency
        conn.execute("PRAGMA journal_mode=WAL")

        # Increase cache size from 2MB to 10MB
        conn.execute("PRAGMA cache_size=-10000")

        # Faster synchronization (safe for Discord bot use case)
        conn.execute("PRAGMA synchronous=NORMAL")

        # Use memory for temporary tables
        conn.execute("PRAGMA temp_store=MEMORY")

        return conn

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
                    completed_at TEXT,
                    UNIQUE(user_id, activity_id, date)
                )
            """)
            logger.debug("Activities table created/verified")

            # Add completed_at column to existing tables
            try:
                cursor.execute("ALTER TABLE activities ADD COLUMN completed_at TEXT")
                logger.info("Added completed_at column to activities table")
            except sqlite3.OperationalError:
                # Column already exists
                logger.debug("completed_at column already exists")

            # Settings table for persistent config
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)
            logger.debug("Settings table created/verified")

            # Dashboard messages table for persistent dashboard tracking
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS dashboard_messages (
                    user_id TEXT PRIMARY KEY,
                    channel_id TEXT NOT NULL,
                    message_id TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    last_updated TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            logger.debug("Dashboard messages table created/verified")

            # ============================================================
            # OPTIMIZED INDEXES - Much faster queries!
            # ============================================================

            # Primary lookup index - covers most queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_activities_lookup 
                ON activities(user_id, date, activity_id)
            """)

            # Specialized index for autocomplete (finding completed activities)
            # Partial index only includes completed=1 rows (smaller, faster)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_activities_completed 
                ON activities(user_id, date) WHERE completed = 1
            """)

            # Index for date-based queries (cleanup, daily reset)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_activities_date 
                ON activities(date)
            """)

            # Covering index for status checks (includes completed in index)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_activities_status
                ON activities(user_id, activity_id, date, completed)
            """)

            logger.debug("Activity indexes created/verified")

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
            f"User {user_id} earned {amount} BP (Balance: {current_balance} â†’ {new_balance})"
        )
        return new_balance

    def subtract_user_bp(self, user_id: int, amount: int) -> int:
        """Subtract BP from user's balance."""
        current_balance = self.get_user_bp_balance(user_id)
        new_balance = current_balance - amount
        self.set_user_bp_balance(user_id, new_balance)
        logger.info(
            f"User {user_id} lost {amount} BP (Balance: {current_balance} â†’ {new_balance})"
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
            # Set completed_at to current UTC time when completing, NULL when uncompleting
            completed_at = datetime.now(timezone.utc).isoformat() if completed else None
            cursor.execute(
                """
                INSERT INTO activities (user_id, activity_id, date, completed, completed_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(user_id, activity_id, date) 
                DO UPDATE SET completed = ?, completed_at = ?
            """,
                (
                    str(user_id),
                    activity_id,
                    date,
                    int(completed),
                    completed_at,
                    int(completed),
                    completed_at,
                ),
            )
            conn.commit()

    def get_user_completed_activities(self, user_id: int, date: str) -> List[str]:
        """Get list of completed activities for a user on a specific date, sorted by completion time (most recent first)."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT activity_id FROM activities 
                WHERE user_id = ? AND date = ? AND completed = 1
                ORDER BY completed_at DESC NULLS LAST
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

    # Dashboard persistence methods
    def save_dashboard_message(self, user_id: int, channel_id: int, message_id: int):
        """Save dashboard message IDs to database for persistence."""
        logger.info(
            f"Saving dashboard for user {user_id}: channel={channel_id}, message={message_id}"
        )
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO dashboard_messages (user_id, channel_id, message_id, last_updated)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET 
                    channel_id = ?,
                    message_id = ?,
                    last_updated = ?
            """,
                (
                    str(user_id),
                    str(channel_id),
                    str(message_id),
                    datetime.utcnow().isoformat(),
                    str(channel_id),
                    str(message_id),
                    datetime.utcnow().isoformat(),
                ),
            )
            conn.commit()

    def get_dashboard_message(self, user_id: int) -> Optional[Tuple[int, int]]:
        """Get saved dashboard message IDs for a user.

        Returns:
            Tuple of (channel_id, message_id) or None if not found
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT channel_id, message_id 
                FROM dashboard_messages 
                WHERE user_id = ?
            """,
                (str(user_id),),
            )
            result = cursor.fetchone()
            if result:
                channel_id = int(result[0])
                message_id = int(result[1])
                logger.debug(
                    f"Retrieved dashboard for user {user_id}: channel={channel_id}, message={message_id}"
                )
                return (channel_id, message_id)
            return None

    def delete_dashboard_message(self, user_id: int):
        """Delete dashboard message record for a user."""
        logger.info(f"Deleting dashboard record for user {user_id}")
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM dashboard_messages WHERE user_id = ?", (str(user_id),)
            )
            conn.commit()

    def get_all_dashboard_messages(self) -> List[Tuple[int, int, int]]:
        """Get all saved dashboard messages.

        Returns:
            List of tuples: (user_id, channel_id, message_id)
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT user_id, channel_id, message_id FROM dashboard_messages"
            )
            results = cursor.fetchall()
            return [(int(row[0]), int(row[1]), int(row[2])) for row in results]

    def optimize_database(self):
        """Run VACUUM and ANALYZE to optimize database performance."""
        logger.info("Running database optimization...")
        with self.get_connection() as conn:
            conn.execute("VACUUM")
            conn.execute("ANALYZE")
        logger.info("Database optimization complete")


def get_today_date() -> str:
    """
    Get today's activity date in UTC (07:00 MSK = 04:00 UTC).

    Returns the "activity day" which continues until 04:00 UTC:
    - From 00:00 to 03:59 UTC â†’ Returns YESTERDAY's date (activities still valid)
    - From 04:00 to 23:59 UTC â†’ Returns TODAY's date (new activity day)

    This prevents the "midnight reset bug" where progress appears at 0
    between 00:00-04:00 UTC before the actual daily reset runs.
    """
    now = datetime.now(timezone.utc)
    reset_time_utc = time(hour=4, minute=0)  # 07:00 MSK = 04:00 UTC

    if now.time() < reset_time_utc:
        # Still in previous activity day
        yesterday = now - timedelta(days=1)
        date = yesterday.strftime("%Y-%m-%d")
        logger.debug(
            f"Before reset time ({now.time()} < 04:00 UTC / 07:00 MSK) - using activity date: {date}"
        )
    else:
        # In current activity day
        date = now.strftime("%Y-%m-%d")
        logger.debug(
            f"After reset time ({now.time()} >= 04:00 UTC / 07:00 MSK) - using activity date: {date}"
        )

    return date


def get_actual_date() -> str:
    """Get the actual calendar date in UTC."""
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return date
