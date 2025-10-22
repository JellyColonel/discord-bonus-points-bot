"""Embed creation utilities."""

import discord

from bot.core.database import get_today_date
from bot.data import ACTIVITIES

from .helpers import calculate_bp, is_event_active


def create_activities_embed(db, user_id):
    """Create embed showing all activities."""
    vip_status = db.get_user_vip_status(user_id)
    balance = db.get_user_bp_balance(user_id)
    today = get_today_date()
    completed_activities = db.get_user_completed_activities(user_id, today)

    event_status = "🎉 **СОБЫТИЕ: x2 BP!**" if is_event_active(db) else ""

    embed = discord.Embed(
        title="📊 Статус Бонусных Активностей",
        description=(
            f"**Баланс: {balance} BP**\n"
            f"VIP Статус: {'✅ Активен' if vip_status else '❌ Неактивен'}\n"
            f"{event_status}"
        ),
        color=discord.Color.gold() if is_event_active(db) else discord.Color.blue(),
    )

    for category, activities in ACTIVITIES.items():
        # Split activities into chunks to avoid 1024 character limit
        MAX_FIELD_LENGTH = 1000  # Leave some margin

        category_text = ""
        field_number = 1

        for activity in activities:
            completed = activity["id"] in completed_activities
            status = "✅" if completed else "❌"
            points = calculate_bp(activity, vip_status, db)
            activity_line = f"{status} {activity['name']} - **{points} BP**\n"

            # Check if adding this activity would exceed the limit
            if len(category_text) + len(activity_line) > MAX_FIELD_LENGTH:
                # Add current field and start a new one
                field_name = (
                    f"{category} ({field_number})" if field_number > 1 else category
                )
                embed.add_field(name=field_name, value=category_text, inline=False)
                category_text = activity_line
                field_number += 1
            else:
                category_text += activity_line

        # Add the remaining text
        if category_text:
            field_name = (
                f"{category} ({field_number})" if field_number > 1 else category
            )
            embed.add_field(name=field_name, value=category_text, inline=False)

    return embed
