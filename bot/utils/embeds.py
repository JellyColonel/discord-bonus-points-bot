# bonus_points_bot/bot/utils/embeds.py
"""Embed creation utilities - OPTIMIZED VERSION"""

import discord

from bot.core.database import get_today_date
from bot.data import ACTIVITIES


def create_activities_embed(db, user_id):
    """
    Create embed showing all activities.
    OPTIMIZED: Batched database queries in single connection.
    """
    # Use single connection for all queries
    conn = db.get_connection()
    cursor = conn.cursor()

    try:
        # Query 1: Get user data (VIP status + balance) in one query
        cursor.execute(
            """
            SELECT vip_status, bp_balance 
            FROM users 
            WHERE user_id = ?
        """,
            (str(user_id),),
        )
        user_data = cursor.fetchone()
        vip_status = bool(user_data[0]) if user_data else False
        balance = user_data[1] if user_data else 0

        # Query 2: Get completed activities
        today = get_today_date()
        cursor.execute(
            """
            SELECT activity_id 
            FROM activities 
            WHERE user_id = ? AND date = ? AND completed = 1
        """,
            (str(user_id), today),
        )
        completed_activities = {
            row[0] for row in cursor.fetchall()
        }  # Use set for O(1) lookups

        # Query 3: Get event status
        cursor.execute(
            """
            SELECT value 
            FROM settings 
            WHERE key = ?
        """,
            ("double_bp_event",),
        )
        result = cursor.fetchone()
        event_active = (result[0] == "True") if result else False

    finally:
        conn.close()

    # Build embed
    event_status = "🎉 **СОБЫТИЕ: x2 BP!**" if event_active else ""

    embed = discord.Embed(
        title="📊 Статус Бонусных Активностей",
        description=(
            f"**Баланс: {balance} BP**\n"
            f"VIP Статус: {'✅ Активен' if vip_status else '❌ Неактивен'}\n"
            f"{event_status}"
        ),
        color=discord.Color.gold() if event_active else discord.Color.blue(),
    )

    # Pre-calculate BP multiplier ONCE instead of 41 times
    bp_multiplier = 2 if event_active else 1

    for category, activities in ACTIVITIES.items():
        # Build category text
        MAX_FIELD_LENGTH = 1000
        category_text = ""
        field_number = 1

        for activity in activities:
            completed = activity["id"] in completed_activities  # O(1) lookup
            status = "✅" if completed else "❌"

            # Calculate BP directly (no helper function calls)
            base_bp = activity["bp_vip"] if vip_status else activity["bp"]
            points = base_bp * bp_multiplier

            activity_line = f"{status} {activity['name']} - **{points} BP**\n"

            # Check if adding this would exceed field limit
            if len(category_text) + len(activity_line) > MAX_FIELD_LENGTH:
                # Add current field and start new one
                field_name = (
                    f"{category} ({field_number})" if field_number > 1 else category
                )
                embed.add_field(name=field_name, value=category_text, inline=False)
                category_text = activity_line
                field_number += 1
            else:
                category_text += activity_line

        # Add remaining text
        if category_text:
            field_name = (
                f"{category} ({field_number})" if field_number > 1 else category
            )
            embed.add_field(name=field_name, value=category_text, inline=False)

    return embed
