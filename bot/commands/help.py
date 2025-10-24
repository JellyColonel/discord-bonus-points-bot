# bonus_points_bot/bot/commands/help.py
"""Help command module."""

import logging

import discord

from bot.utils.helpers import has_admin_role

logger = logging.getLogger(__name__)


def setup_help_command(tree, db, config):
    """Setup help command."""

    @tree.command(name="help", description="Показать список всех команд")
    async def help_command(interaction: discord.Interaction):
        try:
            embed = discord.Embed(
                title="📖 Справка по командам",
                description="Полный список доступных команд бота",
                color=discord.Color.blue(),
            )

            # User commands - Activities
            activities_cmds = (
                "**`/activities`** - Показать персональную панель активностей\n"
                "**`/activities force_new: True`** - Создать новую панель (пересоздать/переместить в другой канал)\n"
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
            if has_admin_role(interaction, config):
                admin_cmds = (
                    "**`/toggleevent [true/false]`** - Включить/выключить событие x2 BP\n"
                    "**`/testreset`** - Тестовый сброс активностей\n"
                )
                embed.add_field(
                    name="👑 Команды администратора", value=admin_cmds, inline=False
                )

            # Additional info
            embed.add_field(
                name="ℹ️ Дополнительная информация",
                value=(
                    "• Панель `/activities` сохраняется между перезапусками бота\n"
                    "• У каждого пользователя одна персональная панель\n"
                    "• Используйте `force_new: True` чтобы пересоздать или переместить панель в другой канал\n"
                    "• VIP статус удваивает награду за активности\n"
                    "• Событие x2 BP удваивает все награды\n"
                    "• VIP + Событие = 4x базовая награда\n"
                    "• Баланс BP сохраняется между днями\n"
                    "• Активности сбрасываются в 07:00 по МСК\n"
                    "• Сообщения `/complete` и `/uncomplete` удаляются через 10 секунд"
                ),
                inline=False,
            )

            embed.set_footer(
                text="Используйте автодополнение для выбора активностей в /complete и /uncomplete"
            )

            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            logger.error(f"Error in help command: {e}", exc_info=True)
            try:
                await interaction.response.send_message(
                    "❌ Произошла ошибка при отображении справки. Попробуйте позже.",
                    ephemeral=True,
                )
            except discord.HTTPException:
                pass
