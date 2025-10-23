# bonus_points_bot/bot/commands/admin.py
"""Admin commands module."""

import logging
from datetime import datetime, timedelta

import discord
import pytz
from discord import app_commands

from bot.utils.helpers import has_admin_role, is_event_active

logger = logging.getLogger(__name__)


def setup_admin_commands(tree, db, config):
    """Setup admin commands."""

    @tree.command(
        name="toggleevent", description="[ADMIN] Включить/выключить событие x2 BP"
    )
    @app_commands.describe(enabled="Включить событие (true/false)")
    async def toggleevent_command(interaction: discord.Interaction, enabled: bool):
        try:
            # Check admin permissions
            if not has_admin_role(interaction, config):
                await interaction.response.send_message(
                    "❌ У вас нет прав для использования этой команды!", ephemeral=True
                )
                return

            # Toggle event
            db.set_setting("double_bp_event", str(enabled))

            embed = discord.Embed(
                title="🎉 Событие x2 BP" if enabled else "⚙️ Событие x2 BP",
                description=(
                    f"Событие x2 BP {'**АКТИВИРОВАНО**' if enabled else '**ДЕАКТИВИРОВАНО**'}!\n\n"
                    f"Все бонусные очки теперь умножаются на {'**2**' if enabled else '**1**'}."
                ),
                color=discord.Color.gold() if enabled else discord.Color.blue(),
            )

            embed.add_field(
                name="Изменено администратором",
                value=f"{interaction.user.mention}",
                inline=False,
            )

            await interaction.response.send_message(embed=embed)
            logger.info(f"Admin {interaction.user.id} toggled event to {enabled}")
        except Exception as e:
            logger.error(f"Error in toggleevent command: {e}", exc_info=True)
            await interaction.response.send_message(
                "❌ Произошла ошибка при изменении события. Попробуйте позже.",
                ephemeral=True,
            )

    @tree.command(name="eventstatus", description="Проверить статус события x2 BP")
    async def eventstatus_command(interaction: discord.Interaction):
        try:
            event_active = is_event_active(db)

            embed = discord.Embed(
                title="🎉 Статус События x2 BP"
                if event_active
                else "⚙️ Статус События x2 BP",
                description=f"Событие x2 BP: {'**АКТИВНО** 🎉' if event_active else '**НЕАКТИВНО**'}",
                color=discord.Color.gold() if event_active else discord.Color.blue(),
            )

            if event_active:
                embed.add_field(
                    name="Множитель BP",
                    value="Все активности дают **в 2 раза больше** бонусных очков!",
                    inline=False,
                )

            embed.set_footer(text="Используйте /help для списка всех команд")

            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            logger.error(f"Error in eventstatus command: {e}", exc_info=True)
            await interaction.response.send_message(
                "❌ Произошла ошибка при проверке статуса события. Попробуйте позже.",
                ephemeral=True,
            )

    @tree.command(name="testreset", description="[ADMIN] Test daily reset manually")
    async def testreset_command(interaction: discord.Interaction):
        try:
            # Check admin permissions
            if not has_admin_role(interaction, config):
                await interaction.response.send_message(
                    "❌ У вас нет прав для использования этой команды!", ephemeral=True
                )
                return

            await interaction.response.send_message(
                "🔄 Запускаю тестовый сброс...", ephemeral=True
            )

            logger.info(f"Manual reset triggered by admin {interaction.user.id}")

            conn = db.get_connection()
            cursor = conn.cursor()

            today = datetime.now(pytz.timezone("Europe/Moscow")).strftime("%Y-%m-%d")

            cursor.execute(
                """
                UPDATE activities 
                SET completed = 0 
                WHERE date = ?
            """,
                (today,),
            )

            reset_count = cursor.rowcount

            cutoff_date = (
                datetime.now(pytz.timezone("Europe/Moscow")) - timedelta(days=30)
            ).strftime("%Y-%m-%d")
            cursor.execute("DELETE FROM activities WHERE date < ?", (cutoff_date,))

            deleted = cursor.rowcount
            conn.commit()
            conn.close()

            await interaction.followup.send(
                f"✅ Сброс выполнен успешно!\n"
                f"Сброшено активностей: {reset_count}\n"
                f"Удалено старых записей: {deleted}",
                ephemeral=True,
            )
            logger.info(
                f"Manual reset complete - reset {reset_count} activities, deleted {deleted} old records"
            )
        except Exception as e:
            logger.error(f"Error in testreset command: {e}", exc_info=True)
            try:
                await interaction.followup.send(
                    f"❌ Ошибка при сбросе: {e}", ephemeral=True
                )
            except discord.HTTPException:
                # If followup fails, try response
                try:
                    await interaction.response.send_message(
                        f"❌ Ошибка при сбросе: {e}", ephemeral=True
                    )
                except discord.HTTPException:
                    # Both failed, just log it
                    logger.error(
                        f"Could not send error message to user {interaction.user.id}"
                    )
