"""Activity-related commands."""

import discord
from discord import app_commands

from bot.core.database import get_today_date
from bot.data import get_activity_by_id, get_all_activities
from bot.utils.embeds import create_activities_embed
from bot.utils.helpers import calculate_bp, is_event_active


def setup_activity_commands(tree, db, config):
    """Setup activity-related commands."""

    @tree.command(
        name="activities", description="Показать список всех активностей и их статус"
    )
    async def activities_command(interaction: discord.Interaction):
        embed = create_activities_embed(db, interaction.user.id)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @tree.command(name="complete", description="Отметить активность как выполненную")
    @app_commands.describe(activity="Выберите активность")
    async def complete_command(interaction: discord.Interaction, activity: str):
        activity_data = get_activity_by_id(activity)
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

        await interaction.response.send_message(
            f'✅ Активность "{activity_data["name"]}" отмечена как выполненная!\n'
            f"**+{points} BP{event_note}**\n"
            f"Текущий баланс: **{new_balance} BP**",
            ephemeral=True,
        )

    @complete_command.autocomplete("activity")
    async def complete_autocomplete(interaction: discord.Interaction, current: str):
        """Show only UNCOMPLETED activities"""
        today = get_today_date()
        completed_activities = db.get_user_completed_activities(
            interaction.user.id, today
        )
        all_activities = get_all_activities()

        choices = []
        for activity in all_activities:
            # Only show activities that are NOT completed
            if activity["id"] not in completed_activities:
                if (
                    current.lower() in activity["name"].lower()
                    or current.lower() in activity["id"].lower()
                ):
                    # Add checkmark to show status visually
                    choices.append(
                        app_commands.Choice(
                            name=f"{activity['name']} ({activity['bp']}/{activity['bp_vip']} BP)",
                            value=activity["id"],
                        )
                    )
        return choices[:25]

    @tree.command(
        name="uncomplete", description="Отметить активность как невыполненную"
    )
    @app_commands.describe(activity="Выберите активность")
    async def uncomplete_command(interaction: discord.Interaction, activity: str):
        activity_data = get_activity_by_id(activity)
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

        await interaction.response.send_message(
            f'❌ Активность "{activity_data["name"]}" отмечена как невыполненная.\n'
            f"**-{points} BP**\n"
            f"Текущий баланс: **{new_balance} BP**",
            ephemeral=True,
        )

    @uncomplete_command.autocomplete("activity")
    async def uncomplete_autocomplete(interaction: discord.Interaction, current: str):
        """Show only COMPLETED activities"""
        today = get_today_date()
        completed_activities = db.get_user_completed_activities(
            interaction.user.id, today
        )
        all_activities = get_all_activities()

        choices = []
        for activity in all_activities:
            # Only show activities that ARE completed
            if activity["id"] in completed_activities:
                if (
                    current.lower() in activity["name"].lower()
                    or current.lower() in activity["id"].lower()
                ):
                    # Add checkmark to show status visually
                    choices.append(
                        app_commands.Choice(
                            name=f"{activity['name']} ({activity['bp']}/{activity['bp_vip']} BP)",
                            value=activity["id"],
                        )
                    )
        return choices[:25]
