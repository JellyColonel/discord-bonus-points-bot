# Discord Bonus Points Bot

Discord bot for tracking daily bonus points activities with VIP support and BP balance tracking.

## Features

- Track 41 daily activities (33 solo + 8 paired)
- **BP Balance Tracking** - Track your total bonus points
- VIP status with doubled rewards
- **Double BP events** - Toggle with `/toggleevent` command (admin only)
- **Built-in help system** - Use `/help` to see all commands
- SQLite database for persistent storage
- Automatic daily reset at 07:00 Moscow Time
- Slash commands with autocomplete
- Secure configuration with `.env` files

## Quick Start

### First Time Setup
1. Set your initial BP balance: `/setbalance 1000`
2. Set VIP status if needed: `/setvip true`
3. View all commands: `/help`

### Daily Usage
1. Complete activities: `/complete [activity]`
2. Check progress: `/total`
3. View balance: `/balance`

## Commands

### General
- **`/help`** - Show all available commands with descriptions

### User Commands - Activities
- `/activities` - View all activities and status (shows current balance)
- `/complete [activity]` - Mark activity as completed (adds BP to balance)
- `/uncomplete [activity]` - Mark activity as incomplete (subtracts BP from balance)

### User Commands - Balance
- `/balance` - View your current BP balance
- `/setbalance [amount]` - Set your current BP balance
- `/total` - View total BP earned today and current balance

### User Commands - Settings
- `/setvip [true/false]` - Set VIP status
- `/eventstatus` - Check if x2 BP event is active

### Admin Commands
- `/toggleevent [true/false]` - Enable/disable x2 BP event (requires admin role or Administrator permission)

## BP Balance System

The bot now tracks your total BP balance:

1. **Set Initial Balance**: Use `/setbalance 1000` to set your starting BP
2. **Complete Activities**: Use `/complete` to mark activities done - BP is automatically added to your balance
3. **Undo Completion**: Use `/uncomplete` to undo - BP is automatically subtracted
4. **Check Balance**: Use `/balance` or `/total` to see your current BP

### Examples

```
/help
→ 📖 Справка по командам
   [Shows organized list of all commands]

/setbalance 1500
→ ✅ Баланс установлен: 1500 BP

/complete browser
→ ✅ Активность "Посетить любой сайт в браузере" отмечена как выполненная!
   +2 BP
   Текущий баланс: 1502 BP

/balance
→ 💰 Баланс Бонусных Очков: 1502 BP

/total
→ 💰 Итого за сегодня
   Заработано сегодня: 2 BP
   Текущий баланс: 1502 BP
```

## Help Command Features

The `/help` command provides:
- **Organized command list** - Commands grouped by category (Activities, Balance, Settings)
- **Clear descriptions** - Each command explained in Russian
- **Admin-aware** - Shows admin commands only to users with admin permissions
- **Additional info** - Explains VIP bonuses, events, and daily reset time
- **Always accessible** - Footer reminder on most commands

## Database

Creates `bonus_points.db` with three tables:
- `users` - User VIP status and BP balance
- `activities` - Daily activity completions
- `settings` - Bot configuration (including event status)

## Event Mode

Admins can enable x2 BP events using `/toggleevent true`:
- Shows 🎉 indicators in all responses
- Changes embed colors to gold
- Automatically calculates doubled BP for all activities
- Applies multiplier on top of VIP bonuses (VIP + Event = 4x base BP)
- Event status persists in database (survives bot restarts)

To disable: `/toggleevent false`

## Admin Setup

To use the `/toggleevent` command, either:
1. Set `ADMIN_ROLE_ID` in `.env` to your Discord admin role ID, OR
2. Have the "Administrator" permission in Discord

If `ADMIN_ROLE_ID` is not configured, only users with Administrator permission can toggle events.

## Tips

💡 **Use autocomplete** - When typing `/complete` or `/uncomplete`, start typing the activity name and Discord will show suggestions

💡 **Check help anytime** - Type `/help` to see all available commands

💡 **Track your progress** - Use `/total` daily to see how many BP you earned

💡 **Set realistic goals** - Use `/activities` to see which activities you've completed