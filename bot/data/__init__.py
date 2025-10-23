# bonus_points_bot/bot/data/__init__.py
"""Data definitions for the bot."""

from .activities import ACTIVITIES, get_activity_by_id, get_all_activities

__all__ = ['ACTIVITIES', 'get_all_activities', 'get_activity_by_id']