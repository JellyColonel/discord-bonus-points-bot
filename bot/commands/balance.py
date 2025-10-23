# bonus_points_bot/bot/commands/balance.py
"""Balance-related commands."""

import logging

import discord
from discord import app_commands

from bot.core.database import get_today_date
from bot.data import TOTAL_ACTIVITIES, get_activity_by_id
from bot.utils.helpers import calculate_bp, is_event_active

logger = logging.getLogger(__name__)


def setup_balance_commands(tree, db, config):
    """Setup balance-related commands."""

    @tree.command(name="balance", description="Показать текущий баланс BP")
    async def balance_command(interaction: discord.Interaction):
        try:
            balance = db.get_user_bp_balance(interaction.user.id)
            vip_status = db.get_user_vip_status(interaction.user.id)

            embed = discord.Embed(
                title="💰 Баланс Бонусных Очков",
                description=f"**{balance} BP**",
                color=discord.Color.gold() if vip_status else discord.Color.green(),
            )

            embed.add_field(
                name="VIP Статус",
                value="✅ Активен" if vip_status else "❌ Неактивен",
                inline=True,
            )

            if is_event_active(db):
                embed.add_field(name="Событие", value="🎉 x2 BP активно!", inline=True)

            embed.set_footer(text="Используйте /help для списка всех команд")

            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            logger.error(
                f"Error in balance command for user {interaction.user.id}: {e}",
                exc_info=True,
            )
            await interaction.response.send_message(
                "❌ Произошла ошибка при получении баланса. Попробуйте позже.",
                ephemeral=True,
            )

    @tree.command(name="setbalance", description="Установить текущий баланс BP")
    @app_commands.describe(amount="Количество BP")
    async def setbalance_command(interaction: discord.Interaction, amount: int):
        try:
            if amount < 0:
                await interaction.response.send_message(
                    "❌ Баланс не может быть отрицательным!",
                    ephemeral=True,
                )
                return

            # Reasonable limit to prevent typos (e.g., accidentally typing 999999999)
            if amount > 1000000:
                await interaction.response.send_message(
                    "❌ Баланс не может превышать 1,000,000 BP!",
                    ephemeral=True,
                )
                return

            db.set_user_bp_balance(interaction.user.id, amount)

            await interaction.response.send_message(
                f"✅ Баланс установлен: **{amount} BP**",
                ephemeral=True,
            )
            logger.info(f"User {interaction.user.id} set balance to {amount}")
        except Exception as e:
            logger.error(
                f"Error in setbalance command for user {interaction.user.id}: {e}",
                exc_info=True,
            )
            await interaction.response.send_message(
                "❌ Произошла ошибка при установке баланса. Попробуйте позже.",
                ephemeral=True,
            )

    @tree.command(
        name="total", description="Показать общее количество заработанных BP за день"
    )
    async def total_command(interaction: discord.Interaction):
        try:
            vip_status = db.get_user_vip_status(interaction.user.id)
            today = get_today_date()
            completed_activities = db.get_user_completed_activities(
                interaction.user.id, today
            )

            total_bp = 0

            for activity_id in completed_activities:
                activity = get_activity_by_id(activity_id)
                if activity:
                    points = calculate_bp(activity, vip_status, db)
                    total_bp += points

            balance = db.get_user_bp_balance(interaction.user.id)
            event_status = "\n🎉 **Событие x2 активно!**" if is_event_active(db) else ""

            embed = discord.Embed(
                title="💰 Итого за сегодня",
                description=(
                    f"**Заработано сегодня: {total_bp} BP**\n"
                    f"**Текущий баланс: {balance} BP**\n\n"
                    f"Выполнено активностей: {len(completed_activities)}/{len(TOTAL_ACTIVITIES)}\n"
                    f"VIP статус: {'✅' if vip_status else '❌'}{event_status}"
                ),
                color=discord.Color.gold()
                if is_event_active(db)
                else discord.Color.green(),
            )

            embed.set_footer(text="Используйте /help для списка всех команд")

            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            logger.error(
                f"Error in total command for user {interaction.user.id}: {e}",
                exc_info=True,
            )
            await interaction.response.send_message(
                "❌ Произошла ошибка при подсчёте итогов. Попробуйте позже.",
                ephemeral=True,
            )

    @tree.command(name="setvip", description="Установить VIP статус")
    @app_commands.describe(status="VIP статус (true/false)")
    async def setvip_command(interaction: discord.Interaction, status: bool):
        try:
            db.set_user_vip_status(interaction.user.id, status)
            await interaction.response.send_message(
                f"VIP статус {'✅ активирован' if status else '❌ деактивирован'}",
                ephemeral=True,
            )
            logger.info(f"User {interaction.user.id} set VIP status to {status}")
        except Exception as e:
            logger.error(
                f"Error in setvip command for user {interaction.user.id}: {e}",
                exc_info=True,
            )
            await interaction.response.send_message(
                "❌ Произошла ошибка при установке VIP статуса. Попробуйте позже.",
                ephemeral=True,
            )
