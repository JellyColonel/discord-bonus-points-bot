# bonus_points_bot/bot/commands/activities.py
"""Activities command module with persistent dashboard support."""

import asyncio
import logging
from datetime import datetime, timedelta

import discord
from discord import app_commands

from bot.core.database import Database, get_today_date
from bot.data.activities import get_activity_by_id, search_activities
from bot.utils.embeds import create_activities_embed
from bot.utils.helpers import calculate_bp

logger = logging.getLogger(__name__)

# ============================================================================
# OPTIMIZATION: Autocomplete caching to reduce DB calls
# ============================================================================

_autocomplete_cache = {}
_CACHE_TIMEOUT = timedelta(seconds=10)
_MAX_CACHE_SIZE = 200

# ============================================================================
# UX IMPROVEMENT: Track activities messages for dynamic updates
# WITH PERSISTENCE: Now also saved to database
# ============================================================================

_activities_messages = {}  # user_id -> {"message": message, "channel": channel, "timestamp": datetime}
_MESSAGE_CACHE_TIMEOUT = timedelta(minutes=10)  # Keep messages for 10 minutes


def _clean_cache():
    """Remove expired entries from autocomplete cache."""
    current_time = datetime.now()
    expired_keys = [
        key
        for key, (_, timestamp) in _autocomplete_cache.items()
        if current_time - timestamp > _CACHE_TIMEOUT
    ]
    for key in expired_keys:
        del _autocomplete_cache[key]

    # Limit cache size
    if len(_autocomplete_cache) > _MAX_CACHE_SIZE:
        # Remove oldest entries
        sorted_items = sorted(_autocomplete_cache.items(), key=lambda x: x[1][1])
        for key, _ in sorted_items[: len(_autocomplete_cache) - _MAX_CACHE_SIZE]:
            del _autocomplete_cache[key]


def _clean_message_cache():
    """Remove expired message references from memory cache."""
    current_time = datetime.now()
    expired_users = [
        user_id
        for user_id, data in _activities_messages.items()
        if current_time - data["timestamp"] > _MESSAGE_CACHE_TIMEOUT
    ]
    for user_id in expired_users:
        del _activities_messages[user_id]
        logger.debug(f"Cleaned up expired message cache for user {user_id}")


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


async def _restore_dashboards_from_db(bot: discord.Client, db: Database):
    """Restore dashboard messages from database on bot startup."""
    logger.info("🔄 Restoring dashboards from database...")

    try:
        dashboards = db.get_all_dashboard_messages()

        if not dashboards:
            logger.info("No dashboards to restore")
            return

        logger.info(f"Found {len(dashboards)} dashboard(s) to restore")
        restored_count = 0
        deleted_count = 0

        for user_id, channel_id, message_id in dashboards:
            try:
                channel = bot.get_channel(channel_id)
                if channel is None:
                    try:
                        channel = await bot.fetch_channel(channel_id)
                    except (discord.NotFound, discord.Forbidden):
                        logger.warning(
                            f"Channel {channel_id} not found for user {user_id}'s dashboard, removing from DB"
                        )
                        db.delete_dashboard_message(user_id)
                        deleted_count += 1
                        continue

                try:
                    message = await channel.fetch_message(message_id)

                    # Successfully restored - add to in-memory cache
                    _activities_messages[user_id] = {
                        "message": message,
                        "channel": channel,
                        "timestamp": datetime.now(),
                    }
                    restored_count += 1
                    logger.debug(
                        f"✅ Restored dashboard for user {user_id} (msg: {message_id})"
                    )

                except discord.NotFound:
                    logger.warning(
                        f"Dashboard message {message_id} not found for user {user_id}, removing from DB"
                    )
                    db.delete_dashboard_message(user_id)
                    deleted_count += 1

                except discord.Forbidden:
                    logger.warning(
                        f"No permission to access dashboard message {message_id} for user {user_id}"
                    )
                    db.delete_dashboard_message(user_id)
                    deleted_count += 1

            except Exception as e:
                logger.error(
                    f"Error restoring dashboard for user {user_id}: {e}", exc_info=True
                )

        logger.info(
            f"✅ Dashboard restoration complete: {restored_count} restored, {deleted_count} cleaned up"
        )

    except Exception as e:
        logger.error(f"Failed to restore dashboards: {e}", exc_info=True)


