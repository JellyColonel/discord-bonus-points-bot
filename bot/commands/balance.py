"""Balance-related commands."""

import discord
from discord import app_commands

from core.database import get_today_date
from data import get_activity_by_id, get_all_activities
from utils.helpers import calculate_bp, is_event_active


def setup_balance_commands(tree, db, config):
    """Setup balance-related commands."""
    
    @tree.command(name="balance", description="Показать текущий баланс BP")
    async def balance_command(interaction: discord.Interaction):
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
            embed.add_field(
                name="Событие", 
                value="🎉 x2 BP активно!", 
                inline=True
            )

        embed.set_footer(text="Используйте /help для списка всех команд")

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @tree.command(
        name="setbalance", 
        description="Установить текущий баланс BP"
    )
    @app_commands.describe(amount="Количество BP")
    async def setbalance_command(interaction: discord.Interaction, amount: int):
        if amount < 0:
            await interaction.response.send_message(
                "❌ Баланс не может быть отрицательным!",
                ephemeral=True,
            )
            return

        db.set_user_bp_balance(interaction.user.id, amount)

        await interaction.response.send_message(
            f"✅ Баланс установлен: **{amount} BP**",
            ephemeral=True,
        )

    @tree.command(
        name="total", 
        description="Показать общее количество заработанных BP за день"
    )
    async def total_command(interaction: discord.Interaction):
        vip_status = db.get_user_vip_status(interaction.user.id)
        today = get_today_date()
        completed_activities = db.get_user_completed_activities(
            interaction.user.id, today
        )

        total_bp = 0
        all_activities = get_all_activities()

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
                f"Выполнено активностей: {len(completed_activities)}/{len(all_activities)}\n"
                f"VIP статус: {'✅' if vip_status else '❌'}{event_status}"
            ),
            color=discord.Color.gold() if is_event_active(db) else discord.Color.green(),
        )

        embed.set_footer(text="Используйте /help для списка всех команд")

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @tree.command(name="setvip", description="Установить VIP статус")
    @app_commands.describe(status="VIP статус (true/false)")
    async def setvip_command(interaction: discord.Interaction, status: bool):
        db.set_user_vip_status(interaction.user.id, status)
        await interaction.response.send_message(
            f"VIP статус {'✅ активирован' if status else '❌ деактивирован'}",
            ephemeral=True,
        )
