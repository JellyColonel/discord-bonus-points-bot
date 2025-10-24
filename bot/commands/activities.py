# bonus_points_bot/bot/commands/activities.py
"""Activity-related commands - OPTIMIZED VERSION with UX improvements"""

import asyncio
import logging
from datetime import datetime, timedelta

import discord
from discord import app_commands

from bot.core.database import get_today_date
from bot.data import get_activity_by_id, get_all_activities
from bot.utils.embeds import create_activities_embed
from bot.utils.helpers import calculate_bp, is_event_active

logger = logging.getLogger(__name__)

# ============================================================================
# OPTIMIZATION: Autocomplete caching to reduce DB calls
# ============================================================================

_autocomplete_cache = {}
_CACHE_TIMEOUT = timedelta(seconds=10)
_MAX_CACHE_SIZE = 200

# ============================================================================
# UX IMPROVEMENT: Track activities messages for dynamic updates
# ============================================================================

_activities_messages = {}  # user_id -> (message, timestamp)
_MESSAGE_CACHE_TIMEOUT = timedelta(minutes=10)  # Keep messages for 10 minutes


def _get_cached_completed_activities(user_id, today):
    """Get cached completed activities if available and fresh."""
    cache_key = (user_id, today)
    now = datetime.now()

    if cache_key in _autocomplete_cache:
        cached_data, cache_time = _autocomplete_cache[cache_key]
        if now - cache_time < _CACHE_TIMEOUT:
            return cached_data

    return None


def _set_autocomplete_cache(user_id, today, data):
    """Store completed activities in cache."""
    cache_key = (user_id, today)
    _autocomplete_cache[cache_key] = (data, datetime.now())

    # Keep cache size manageable
    if len(_autocomplete_cache) > _MAX_CACHE_SIZE:
        _autocomplete_cache.clear()


def _store_activities_message(user_id, message):
    """Store activities message reference for dynamic updates."""
    _activities_messages[user_id] = (message, datetime.now())

    # Cleanup old messages
    if len(_activities_messages) > 100:
        now = datetime.now()
        expired = [
            uid
            for uid, (_, timestamp) in _activities_messages.items()
            if now - timestamp > _MESSAGE_CACHE_TIMEOUT
        ]
        for uid in expired:
            del _activities_messages[uid]


async def _update_activities_message(db, user_id):
    """Update stored activities message if it exists."""
    if user_id not in _activities_messages:
        return

    message, timestamp = _activities_messages[user_id]

    # Check if message is too old
    if datetime.now() - timestamp > _MESSAGE_CACHE_TIMEOUT:
        del _activities_messages[user_id]
        return

    try:
        embed = create_activities_embed(db, user_id)
        await message.edit(embed=embed)
        logger.debug(f"Updated activities dashboard for user {user_id}")
    except discord.NotFound:
        # Message was deleted
        del _activities_messages[user_id]
        logger.debug(f"Activities message for user {user_id} was deleted")
    except discord.HTTPException as e:
        # Other Discord API errors - log but don't crash
        logger.debug(f"Failed to update activities message for user {user_id}: {e}")
    except Exception as e:
        logger.error(
            f"Unexpected error updating activities message: {e}", exc_info=True
        )


async def _delete_message_after_delay(message, delay=10):
    """Delete a message after specified delay in seconds."""
    try:
        await asyncio.sleep(delay)
        await message.delete()
    except discord.NotFound:
        # Message already deleted
        pass
    except discord.HTTPException as e:
        logger.debug(f"Failed to delete message: {e}")
    except Exception as e:
        logger.error(f"Unexpected error deleting message: {e}", exc_info=True)


