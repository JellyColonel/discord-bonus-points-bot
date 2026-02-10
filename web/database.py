"""Database operations module for Bonus Points Web Dashboard."""

import logging
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, time, timedelta, timezone
from typing import Generator, List, Optional, Tuple

logger = logging.getLogger(__name__)


class Database:
    """Handles all database operations for the web dashboard.

    Uses thread-local connections for efficient connection reuse.
    Each thread gets its own connection that persists across operations.
    """

    def __init__(self, db_path: str = "bonus_points.db"):
        self.db_path = db_path
        self._local = threading.local()
        self._lock = threading.Lock()
        logger.info(f"Initializing database at: {db_path}")
        self.init_db()
        logger.info("Database initialization complete")

    def _create_connection(self) -> sqlite3.Connection:
        """Create a new database connection with performance optimizations."""
        conn = sqlite3.connect(
            self.db_path,
            check_same_thread=False,  # Safe because we use thread-local storage
            timeout=30.0,  # Wait up to 30s for locks
        )

        # Write-Ahead Logging mode - better concurrency
        conn.execute("PRAGMA journal_mode=WAL")

        # Increase cache size from 2MB to 10MB
        conn.execute("PRAGMA cache_size=-10000")

        # Faster synchronization
        conn.execute("PRAGMA synchronous=NORMAL")

        # Use memory for temporary tables
        conn.execute("PRAGMA temp_store=MEMORY")

        # Enable foreign keys (good practice)
        conn.execute("PRAGMA foreign_keys=ON")

        return conn

    def get_connection(self) -> sqlite3.Connection:
        """Get a thread-local database connection.

        Returns an existing connection for this thread if available,
        otherwise creates a new one. Connections are reused within
        the same thread for better performance.
        """
        # Check if this thread already has a connection
        conn = getattr(self._local, "connection", None)

        if conn is not None:
            # Verify connection is still valid
            try:
                conn.execute("SELECT 1")
                return conn
            except sqlite3.Error:
                # Connection is broken, close it and create a new one
                logger.warning("Thread-local connection was broken, recreating")
                try:
                    conn.close()
                except Exception:
                    pass
                conn = None

        # Create new connection for this thread
        conn = self._create_connection()
        self._local.connection = conn
        logger.debug(
            f"Created new connection for thread {threading.current_thread().name}"
        )
        return conn

    @contextmanager
    def get_cursor(self, commit: bool = True) -> Generator[sqlite3.Cursor, None, None]:
        """Context manager for database operations.

        Uses thread-local connection for efficiency. The connection is
        reused across multiple operations within the same thread.

        Args:
            commit: Whether to commit after operations (default True).
                   Set to False for read-only operations.

        Yields:
            sqlite3.Cursor: Database cursor for executing queries.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            yield cursor
            if commit:
                conn.commit()
        except Exception:
            conn.rollback()
            raise

    def close_connection(self) -> None:
        """Close the connection for the current thread.

        Call this when a thread is done with database operations,
        such as at the end of a request in a web application.
        """
        conn = getattr(self._local, "connection", None)
        if conn is not None:
            try:
                conn.close()
                logger.debug(
                    f"Closed connection for thread {threading.current_thread().name}"
                )
            except Exception as e:
                logger.warning(f"Error closing connection: {e}")
            finally:
                self._local.connection = None

    def init_db(self) -> None:
        """Initialize database tables."""
        logger.info("Creating/verifying database tables...")
        conn = self._create_connection()  # Use fresh connection for init
        try:
            cursor = conn.cursor()

            # Users table with bp_balance and event_active columns
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    vip_status INTEGER DEFAULT 0,
                    bp_balance INTEGER DEFAULT 0,
                    event_active INTEGER DEFAULT 0
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

            # Try to add event_active column to existing users table
            try:
                cursor.execute(
                    "ALTER TABLE users ADD COLUMN event_active INTEGER DEFAULT 0"
                )
                logger.info("Added event_active column to users table")
            except sqlite3.OperationalError:
                # Column already exists
                logger.debug("event_active column already exists")

            # Activities table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS activities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    activity_id TEXT,
                    completed INTEGER DEFAULT 0,
                    date TEXT,
                    completed_at TEXT,
                    bp_earned INTEGER DEFAULT NULL,
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

            # Add bp_earned column to existing tables
            try:
                cursor.execute(
                    "ALTER TABLE activities ADD COLUMN bp_earned INTEGER DEFAULT NULL"
                )
                logger.info("Added bp_earned column to activities table")
            except sqlite3.OperationalError:
                # Column already exists
                logger.debug("bp_earned column already exists")

            # Hidden activities table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS hidden_activities (
                    user_id TEXT,
                    activity_id TEXT,
                    hidden_at TEXT,
                    PRIMARY KEY (user_id, activity_id)
                )
            """)
            logger.debug("Hidden activities table created/verified")

            # Settings table for persistent config
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)
            logger.debug("Settings table created/verified")

            # ============================================================
            # OPTIMIZED INDEXES
            # ============================================================

            # Primary lookup index - covers most queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_activities_lookup
                ON activities(user_id, date, activity_id)
            """)

            # Specialized index for finding completed activities
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_activities_completed
                ON activities(user_id, date) WHERE completed = 1
            """)

            # Index for date-based queries (cleanup)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_activities_date
                ON activities(date)
            """)

            # Covering index for status checks
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_activities_status
                ON activities(user_id, activity_id, date, completed)
            """)

            # Index for hidden activities lookup
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_hidden_activities_user
                ON hidden_activities(user_id)
            """)

            logger.debug("Activity indexes created/verified")

            conn.commit()
        finally:
            conn.close()
        logger.info("Database tables ready")

    # =========================================================================
    # User VIP methods
    # =========================================================================

    def get_user_vip_status(self, user_id: int) -> bool:
        """Get user's VIP status."""
        with self.get_cursor(commit=False) as cursor:
            cursor.execute(
                "SELECT vip_status FROM users WHERE user_id = ?", (str(user_id),)
            )
            result = cursor.fetchone()
            vip = bool(result[0]) if result else False
            logger.debug(f"User {user_id} VIP status: {vip}")
            return vip

    def set_user_vip_status(self, user_id: int, vip_status: bool) -> None:
        """Set user's VIP status."""
        logger.info(f"Setting VIP status for user {user_id}: {vip_status}")
        with self.get_cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO users (user_id, vip_status) VALUES (?, ?)
                ON CONFLICT(user_id) DO UPDATE SET vip_status = ?
            """,
                (str(user_id), int(vip_status), int(vip_status)),
            )

    # =========================================================================
    # User Event methods
    # =========================================================================

    def get_user_event_status(self, user_id: int) -> bool:
        """Get user's x2 event status."""
        with self.get_cursor(commit=False) as cursor:
            cursor.execute(
                "SELECT event_active FROM users WHERE user_id = ?", (str(user_id),)
            )
            result = cursor.fetchone()
            event_active = bool(result[0]) if result else False
            logger.debug(f"User {user_id} event status: {event_active}")
            return event_active

    def set_user_event_status(self, user_id: int, event_active: bool) -> None:
        """Set user's x2 event status."""
        logger.info(f"Setting event status for user {user_id}: {event_active}")
        with self.get_cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO users (user_id, event_active) VALUES (?, ?)
                ON CONFLICT(user_id) DO UPDATE SET event_active = ?
            """,
                (str(user_id), int(event_active), int(event_active)),
            )

    # =========================================================================
    # BP Balance methods
    # =========================================================================

    def get_user_bp_balance(self, user_id: int) -> int:
        """Get user's current BP balance."""
        with self.get_cursor(commit=False) as cursor:
            cursor.execute(
                "SELECT bp_balance FROM users WHERE user_id = ?", (str(user_id),)
            )
            result = cursor.fetchone()
            balance = result[0] if result else 0
            logger.debug(f"User {user_id} balance: {balance} BP")
            return balance

    def set_user_bp_balance(self, user_id: int, balance: int) -> None:
        """Set user's BP balance."""
        logger.info(f"Setting balance for user {user_id}: {balance} BP")
        with self.get_cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO users (user_id, bp_balance) VALUES (?, ?)
                ON CONFLICT(user_id) DO UPDATE SET bp_balance = ?
            """,
                (str(user_id), int(balance), int(balance)),
            )

    def add_user_bp(self, user_id: int, amount: int) -> int:
        """Add BP to user's balance.

        Note: This is not atomic - for high-concurrency scenarios,
        consider using a single UPDATE with arithmetic.
        """
        current_balance = self.get_user_bp_balance(user_id)
        new_balance = current_balance + amount
        self.set_user_bp_balance(user_id, new_balance)
        logger.info(
            f"User {user_id} earned {amount} BP (Balance: {current_balance} -> {new_balance})"
        )
        return new_balance

    def subtract_user_bp(self, user_id: int, amount: int) -> int:
        """Subtract BP from user's balance.

        Note: This is not atomic - for high-concurrency scenarios,
        consider using a single UPDATE with arithmetic.
        """
        current_balance = self.get_user_bp_balance(user_id)
        new_balance = current_balance - amount
        self.set_user_bp_balance(user_id, new_balance)
        logger.info(
            f"User {user_id} lost {amount} BP (Balance: {current_balance} -> {new_balance})"
        )
        return new_balance

    # =========================================================================
    # Activity methods
    # =========================================================================

    def get_activity_status(self, user_id: int, activity_id: str, date: str) -> bool:
        """Check if an activity is completed."""
        with self.get_cursor(commit=False) as cursor:
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
        self,
        user_id: int,
        activity_id: str,
        date: str,
        completed: bool,
        bp_earned: Optional[int] = None,
    ) -> None:
        """Set activity completion status with BP earned.

        Args:
            user_id: User's Discord ID
            activity_id: Activity identifier
            date: Activity date (YYYY-MM-DD)
            completed: Whether activity is completed
            bp_earned: BP amount earned (stored when completing, used when uncompleting)
        """
        logger.info(
            f"User {user_id} {'completed' if completed else 'uncompleted'} activity {activity_id} on {date}"
            + (f" (bp_earned={bp_earned})" if bp_earned is not None else "")
        )
        with self.get_cursor() as cursor:
            # Set completed_at to current UTC time when completing, NULL when uncompleting
            completed_at = datetime.now(timezone.utc).isoformat() if completed else None

            # When completing, store bp_earned; when uncompleting, clear it
            stored_bp = bp_earned if completed else None

            cursor.execute(
                """
                INSERT INTO activities (user_id, activity_id, date, completed, completed_at, bp_earned)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id, activity_id, date)
                DO UPDATE SET completed = ?, completed_at = ?, bp_earned = ?
            """,
                (
                    str(user_id),
                    activity_id,
                    date,
                    int(completed),
                    completed_at,
                    stored_bp,
                    int(completed),
                    completed_at,
                    stored_bp,
                ),
            )

    def get_activity_bp_earned(
        self, user_id: int, activity_id: str, date: str
    ) -> Optional[int]:
        """Get the BP earned for a specific completed activity.

        Returns the stored bp_earned value, or None if not found/not completed.
        This is used when uncompleting an activity to subtract the correct amount.
        """
        with self.get_cursor(commit=False) as cursor:
            cursor.execute(
                """
                SELECT bp_earned FROM activities
                WHERE user_id = ? AND activity_id = ? AND date = ? AND completed = 1
            """,
                (str(user_id), activity_id, date),
            )
            result = cursor.fetchone()
            bp_earned = result[0] if result and result[0] is not None else None
            logger.debug(
                f"Activity {activity_id} bp_earned for user {user_id} on {date}: {bp_earned}"
            )
            return bp_earned

    def get_user_completed_activities(self, user_id: int, date: str) -> List[str]:
        """Get list of completed activities for a user on a specific date.

        Results are sorted by completion time (most recent first).
        """
        with self.get_cursor(commit=False) as cursor:
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

    def get_user_completed_activities_with_bp(
        self, user_id: int, date: str
    ) -> List[Tuple[str, Optional[int]]]:
        """Get list of completed activities with their bp_earned values.

        Returns list of tuples: (activity_id, bp_earned)
        Results are sorted by completion time (most recent first).
        """
        with self.get_cursor(commit=False) as cursor:
            cursor.execute(
                """
                SELECT activity_id, bp_earned FROM activities
                WHERE user_id = ? AND date = ? AND completed = 1
                ORDER BY completed_at DESC NULLS LAST
            """,
                (str(user_id), date),
            )
            results = cursor.fetchall()
            logger.debug(
                f"User {user_id} completed {len(results)} activities with BP on {date}"
            )
            return [(row[0], row[1]) for row in results]

    # =========================================================================
    # Hidden Activities methods
    # =========================================================================

    def get_hidden_activities(self, user_id: int) -> List[str]:
        """Get list of hidden activity IDs for a user."""
        with self.get_cursor(commit=False) as cursor:
            cursor.execute(
                "SELECT activity_id FROM hidden_activities WHERE user_id = ?",
                (str(user_id),),
            )
            results = cursor.fetchall()
            activity_ids = [row[0] for row in results]
            logger.debug(f"User {user_id} has {len(activity_ids)} hidden activities")
            return activity_ids

    def hide_activity(self, user_id: int, activity_id: str) -> bool:
        """Hide an activity for a user.

        Returns True if the activity was hidden, False if already hidden.
        """
        logger.info(f"User {user_id} hiding activity {activity_id}")
        with self.get_cursor() as cursor:
            try:
                cursor.execute(
                    """
                    INSERT INTO hidden_activities (user_id, activity_id, hidden_at)
                    VALUES (?, ?, ?)
                """,
                    (str(user_id), activity_id, datetime.now(timezone.utc).isoformat()),
                )
                return True
            except sqlite3.IntegrityError:
                # Already hidden
                logger.debug(
                    f"Activity {activity_id} already hidden for user {user_id}"
                )
                return False

    def unhide_activity(self, user_id: int, activity_id: str) -> bool:
        """Unhide an activity for a user.

        Returns True if the activity was unhidden, False if wasn't hidden.
        """
        logger.info(f"User {user_id} unhiding activity {activity_id}")
        with self.get_cursor() as cursor:
            cursor.execute(
                "DELETE FROM hidden_activities WHERE user_id = ? AND activity_id = ?",
                (str(user_id), activity_id),
            )
            deleted = cursor.rowcount > 0
            if not deleted:
                logger.debug(
                    f"Activity {activity_id} was not hidden for user {user_id}"
                )
            return deleted

    def is_activity_hidden(self, user_id: int, activity_id: str) -> bool:
        """Check if an activity is hidden for a user."""
        with self.get_cursor(commit=False) as cursor:
            cursor.execute(
                """
                SELECT 1 FROM hidden_activities
                WHERE user_id = ? AND activity_id = ?
            """,
                (str(user_id), activity_id),
            )
            return cursor.fetchone() is not None

    # =========================================================================
    # Settings methods
    # =========================================================================

    def get_setting(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get a setting value from database."""
        with self.get_cursor(commit=False) as cursor:
            cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
            result = cursor.fetchone()
            value = result[0] if result else default
            logger.debug(f"Get setting {key}: {value}")
            return value

    def set_setting(self, key: str, value: str) -> None:
        """Set a setting value in database."""
        logger.info(f"Setting {key} = {value}")
        with self.get_cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO settings (key, value) VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value = ?
            """,
                (key, str(value), str(value)),
            )

    def optimize_database(self) -> None:
        """Run VACUUM and ANALYZE to optimize database performance.

        Note: VACUUM requires exclusive access, so this creates a
        fresh connection rather than using the thread-local one.
        """
        logger.info("Running database optimization...")
        conn = self._create_connection()
        try:
            conn.execute("VACUUM")
            conn.execute("ANALYZE")
        finally:
            conn.close()
        logger.info("Database optimization complete")


def get_today_date() -> str:
    """
    Get today's activity date in UTC (07:00 MSK = 04:00 UTC).

    Returns the "activity day" which continues until 04:00 UTC:
    - From 00:00 to 03:59 UTC -> Returns YESTERDAY's date (activities still valid)
    - From 04:00 to 23:59 UTC -> Returns TODAY's date (new activity day)

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
