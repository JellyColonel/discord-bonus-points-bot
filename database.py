import sqlite3
from datetime import datetime

import pytz


class Database:
    def __init__(self, db_name="bonus_points.db"):
        self.db_name = db_name
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_name)

    def init_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()

        # Users table - add bp_balance column
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                vip_status INTEGER DEFAULT 0,
                bp_balance INTEGER DEFAULT 0
            )
        """)

        # Add bp_balance column to existing users table if it doesn't exist
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN bp_balance INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            # Column already exists
            pass

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

        # Settings table for persistent config
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)

        conn.commit()
        conn.close()

    def get_user_vip_status(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT vip_status FROM users WHERE user_id = ?", (str(user_id),)
        )
        result = cursor.fetchone()
        conn.close()
        return bool(result[0]) if result else False

    def set_user_vip_status(self, user_id, vip_status):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO users (user_id, vip_status) VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET vip_status = ?
        """,
            (str(user_id), int(vip_status), int(vip_status)),
        )
        conn.commit()
        conn.close()

    def get_user_bp_balance(self, user_id):
        """Get user's current BP balance"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT bp_balance FROM users WHERE user_id = ?", (str(user_id),)
        )
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else 0

    def set_user_bp_balance(self, user_id, balance):
        """Set user's BP balance"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO users (user_id, bp_balance) VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET bp_balance = ?
        """,
            (str(user_id), int(balance), int(balance)),
        )
        conn.commit()
        conn.close()

    def add_user_bp(self, user_id, amount):
        """Add BP to user's balance"""
        current_balance = self.get_user_bp_balance(user_id)
        new_balance = current_balance + amount
        self.set_user_bp_balance(user_id, new_balance)
        return new_balance

    def subtract_user_bp(self, user_id, amount):
        """Subtract BP from user's balance"""
        current_balance = self.get_user_bp_balance(user_id)
        new_balance = current_balance - amount
        self.set_user_bp_balance(user_id, new_balance)
        return new_balance

    def get_activity_status(self, user_id, activity_id, date):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT completed FROM activities 
            WHERE user_id = ? AND activity_id = ? AND date = ?
        """,
            (str(user_id), activity_id, date),
        )
        result = cursor.fetchone()
        conn.close()
        return bool(result[0]) if result else False

    def set_activity_status(self, user_id, activity_id, date, completed):
        conn = self.get_connection()
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
        conn.close()

    def get_user_completed_activities(self, user_id, date):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT activity_id FROM activities 
            WHERE user_id = ? AND date = ? AND completed = 1
        """,
            (str(user_id), date),
        )
        results = cursor.fetchall()
        conn.close()
        return [row[0] for row in results]

    def get_setting(self, key, default=None):
        """Get a setting value from database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else default

    def set_setting(self, key, value):
        """Set a setting value in database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO settings (key, value) VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = ?
        """,
            (key, str(value), str(value)),
        )
        conn.commit()
        conn.close()


def get_today_date():
    """Get today's date in Moscow timezone"""
    moscow_tz = pytz.timezone("Europe/Moscow")
    return datetime.now(moscow_tz).strftime("%Y-%m-%d")
