# bonus_points_bot/bot/commands/activities.py
"""Activities command module with persistent dashboard support - ONE dashboard per user."""

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

_autocomplete_cache = {}
_CACHE_TIMEOUT = timedelta(seconds=10)
_MAX_CACHE_SIZE = 200

_activities_messages = {}  # user_id -> {"message": message, "channel": channel, "timestamp": datetime}
_MESSAGE_CACHE_TIMEOUT = timedelta(minutes=10)

DISCORD_AUTOCOMPLETE_LIMIT = 25  # Discord's maximum autocomplete choices
AUTOCOMPLETE_SEARCH_BUFFER = 100  # Search this many activities before filtering
DISCORD_CHOICE_NAME_MAX_LENGTH = 100  # Discord's maximum length for choice names


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


async def _delete_old_dashboard(
    bot: discord.Client, user_id: int, channel_id: int, message_id: int
):
    """Delete an old dashboard message."""
    try:
        channel = bot.get_channel(channel_id)
        if channel is None:
            channel = await bot.fetch_channel(channel_id)

        message = await channel.fetch_message(message_id)
        await message.delete()
        logger.info(f"Deleted old dashboard for user {user_id} (msg: {message_id})")
    except discord.NotFound:
        logger.debug(f"Old dashboard message {message_id} already deleted")
    except discord.Forbidden:
        logger.warning(f"No permission to delete old dashboard message {message_id}")
    except Exception as e:
        logger.error(f"Error deleting old dashboard: {e}", exc_info=True)


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


async def _update_activities_message(
    db: Database, user_id: int, bot: discord.Client = None
):
    """Update an existing activities dashboard message.

    If dashboard is not in memory but exists in database, automatically restore it.
    """
    if user_id not in _activities_messages:
        # Check if dashboard exists in database
        saved_dashboard = db.get_dashboard_message(user_id)

        if saved_dashboard and bot:
            channel_id, message_id = saved_dashboard
            logger.info(
                f"Dashboard not in memory for user {user_id}, attempting to restore from DB..."
            )

            try:
                # Try to restore the dashboard
                channel = bot.get_channel(channel_id)
                if channel is None:
                    channel = await bot.fetch_channel(channel_id)

                message = await channel.fetch_message(message_id)

                # Successfully restored - add to memory cache
                _activities_messages[user_id] = {
                    "message": message,
                    "channel": channel,
                    "timestamp": datetime.now(),
                }
                logger.info(
                    f"✅ Auto-restored dashboard for user {user_id} from database"
                )

            except (discord.NotFound, discord.Forbidden) as e:
                logger.warning(f"Could not restore dashboard for user {user_id}: {e}")
                db.delete_dashboard_message(user_id)
                return
            except Exception as e:
                logger.error(
                    f"Error restoring dashboard for user {user_id}: {e}", exc_info=True
                )
                return
        else:
            # No dashboard in memory or database
            logger.debug(
                f"No dashboard found for user {user_id} (not in memory or database)"
            )
            return

    dashboard_data = _activities_messages[user_id]
    message = dashboard_data["message"]
    channel = dashboard_data["channel"]

    try:
        embed = create_activities_embed(db, user_id)

        # Try to edit the message
        try:
            await message.edit(embed=embed)
        except discord.HTTPException as e:
            # If we get a webhook token error, re-fetch the message as a regular message
            if e.code == 50027:  # Invalid Webhook Token
                logger.debug(
                    f"Webhook token expired for user {user_id}, re-fetching message"
                )
                message = await channel.fetch_message(message.id)
                dashboard_data["message"] = message
                await message.edit(embed=embed)
            else:
                raise

        # Update timestamp on successful update
        dashboard_data["timestamp"] = datetime.now()
        logger.debug(f"Updated dashboard for user {user_id}")

    except discord.NotFound:
        logger.warning(f"Dashboard message for user {user_id} was deleted")
        del _activities_messages[user_id]
        db.delete_dashboard_message(user_id)

    except discord.Forbidden as e:
        logger.warning(f"No permission to access dashboard for user {user_id}: {e}")
        del _activities_messages[user_id]
        db.delete_dashboard_message(user_id)

    except Exception as e:
        logger.error(f"Error updating dashboard for user {user_id}: {e}", exc_info=True)


