import discord

import config
from activities import ACTIVITIES
from database import get_today_date


def get_bp_multiplier(db):
    """Get current BP multiplier based on event status"""
    # Check database first (persistent), then fall back to config
    event_active = db.get_setting("double_bp_event", str(config.DOUBLE_BP_EVENT))
    return 2 if event_active == "True" else 1


def is_event_active(db):
    """Check if double BP event is currently active"""
    event_active = db.get_setting("double_bp_event", str(config.DOUBLE_BP_EVENT))
    return event_active == "True"


def calculate_bp(activity, vip_status, db):
    """Calculate BP for an activity considering VIP and event multiplier"""
    base_bp = activity["bp_vip"] if vip_status else activity["bp"]
    multiplier = get_bp_multiplier(db)
    return base_bp * multiplier


def create_activities_embed(db, user_id):
    """Create embed showing all activities"""
    vip_status = db.get_user_vip_status(user_id)
    balance = db.get_user_bp_balance(user_id)
    today = get_today_date()
    completed_activities = db.get_user_completed_activities(user_id, today)

    event_status = "🎉 **СОБЫТИЕ: x2 BP!**" if is_event_active(db) else ""

    embed = discord.Embed(
        title="📊 Статус Бонусных Активностей",
        description=f"**Баланс: {balance} BP**\n"
        f"VIP Статус: {'✅ Активен' if vip_status else '❌ Неактивен'}\n{event_status}",
        color=discord.Color.gold() if is_event_active(db) else discord.Color.blue(),
    )

    for category, activities in ACTIVITIES.items():
        # Split activities into chunks to avoid 1024 character limit
        MAX_FIELD_LENGTH = 1000  # Leave some margin

        category_text = ""
        field_number = 1

        for i, activity in enumerate(activities):
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