async def _update_activities_message(db: Database, user_id: int):
    """Update an existing activities dashboard message."""
    if user_id not in _activities_messages:
        logger.warning(f"No dashboard found for user {user_id}")
        return

    dashboard_data = _activities_messages[user_id]
    message = dashboard_data["message"]

    try:
        embed = create_activities_embed(db, user_id)
        await message.edit(embed=embed)

        # Update timestamp on successful update
        dashboard_data["timestamp"] = datetime.now()
        logger.debug(f"Updated dashboard for user {user_id}")

    except discord.NotFound:
        logger.warning(f"Dashboard message for user {user_id} was deleted")
        del _activities_messages[user_id]
        db.delete_dashboard_message(user_id)

    except discord.Forbidden:
        logger.warning(f"No permission to update dashboard for user {user_id}")
        del _activities_messages[user_id]
        db.delete_dashboard_message(user_id)

    except Exception as e:
        logger.error(f"Error updating dashboard for user {user_id}: {e}", exc_info=True)


def setup_activity_commands(tree: app_commands.CommandTree, db: Database, config):
    """Setup activities-related commands."""

    @tree.command(name="activities", description="Показать все активности и прогресс")
    async def activities_command(interaction: discord.Interaction):
        """Show activities dashboard (one per user, persistent)."""
        user_id = interaction.user.id

        # Clean up expired message cache entries
        _clean_message_cache()

        await interaction.response.defer(ephemeral=False)

        try:
            # Check if user already has a dashboard in memory
            if user_id in _activities_messages:
                dashboard_data = _activities_messages[user_id]
                existing_message = dashboard_data["message"]

                try:
                    # Verify message still exists
                    await existing_message.channel.fetch_message(existing_message.id)

                    # Message exists, update it
                    embed = create_activities_embed(db, user_id)
                    await existing_message.edit(embed=embed)

                    # Update timestamp
                    dashboard_data["timestamp"] = datetime.now()

                    await interaction.followup.send(
                        f"Обновлена ваша панель активностей: {existing_message.jump_url}",
                        ephemeral=True,
                    )
                    logger.info(
                        f"Updated existing dashboard for user {user_id} (msg: {existing_message.id})"
                    )
                    return

                except discord.NotFound:
                    logger.info(
                        f"Previous dashboard for user {user_id} was deleted, creating new one"
                    )
                    del _activities_messages[user_id]
                    db.delete_dashboard_message(user_id)

            else:
                # Check database for saved dashboard
                saved_dashboard = db.get_dashboard_message(user_id)

                if saved_dashboard:
                    channel_id, message_id = saved_dashboard

                    try:
                        channel = interaction.client.get_channel(channel_id)
                        if channel is None:
                            channel = await interaction.client.fetch_channel(channel_id)

                        message = await channel.fetch_message(message_id)

                        # Message exists! Restore it to memory and update it
                        _activities_messages[user_id] = {
                            "message": message,
                            "channel": channel,
                            "timestamp": datetime.now(),
                        }

                        embed = create_activities_embed(db, user_id)
                        await message.edit(embed=embed)

                        await interaction.followup.send(
                            f"Восстановлена и обновлена ваша панель активностей: {message.jump_url}",
                            ephemeral=True,
                        )
                        logger.info(
                            f"Restored dashboard for user {user_id} from DB (msg: {message_id})"
                        )
                        return

                    except (discord.NotFound, discord.Forbidden):
                        logger.info(
                            f"Saved dashboard for user {user_id} no longer accessible, creating new one"
                        )
                        db.delete_dashboard_message(user_id)

            # No existing dashboard found, create a new one
            embed = create_activities_embed(db, user_id)
            message = await interaction.followup.send(embed=embed, wait=True)

            # Save to memory
            _activities_messages[user_id] = {
                "message": message,
                "channel": interaction.channel,
                "timestamp": datetime.now(),
            }

            # Save to database for persistence
            db.save_dashboard_message(user_id, interaction.channel_id, message.id)

            logger.info(
                f"Created new dashboard for user {user_id} (channel: {interaction.channel_id}, msg: {message.id})"
            )

        except Exception as e:
            logger.error(
                f"Error in activities command for user {user_id}: {e}", exc_info=True
            )
            try:
                await interaction.followup.send(
                    "❌ An error occurred while creating your dashboard.",
                    ephemeral=True,
                )
            except discord.HTTPException:
                # Interaction already responded or expired
                pass

    async def activity_autocomplete(
        interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        """Autocomplete for activity selection - shows only uncompleted activities."""
        user_id = interaction.user.id
        today = get_today_date()

        # Check cache first
        cache_key = (user_id, today, current, False)  # False = uncompleted
        current_time = datetime.now()

        if cache_key in _autocomplete_cache:
            cached_results, timestamp = _autocomplete_cache[cache_key]
            if current_time - timestamp < _CACHE_TIMEOUT:
                return cached_results

        # Clean cache periodically
        _clean_cache()

        # Get user's completed activities
        completed_activities = set(db.get_user_completed_activities(user_id, today))

        # Search and filter out completed activities
        results = search_activities(current, max_results=25)
        uncompleted = [
            activity
            for activity in results
            if activity["id"] not in completed_activities
        ]

        # Create choices
        choices = [
            app_commands.Choice(name=activity["name"][:100], value=activity["id"])
            for activity in uncompleted[:25]
        ]

        # Cache the results
        _autocomplete_cache[cache_key] = (choices, current_time)

        return choices

    @tree.command(name="complete", description="Отметить активность как выполненную")
    @app_commands.describe(activity="Активность для выполнения")
    @app_commands.autocomplete(activity=activity_autocomplete)
    async def complete_command(interaction: discord.Interaction, activity: str):
        """Complete an activity and add BP."""
        user_id = interaction.user.id
        today = get_today_date()

        activity_data = get_activity_by_id(activity)
        if not activity_data:
            await interaction.response.send_message(
                "Активность не найдена!", ephemeral=True
            )
            return

        if db.get_activity_status(user_id, activity, today):
            await interaction.response.send_message(
                f"Активность '{activity_data['name']}' уже выполнена!",
                ephemeral=True,
            )
            return

        # Mark as completed
        db.set_activity_status(user_id, activity, today, True)

        # Calculate and add BP
        vip_status = db.get_user_vip_status(user_id)
        bp = calculate_bp(activity_data, vip_status, db)
        new_balance = db.add_user_bp(user_id, bp)

        await interaction.response.send_message(
            f"Активность **{activity_data['name']}** выполнена!\n"
            f"+{bp} BP\n"
            f"Текущий баланс: {new_balance} BP",
            ephemeral=False,
        )

        # Get the message and schedule deletion
        response_message = await interaction.original_response()
        asyncio.create_task(_delete_message_after_delay(response_message, 10))

        # Update dashboard if it exists
        if user_id in _activities_messages:
            await _update_activities_message(db, user_id)

    async def uncomplete_autocomplete(
        interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        """Autocomplete for uncompleting - shows only completed activities."""
        user_id = interaction.user.id
        today = get_today_date()

        # Check cache first
        cache_key = (user_id, today, current, True)  # True = completed
        current_time = datetime.now()

        if cache_key in _autocomplete_cache:
            cached_results, timestamp = _autocomplete_cache[cache_key]
            if current_time - timestamp < _CACHE_TIMEOUT:
                return cached_results

        # Clean cache periodically
        _clean_cache()

        # Get user's completed activities
        completed_activity_ids = set(db.get_user_completed_activities(user_id, today))

        # Filter to only show completed activities
        results = search_activities(current, max_results=25)
        completed = [
            activity for activity in results if activity["id"] in completed_activity_ids
        ]

        # Create choices
        choices = [
            app_commands.Choice(name=activity["name"][:100], value=activity["id"])
            for activity in completed[:25]
        ]

        # Cache the results
        _autocomplete_cache[cache_key] = (choices, current_time)

        return choices

    @tree.command(name="uncomplete", description="Отменить выполнение активности")
    @app_commands.describe(activity="Активность для отмены")
    @app_commands.autocomplete(activity=uncomplete_autocomplete)
    async def uncomplete_command(interaction: discord.Interaction, activity: str):
        """Uncomplete an activity and remove BP."""
        user_id = interaction.user.id
        today = get_today_date()

        activity_data = get_activity_by_id(activity)
        if not activity_data:
            await interaction.response.send_message(
                "Активность не найдена!", ephemeral=True
            )
            return

        if not db.get_activity_status(user_id, activity, today):
            await interaction.response.send_message(
                f"Активность '{activity_data['name']}' не выполнена!",
                ephemeral=True,
            )
            return

        # Mark as incomplete
        db.set_activity_status(user_id, activity, today, False)

        # Calculate and remove BP
        vip_status = db.get_user_vip_status(user_id)
        bp = calculate_bp(activity_data, vip_status, db)
        new_balance = db.subtract_user_bp(user_id, bp)

        await interaction.response.send_message(
            f"Активность **{activity_data['name']}** отменена.\n"
            f"-{bp} BP\n"
            f"Текущий баланс: {new_balance} BP",
            ephemeral=False,
        )

        # Get the message and schedule deletion
        response_message = await interaction.original_response()
        asyncio.create_task(_delete_message_after_delay(response_message, 10))

        # Update dashboard if it exists
        if user_id in _activities_messages:
            await _update_activities_message(db, user_id)