def setup_activity_commands(tree, db, config):
    """Setup activity-related commands."""

    @tree.command(
        name="activities", description="Показать список всех активностей и их статус"
    )
    async def activities_command(interaction: discord.Interaction):
        try:
            # Delete old dashboard if it exists
            if interaction.user.id in _activities_messages:
                old_message, _ = _activities_messages[interaction.user.id]
                try:
                    await old_message.delete()
                    logger.info(f"Deleted old dashboard for user {interaction.user.id}")
                except discord.NotFound:
                    # Old message already deleted
                    logger.debug(
                        f"Old dashboard for user {interaction.user.id} was already deleted"
                    )
                except discord.HTTPException as e:
                    # Permission error or other issue - log but continue
                    logger.debug(
                        f"Could not delete old dashboard for user {interaction.user.id}: {e}"
                    )

            embed = create_activities_embed(db, interaction.user.id)
            # Send as non-ephemeral to create a persistent dashboard
            await interaction.response.send_message(embed=embed, ephemeral=False)

            # Store message reference for dynamic updates
            message = await interaction.original_response()
            _store_activities_message(interaction.user.id, message)

            logger.info(f"User {interaction.user.id} created new activities dashboard")
        except Exception as e:
            logger.error(
                f"Error in activities command for user {interaction.user.id}: {e}",
                exc_info=True,
            )
            await interaction.response.send_message(
                "❌ Произошла ошибка при загрузке активностей. Попробуйте позже.",
                ephemeral=True,
            )

    @tree.command(name="complete", description="Отметить активность как выполненную")
    @app_commands.describe(activity="Выберите активность")
    async def complete_command(interaction: discord.Interaction, activity: str):
        try:
            activity_data = get_activity_by_id(activity)  # O(1) lookup!
            if not activity_data:
                await interaction.response.send_message(
                    "❌ Активность не найдена!", ephemeral=True
                )
                return

            today = get_today_date()

            # Check if already completed
            if db.get_activity_status(interaction.user.id, activity, today):
                await interaction.response.send_message(
                    f'⚠️ Активность "{activity_data["name"]}" уже выполнена сегодня!',
                    ephemeral=True,
                )
                return

            # Mark as completed
            db.set_activity_status(interaction.user.id, activity, today, True)

            # Calculate and add BP
            vip_status = db.get_user_vip_status(interaction.user.id)
            points = calculate_bp(activity_data, vip_status, db)
            new_balance = db.add_user_bp(interaction.user.id, points)

            event_note = " 🎉" if is_event_active(db) else ""

            # Send non-ephemeral message that will be deleted after 10 seconds
            await interaction.response.send_message(
                f'✅ Активность "{activity_data["name"]}" отмечена как выполненная!\n'
                f"**+{points} BP{event_note}**\n"
                f"Текущий баланс: **{new_balance} BP**",
                ephemeral=False,
            )

            # Get the message and schedule deletion
            response_message = await interaction.original_response()
            asyncio.create_task(_delete_message_after_delay(response_message, 10))

            logger.info(
                f"User {interaction.user.id} completed activity {activity}, earned {points} BP"
            )

            # Invalidate cache for this user
            cache_key = (interaction.user.id, today)
            if cache_key in _autocomplete_cache:
                del _autocomplete_cache[cache_key]

            # Update the activities dashboard if it exists
            await _update_activities_message(db, interaction.user.id)

        except Exception as e:
            logger.error(
                f"Error in complete command for user {interaction.user.id}, activity {activity}: {e}",
                exc_info=True,
            )
            await interaction.response.send_message(
                "❌ Произошла ошибка при отметке активности. Попробуйте позже.",
                ephemeral=True,
            )

    @complete_command.autocomplete("activity")
    async def complete_autocomplete(interaction: discord.Interaction, current: str):
        """Show only UNCOMPLETED activities - OPTIMIZED with caching"""
        try:
            today = get_today_date()

            # Try cache first
            cached = _get_cached_completed_activities(interaction.user.id, today)
            if cached is not None:
                completed_activities = cached
            else:
                # Cache miss - fetch and cache
                completed_activities = db.get_user_completed_activities(
                    interaction.user.id, today
                )
                _set_autocomplete_cache(
                    interaction.user.id, today, completed_activities
                )

            # Convert to set for O(1) lookups
            completed_set = set(completed_activities)

            # Use optimized search function
            all_activities = get_all_activities()  # Now cached!
            current_lower = current.lower()

            choices = []
            for activity in all_activities:
                # Skip completed (O(1) lookup)
                if activity["id"] in completed_set:
                    continue

                # Early exit when we have enough
                if len(choices) >= 25:
                    break

                # Use pre-lowercased fields
                if (
                    current_lower in activity["_name_lower"]
                    or current_lower in activity["_id_lower"]
                ):
                    choices.append(
                        app_commands.Choice(
                            name=f"{activity['name']} ({activity['bp']}/{activity['bp_vip']} BP)",
                            value=activity["id"],
                        )
                    )

            return choices
        except Exception as e:
            logger.error(
                f"Error in complete autocomplete for user {interaction.user.id}: {e}",
                exc_info=True,
            )
            return []

    @tree.command(
        name="uncomplete", description="Отметить активность как невыполненную"
    )
    @app_commands.describe(activity="Выберите активность")
    async def uncomplete_command(interaction: discord.Interaction, activity: str):
        try:
            activity_data = get_activity_by_id(activity)  # O(1) lookup!
            if not activity_data:
                await interaction.response.send_message(
                    "❌ Активность не найдена!", ephemeral=True
                )
                return

            today = get_today_date()

            # Check if it was completed
            if not db.get_activity_status(interaction.user.id, activity, today):
                await interaction.response.send_message(
                    f'⚠️ Активность "{activity_data["name"]}" не была выполнена!',
                    ephemeral=True,
                )
                return

            # Mark as not completed
            db.set_activity_status(interaction.user.id, activity, today, False)

            # Subtract BP
            vip_status = db.get_user_vip_status(interaction.user.id)
            points = calculate_bp(activity_data, vip_status, db)
            new_balance = db.subtract_user_bp(interaction.user.id, points)

            # Send non-ephemeral message that will be deleted after 10 seconds
            await interaction.response.send_message(
                f'❌ Активность "{activity_data["name"]}" отмечена как невыполненная.\n'
                f"**-{points} BP**\n"
                f"Текущий баланс: **{new_balance} BP**",
                ephemeral=False,
            )

            # Get the message and schedule deletion
            response_message = await interaction.original_response()
            asyncio.create_task(_delete_message_after_delay(response_message, 10))

            logger.info(
                f"User {interaction.user.id} uncompleted activity {activity}, lost {points} BP"
            )

            # Invalidate cache
            cache_key = (interaction.user.id, today)
            if cache_key in _autocomplete_cache:
                del _autocomplete_cache[cache_key]

            # Update the activities dashboard if it exists
            await _update_activities_message(db, interaction.user.id)

        except Exception as e:
            logger.error(
                f"Error in uncomplete command for user {interaction.user.id}, activity {activity}: {e}",
                exc_info=True,
            )
            await interaction.response.send_message(
                "❌ Произошла ошибка при отмене активности. Попробуйте позже.",
                ephemeral=True,
            )

    @uncomplete_command.autocomplete("activity")
    async def uncomplete_autocomplete(interaction: discord.Interaction, current: str):
        """Show only COMPLETED activities - OPTIMIZED with caching"""
        try:
            today = get_today_date()

            # Try cache first
            cached = _get_cached_completed_activities(interaction.user.id, today)
            if cached is not None:
                completed_activities = cached
            else:
                completed_activities = db.get_user_completed_activities(
                    interaction.user.id, today
                )
                _set_autocomplete_cache(
                    interaction.user.id, today, completed_activities
                )

            completed_set = set(completed_activities)

            all_activities = get_all_activities()  # Cached
            current_lower = current.lower()

            choices = []
            for activity in all_activities:
                # Only show completed
                if activity["id"] not in completed_set:
                    continue

                if len(choices) >= 25:
                    break

                # Use pre-lowercased fields
                if (
                    current_lower in activity["_name_lower"]
                    or current_lower in activity["_id_lower"]
                ):
                    choices.append(
                        app_commands.Choice(
                            name=f"{activity['name']} ({activity['bp']}/{activity['bp_vip']} BP)",
                            value=activity["id"],
                        )
                    )

            return choices
        except Exception as e:
            logger.error(
                f"Error in uncomplete autocomplete for user {interaction.user.id}: {e}",
                exc_info=True,
            )
            return []
