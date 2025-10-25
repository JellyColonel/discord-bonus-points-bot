# bonus_points_bot/bot/utils/embeds.py
"""Embed creation utilities - Shows only uncompleted activities with balance"""

import discord

from bot.core.database import get_today_date
from bot.data import ACTIVITIES, TOTAL_ACTIVITIES


def create_activities_embed(db, user_id):
    """
    Create embed showing only uncompleted activities.
    Shows current balance and progress counter with BP earned/remaining.
    """
    # Import helper for BP calculation
    from bot.data import get_activity_by_id, get_all_activities

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

    # Build embed - count uncompleted and completed activities
    completed_count = len(completed_activities)
    uncompleted_count = TOTAL_ACTIVITIES - completed_count

    # Pre-calculate BP multiplier ONCE (instead of 41 DB queries!)
    bp_multiplier = 2 if event_active else 1

    # Calculate earned BP today
    earned_today = 0
    for activity_id in completed_activities:
        activity = get_activity_by_id(activity_id)
        if activity:
            base_bp = activity["bp_vip"] if vip_status else activity["bp"]
            earned_today += base_bp * bp_multiplier

    # Calculate remaining BP (from uncompleted activities)
    remaining_bp = 0
    for activity in get_all_activities():
        if activity["id"] not in completed_activities:
            base_bp = activity["bp_vip"] if vip_status else activity["bp"]
            remaining_bp += base_bp * bp_multiplier

    # Build description with clean sectioned layout
    event_status = "\n🎉 **×2 BP Событие активно!**" if event_active else ""

    embed = discord.Embed(
        title="📋 Оставшиеся Активности",
        description=(
            f"💰 **Баланс:** {balance} BP\n\n"
            f"📊 **Прогресс**\n"
            f"• Выполнено {completed_count} / {TOTAL_ACTIVITIES} (осталось {uncompleted_count})\n"
            f"• Заработано {earned_today} BP  |  Осталось {remaining_bp} BP\n\n"
            f"⭐ **VIP:** {'✅ Активен' if vip_status else '❌ Неактивен'}{event_status}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━"
        ),
        color=discord.Color.gold() if event_active else discord.Color.blue(),
    )

    # Count activities added
    total_added = 0
    categories_list = list(ACTIVITIES.items())

    for category_index, (category, activities) in enumerate(categories_list):
        is_last_category = category_index == len(categories_list) - 1

        # Build category text - ONLY UNCOMPLETED activities
        MAX_FIELD_LENGTH = 1000
        category_text = ""
        field_number = 1

        for activity in activities:
            completed = activity["id"] in completed_activities  # O(1) lookup

            # Skip completed activities - they disappear from the list!
            if completed:
                continue

            # Calculate BP
            base_bp = activity["bp_vip"] if vip_status else activity["bp"]
            points = base_bp * bp_multiplier

            # No status emoji - just show the uncompleted activity
            activity_line = f"{activity['name']} - **{points} BP**\n"

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

            total_added += 1

        # Add remaining text for this category (only if there are uncompleted activities)
        if category_text:
            field_name = (
                f"{category} ({field_number})" if field_number > 1 else category
            )
            embed.add_field(name=field_name, value=category_text, inline=False)

            # Add empty field as visual separator between categories (except after last category)
            if not is_last_category:
                embed.add_field(
                    name="\u200b",  # Zero-width space (invisible field name)
                    value="",
                    inline=False,
                )

    # If all activities completed, show celebration message
    if total_added == 0:
        embed.add_field(
            name="🎉 Все активности выполнены!",
            value="Отличная работа! Возвращайтесь завтра за новыми активностями.",
            inline=False,
        )

    return embed