def setup_activity_commands(tree: app_commands.CommandTree, db: Database, config):
    """Setup activities-related commands."""

    @tree.command(name="activities", description="Показать все активности и прогресс")
    @app_commands.describe(force_new="Создать новую панель (игнорировать существующую)")
    async def activities_command(
        interaction: discord.Interaction, force_new: bool = False
    ):
        """Show activities dashboard (ONE per user, persistent)."""
        user_id = interaction.user.id

        # Clean up expired message cache entries
        _clean_message_cache()

        await interaction.response.defer(ephemeral=False)

        try:
            # === FORCE NEW: Create fresh dashboard, delete old one ===
            if force_new:
                # Delete old dashboard if exists
                old_dashboard = db.get_dashboard_message(user_id)
                if old_dashboard:
                    old_channel_id, old_message_id = old_dashboard
                    logger.info(
                        f"Force creating new dashboard for user {user_id}, deleting old one"
                    )
                    await _delete_old_dashboard(
                        interaction.client, user_id, old_channel_id, old_message_id
                    )
                    db.delete_dashboard_message(user_id)

                # Clean memory cache
                if user_id in _activities_messages:
                    del _activities_messages[user_id]

                # Create new dashboard directly
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
                    f"Force-created new dashboard for user {user_id} "
                    f"(channel: {interaction.channel_id}, msg: {message.id})"
                )
                return
            # === END FORCE NEW ===

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

                except (discord.NotFound, discord.Forbidden) as e:
                    logger.info(
                        f"Previous dashboard for user {user_id} is no longer accessible ({type(e).__name__}), will create new one"
                    )
                    # Clean up memory cache
                    del _activities_messages[user_id]
                    # Don't delete from DB yet - we'll handle that below

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
                        f"Saved dashboard for user {user_id} no longer accessible, deleting and creating new one"
                    )
                    # Try to delete the old message if we can access it
                    await _delete_old_dashboard(
                        interaction.client, user_id, channel_id, message_id
                    )
                    # Clean up database reference
                    db.delete_dashboard_message(user_id)

            # No existing dashboard found OR old one was inaccessible
            # Delete any old dashboard from DB before creating new one
            old_dashboard = db.get_dashboard_message(user_id)
            if old_dashboard:
                old_channel_id, old_message_id = old_dashboard
                logger.info(
                    f"Deleting old dashboard for user {user_id} before creating new one"
                )
                await _delete_old_dashboard(
                    interaction.client, user_id, old_channel_id, old_message_id
                )
                db.delete_dashboard_message(user_id)

            # Create a new dashboard
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

        # KEY FIX: Search through MORE activities initially
        # This ensures we have enough uncompleted activities after filtering
        # Even if the first 25 matches are all completed, we'll still have options
        results = search_activities(current, max_results=AUTOCOMPLETE_SEARCH_BUFFER)

        # Filter out completed activities
        uncompleted = [
            activity
            for activity in results
            if activity["id"] not in completed_activities
        ]

        # Create choices (limit to Discord's autocomplete maximum)
        choices = [
            app_commands.Choice(
                name=activity["name"][:DISCORD_CHOICE_NAME_MAX_LENGTH],
                value=activity["id"],
            )
            for activity in uncompleted[:DISCORD_AUTOCOMPLETE_LIMIT]
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

        await interaction.response.defer(ephemeral=False)

        activity_data = get_activity_by_id(activity)
        if not activity_data:
            await interaction.followup.send("Активность не найдена!", ephemeral=True)
            return

        if db.get_activity_status(user_id, activity, today):
            await interaction.followup.send(
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

        # Use followup instead of response
        response_message = await interaction.followup.send(
            f"Активность **{activity_data['name']}** выполнена!\n"
            f"+{bp} BP\n"
            f"Текущий баланс: {new_balance} BP",
            wait=True,
        )

        # Schedule deletion
        asyncio.create_task(_delete_message_after_delay(response_message, 10))

        # Update dashboard (auto-restores from DB if needed)
        await _update_activities_message(db, user_id, interaction.client)

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

        # KEY FIX: Search through MORE activities initially
        results = search_activities(current, max_results=AUTOCOMPLETE_SEARCH_BUFFER)

        # Filter to only show completed activities
        completed = [
            activity for activity in results if activity["id"] in completed_activity_ids
        ]

        # Create choices (limit to Discord's autocomplete maximum)
        choices = [
            app_commands.Choice(
                name=activity["name"][:DISCORD_CHOICE_NAME_MAX_LENGTH],
                value=activity["id"],
            )
            for activity in completed[:DISCORD_AUTOCOMPLETE_LIMIT]
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

        await interaction.response.defer(ephemeral=False)

        activity_data = get_activity_by_id(activity)
        if not activity_data:
            await interaction.followup.send("Активность не найдена!", ephemeral=True)
            return

        if not db.get_activity_status(user_id, activity, today):
            await interaction.followup.send(
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

        # Use followup instead of response
        response_message = await interaction.followup.send(
            f"Активность **{activity_data['name']}** отменена.\n"
            f"-{bp} BP\n"
            f"Текущий баланс: {new_balance} BP",
            wait=True,
        )

        # Schedule deletion
        asyncio.create_task(_delete_message_after_delay(response_message, 10))

        # Update dashboard (auto-restores from DB if needed)
        await _update_activities_message(db, user_id, interaction.client)
