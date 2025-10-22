"""Admin commands module."""

import discord
from discord import app_commands

from bot.utils.helpers import has_admin_role, is_event_active


def setup_admin_commands(tree, db, config):
    """Setup admin commands."""

    @tree.command(
        name="toggleevent", description="[ADMIN] Включить/выключить событие x2 BP"
    )
    @app_commands.describe(enabled="Включить событие (true/false)")
    async def toggleevent_command(interaction: discord.Interaction, enabled: bool):
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

    @tree.command(name="eventstatus", description="Проверить статус события x2 BP")
    async def eventstatus_command(interaction: discord.Interaction):
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
