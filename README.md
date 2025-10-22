# Discord Bonus Points Bot

A Discord bot for tracking daily bonus points activities with VIP support and BP balance tracking.

## 📋 Features

- **41 Daily Activities** - Track 33 solo + 8 paired activities
- **BP Balance System** - Persistent balance tracking across days
- **VIP Support** - Double rewards for VIP users
- **x2 Events** - Admin-toggleable double BP events
- **Smart Command System** - Slash commands with autocomplete
- **Persistent Storage** - SQLite database for all data
- **Daily Reset** - Automatic activity reset at 07:00 Moscow Time
- **Modular Architecture** - Clean, maintainable code structure

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Discord Bot Token ([Create one here](https://discord.com/developers/applications))

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/bonus_points_bot.git
   cd bonus_points_bot
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure the bot**
   ```bash
   cp .env.example .env
   # Edit .env and add your Discord bot token
   ```

4. **Run the bot**
   ```bash
   python run.py
   ```

## 📁 Project Structure

```
bonus_points_bot/
│
├── bot/                     # All bot-related code
│   ├── __init__.py
│   ├── main.py             # Main bot entry point
│   │
│   ├── core/               # Core bot functionality
│   │   ├── __init__.py
│   │   ├── bot.py          # Bot class and setup
│   │   ├── config.py       # Configuration management
│   │   └── database.py     # Database operations
│   │
│   ├── commands/           # Command modules
│   │   ├── __init__.py
│   │   ├── activities.py   # Activity-related commands
│   │   ├── balance.py      # Balance-related commands
│   │   ├── admin.py        # Admin commands
│   │   └── help.py         # Help command
│   │
│   ├── data/               # Data definitions
│   │   ├── __init__.py
│   │   └── activities.py   # Activity definitions
│   │
│   └── utils/              # Utility functions
│       ├── __init__.py
│       ├── embeds.py       # Embed creation utilities
│       └── helpers.py      # Helper functions
│
├── data/                   # Runtime data (not in git)
│   └── bonus_points.db     # SQLite database
│
├── logs/                   # Log files (not in git)
│   └── bot.log            # Bot activity logs
│
├── .env                    # Environment variables (not in git)
├── .env.example            # Example environment file
├── .gitignore             # Git ignore rules
├── README.md              # This file
├── requirements.txt       # Python dependencies
└── run.py                 # Entry point script
```

## 💻 Commands

### User Commands

#### 📋 Activities
- `/activities` - View all activities and their completion status
- `/complete [activity]` - Mark an activity as completed (adds BP)
- `/uncomplete [activity]` - Mark an activity as incomplete (removes BP)

#### 💰 Balance
- `/balance` - View your current BP balance
- `/setbalance [amount]` - Set your BP balance to a specific amount
- `/total` - View today's earnings and total balance

#### ⚙️ Settings
- `/setvip [true/false]` - Enable/disable VIP status
- `/eventstatus` - Check if x2 BP event is active

#### 📖 Help
- `/help` - Show all available commands

### Admin Commands

- `/toggleevent [true/false]` - Enable/disable x2 BP event (requires admin role or Administrator permission)

## 🎯 BP Balance System

The bot tracks your total BP balance persistently:

1. **Initial Setup**: Use `/setbalance 1000` to set your starting balance
2. **Earn BP**: Complete activities with `/complete` to add BP
3. **Track Progress**: Use `/balance` or `/total` to check your balance
4. **Undo Mistakes**: Use `/uncomplete` to reverse an activity

### Example Usage

```
/setbalance 1500
→ ✅ Balance set: 1500 BP

/complete browser
→ ✅ Activity "Visit any website" completed!
   +2 BP
   Current balance: 1502 BP

/balance
→ 💰 Bonus Points Balance: 1502 BP
   VIP Status: ❌ Inactive

/total
→ 💰 Today's Total
   Earned today: 2 BP
   Current balance: 1502 BP
   Activities completed: 1/41
```

## 🎉 Event System

Administrators can enable x2 BP events that double all rewards:

- Base activity: 2 BP
- With VIP: 4 BP
- With Event: 4 BP
- VIP + Event: 8 BP

Events persist across bot restarts and are stored in the database.

## ⚙️ Configuration

Create a `.env` file with the following variables:

```env
# Required
DISCORD_TOKEN=your_bot_token_here

# Optional
GUILD_ID=your_guild_id_here           # For faster command sync
ADMIN_ROLE_ID=your_admin_role_id_here # Role that can toggle events
DOUBLE_BP_EVENT=False                 # Initial event state
```

## 📊 Database Schema

The bot uses SQLite with three tables:

- **users** - Stores user VIP status and BP balance
- **activities** - Tracks daily activity completions
- **settings** - Persistent bot configuration

## 🔧 Development

### Adding New Activities

Edit `bot/data/activities.py` to add new activities:

```python
{
    "id": "unique_id",
    "name": "Activity Name",
    "bp": 2,      # Base BP reward
    "bp_vip": 4,  # VIP BP reward
}
```

### Adding New Commands

1. Create a new module in `bot/commands/`
2. Define setup function for your commands
3. Import and call it in `bot/commands/__init__.py`

### Customizing Embeds

Modify `bot/utils/embeds.py` to change how information is displayed.

## 📝 Logging

Logs are stored in `logs/bot.log` with the following information:
- Bot startup and shutdown
- Command usage
- Database operations
- Error messages

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Discord.py for the excellent Discord API wrapper
- The Discord community for feedback and suggestions

## 💡 Tips

- Use autocomplete when typing `/complete` or `/uncomplete` commands
- Check `/help` anytime to see all available commands
- Use `/total` daily to track your progress
- Set realistic BP goals with `/activities` to see what you can achieve

## 🐛 Troubleshooting

### Bot won't start
- Check that your Discord token is correctly set in `.env`
- Ensure Python 3.8+ is installed
- Verify all dependencies are installed with `pip install -r requirements.txt`

### Commands not showing up
- If GUILD_ID is set, commands sync instantly to that guild
- Global commands can take up to 1 hour to propagate
- Try kicking and re-inviting the bot to your server

### Database errors
- Ensure the `data/` directory exists and is writable
- Delete `bonus_points.db` to reset the database (will lose all data)
