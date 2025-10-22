import discord
from discord import app_commands

import config
from activities import get_activity_by_id, get_all_activities
from database import get_today_date
from utils import calculate_bp, create_activities_embed, is_event_active


class BonusCommands(app_commands.Group):
    def __init__(self, db):
        super().__init__()
        self.db = db


def has_admin_role(interaction: discord.Interaction) -> bool:
    """Check if user has admin role"""
    # First check for administrator permission
    if interaction.user.guild_permissions.administrator:
        return True

    # Then check for admin role if configured with a valid ID
    if config.ADMIN_ROLE_ID and config.ADMIN_ROLE_ID.isdigit():
        admin_role = discord.utils.get(
            interaction.user.roles, id=int(config.ADMIN_ROLE_ID)
        )
        return admin_role is not None

    return False


def setup_commands(tree, db):
    """Setup all bot commands"""

    @tree.command(name="commands", description="Показать список всех команд")
    async def commands_command(interaction: discord.Interaction):
        embed = discord.Embed(
            title="📖 Справка по командам",
            description="Полный список доступных команд бота",
            color=discord.Color.blue(),
        )

        # User commands - Activities
        activities_cmds = (
            "**`/activities`** - Показать все активности и их статус\n"
            "**`/complete [активность]`** - Отметить активность как выполненную (добавляет BP)\n"
            "**`/uncomplete [активность]`** - Отменить выполнение активности (вычитает BP)\n"
        )
        embed.add_field(name="📋 Активности", value=activities_cmds, inline=False)

        # User commands - Balance
        balance_cmds = (
            "**`/balance`** - Показать текущий баланс BP\n"
            "**`/setbalance [количество]`** - Установить баланс BP\n"
            "**`/total`** - Показать заработок за день и общий баланс\n"
        )
        embed.add_field(name="💰 Баланс", value=balance_cmds, inline=False)

        # User commands - Settings
        settings_cmds = (
            "**`/setvip [true/false]`** - Включить/выключить VIP статус\n"
            "**`/eventstatus`** - Проверить статус события x2 BP\n"
        )
        embed.add_field(name="⚙️ Настройки", value=settings_cmds, inline=False)

        # Admin commands
        if has_admin_role(interaction):
            admin_cmds = (
                "**`/toggleevent [true/false]`** - Включить/выключить событие x2 BP\n"
            )
            embed.add_field(
                name="👑 Команды администратора", value=admin_cmds, inline=False
            )

        # Additional info
        embed.add_field(
            name="ℹ️ Дополнительная информация",
            value=(
                "• VIP статус удваивает награду за активности\n"
                "• Событие x2 BP удваивает все награды\n"
                "• VIP + Событие = 4x базовая награда\n"
                "• Баланс BP сохраняется между днями\n"
                "• Активности сбрасываются в 07:00 по МСК"
            ),
            inline=False,
        )

        embed.set_footer(
            text="Используйте автодополнение для выбора активностей в /complete и /uncomplete"
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

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

    @tree.command(name="setvip", description="Установить VIP статус")
    @app_commands.describe(status="VIP статус (true/false)")
    async def setvip_command(interaction: discord.Interaction, status: bool):
        db.set_user_vip_status(interaction.user.id, status)
        await interaction.response.send_message(
            f"VIP статус {'✅ активирован' if status else '❌ деактивирован'}",
            ephemeral=True,
        )

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
            embed.add_field(name="Событие", value="🎉 x2 BP активно!", inline=True)

        embed.set_footer(text="Используйте /commands для списка всех команд")

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @tree.command(name="setbalance", description="Установить текущий баланс BP")
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
        name="total", description="Показать общее количество заработанных BP за день"
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
            description=f"**Заработано сегодня: {total_bp} BP**\n"
            f"**Текущий баланс: {balance} BP**\n\n"
            f"Выполнено активностей: {len(completed_activities)}/{len(all_activities)}\n"
            f"VIP статус: {'✅' if vip_status else '❌'}{event_status}",
            color=discord.Color.gold()
            if is_event_active(db)
            else discord.Color.green(),
        )

        embed.set_footer(text="Используйте /commands для списка всех команд")

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @tree.command(
        name="toggleevent", description="[ADMIN] Включить/выключить событие x2 BP"
    )
    @app_commands.describe(enabled="Включить событие (true/false)")
    async def toggleevent_command(interaction: discord.Interaction, enabled: bool):
        # Check admin permissions
        if not has_admin_role(interaction):
            await interaction.response.send_message(
                "❌ У вас нет прав для использования этой команды!", ephemeral=True
            )
            return

        # Toggle event
        db.set_setting("double_bp_event", str(enabled))

        embed = discord.Embed(
            title="🎉 Событие x2 BP" if enabled else "⚙️ Событие x2 BP",
            description=f"Событие x2 BP {'**АКТИВИРОВАНО**' if enabled else '**ДЕАКТИВИРОВАНО**'}!\n\n"
            f"Все бонусные очки теперь умножаются на {'**2**' if enabled else '**1**'}.",
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

        embed.set_footer(text="Используйте /commands для списка всех команд")

        await interaction.response.send_message(embed=embed, ephemeral=True)
