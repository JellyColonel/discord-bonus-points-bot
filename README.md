# 💎 Discord Bonus Points Bot

A Discord bot with web dashboard for tracking daily bonus points activities. Features VIP support, BP balance tracking, and an intuitive web interface for managing activities.

## ✨ Features

### Core Features
- **40+ Daily Activities** - Track solo and paired activities
- **BP Balance System** - Persistent balance tracking across days
- **VIP Support** - Double rewards for VIP users (toggleable)
- **x2 Events** - Admin-toggleable double BP events
- **Daily Reset** - Automatic activity reset at 07:00 Moscow Time
- **Completion Timestamps** - Track when activities were completed (sorted by most recent)

### Web Dashboard
- **Discord OAuth2 Login** - Secure authentication with your Discord account
- **Real-time Updates** - Dynamic activity management without page reloads
- **Mobile Responsive** - Clean interface that works on all devices
- **Activity Search** - Quickly find activities among 40+ options
- **Progress Tracking** - Visual progress bars and statistics
- **Tabbed Interface** - Separate views for active and completed activities
- **One-Click VIP Toggle** - Easy VIP status management
- **Balance Management** - Set balance directly from the dashboard

### Performance Optimizations
- **Activity Caching** - O(1) lookups for fast autocomplete
- **Database Indexing** - Optimized queries for 80-85% faster performance
- **WAL Mode** - Better concurrent access for Discord bot + web server
- **Connection Pooling** - Efficient database resource management

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Discord Bot Token ([Create one here](https://discord.com/developers/applications))
- Discord OAuth2 Application configured for web dashboard

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
   # Edit .env and add your configuration
   ```

4. **Run the bot and web server**
   ```bash
   python run.py
   ```
   
   This starts both:
   - Discord bot on your configured server
   - Web dashboard on http://localhost:5000

## ⚙️ Configuration

Create a `.env` file with the following variables:

```env
# Discord Bot Configuration
DISCORD_TOKEN=your_bot_token_here
GUILD_ID=your_guild_id_here           # Optional: for faster command sync
ADMIN_ROLE_ID=your_admin_role_id_here # Role that can toggle events

# Web Dashboard Configuration
DISCORD_CLIENT_ID=your_client_id_here
DISCORD_CLIENT_SECRET=your_client_secret_here
DISCORD_REDIRECT_URI=http://localhost:5000/callback
SECRET_KEY=your_random_secret_key_here

# Optional
DOUBLE_BP_EVENT=False                 # Initial event state
```

### Getting Discord OAuth2 Credentials

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Select your application
3. Go to "OAuth2" section
4. Copy your Client ID and Client Secret
5. Add redirect URI: `http://localhost:5000/callback`
6. Under OAuth2 > URL Generator, select scopes: `identify`, `guilds`

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

## 🌐 Web Dashboard

Access the web dashboard at `http://localhost:5000` (or your configured host).

### Features:
- **Activity Management** - Check/uncheck activities with real-time updates
- **Search & Filter** - Find activities quickly with search functionality
- **Two Tabs:**
  - **Active Activities** - Uncompleted activities in category order
  - **Completed Activities** - Recently completed activities (newest first)
- **VIP Toggle** - Click the VIP badge to toggle status
- **Balance Control** - Set your balance directly from the interface
- **Statistics Cards** - View balance, progress, earned today, and remaining BP

### Deployment Options:

#### Option 1: Same Server (Local/VPS)
The web dashboard runs alongside the Discord bot. Just ensure port 5000 is accessible.

#### Option 2: Cloudflare Tunnel (Recommended for Public Access)
No VPS or port forwarding needed! Use Cloudflare Tunnel to expose your local dashboard:
```bash
cloudflared tunnel --url http://localhost:5000
```

## 🎯 BP Balance System

The bot tracks your total BP balance persistently:

1. **Initial Setup**: Use `/setbalance 1000` or the web dashboard to set your starting balance
2. **Earn BP**: Complete activities via Discord or web dashboard to add BP
3. **Track Progress**: Use `/balance`, `/total`, or view the dashboard
4. **Undo Mistakes**: Use `/uncomplete` or uncheck activities on the dashboard

### BP Calculation

- **Base activity**: 2 BP
- **With VIP**: 4 BP (2x multiplier)
- **With Event**: 4 BP (2x multiplier)
- **VIP + Event**: 8 BP (4x multiplier)

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

Administrators can enable x2 BP events that double all rewards. Events persist across bot restarts and are stored in the database.

## 📊 Database Schema

The bot uses SQLite with the following tables:

- **users** - Stores user VIP status and BP balance
- **activities** - Tracks daily activity completions with timestamps
  - `completed_at` - Records when each activity was completed (for sorting)
- **settings** - Persistent bot configuration (event status, etc.)

### Recent Schema Updates
- Added `completed_at` timestamp column for tracking completion times
- Completed activities now sort by most recent first
- Optimized indexes for faster queries

## 📁 Project Structure

```
bonus_points_bot/
│
├── bot/                       # Discord bot code
│   ├── __init__.py
│   ├── main.py               # Bot entry point
│   ├── core/                 # Core functionality
│   │   ├── bot.py           # Bot setup
│   │   ├── config.py        # Configuration
│   │   └── database.py      # Database operations
│   ├── commands/            # Command modules
│   │   ├── activities.py   # Activity commands
│   │   ├── balance.py      # Balance commands
│   │   ├── admin.py        # Admin commands
│   │   └── help.py         # Help command
│   ├── data/               # Data definitions
│   │   └── activities.py  # Activity definitions
│   └── utils/             # Utilities
│       ├── embeds.py     # Discord embeds
│       └── helpers.py    # Helper functions
│
├── web/                    # Web dashboard code
│   ├── __init__.py
│   ├── app.py             # Flask application
│   ├── auth.py            # Discord OAuth2
│   ├── config.py          # Web configuration
│   ├── templates/         # HTML templates
│   │   ├── base.html     # Base template
│   │   ├── dashboard.html # Main dashboard
│   │   └── login.html    # Login page
│   └── static/           # Static assets
│       ├── css/
│       │   └── style.css # Dashboard styles
│       └── js/
│           └── dashboard.js # Dashboard logic
│
├── data/                  # Runtime data (not in git)
│   └── bonus_points.db   # SQLite database
│
├── logs/                 # Log files (not in git)
│   └── bot.log          # Activity logs
│
├── .env                  # Environment variables (not in git)
├── .env.example         # Example environment file
├── .gitignore          # Git ignore rules
├── README.md           # This file
├── requirements.txt    # Python dependencies
└── run.py             # Main entry point (starts bot + web)
```

## 🔧 Development

### Adding New Activities

Edit `bot/data/activities.py`:

```python
{
    "id": "unique_id",
    "name": "Activity Name",
    "bp": 2,      # Base BP reward
    "bp_vip": 4,  # VIP BP reward
}
```

Activities are automatically available in both Discord commands and web dashboard.

### Adding New Commands

1. Create a new module in `bot/commands/`
2. Define setup function for your commands
3. Import and call it in `bot/commands/__init__.py`

### Customizing the Dashboard

- **Styles**: Edit `web/static/css/style.css`
- **Layout**: Edit `web/templates/dashboard.html`
- **Behavior**: Edit `web/static/js/dashboard.js`
- **Colors**: Modify CSS variables in `:root` selector

## 📝 Logging

Logs are stored in `logs/bot.log` with:
- Bot startup and shutdown
- Command usage
- Database operations
- Web server requests
- Error messages with stack traces

## 🐛 Troubleshooting

### Bot won't start
- Check Discord token in `.env`
- Ensure Python 3.8+ is installed
- Install dependencies: `pip install -r requirements.txt`
- Check `logs/bot.log` for error details

### Commands not showing up
- If GUILD_ID is set, commands sync instantly to that guild
- Global commands can take up to 1 hour to propagate
- Try kicking and re-inviting the bot

### Web dashboard not accessible
- Ensure Flask is running (check console output)
- Verify port 5000 is not in use
- Check Discord OAuth2 redirect URI matches your configuration
- For public access, use Cloudflare Tunnel

### Database errors
- Ensure `data/` directory exists and is writable
- Check file permissions on `bonus_points.db`
- For corruption, backup and delete database (will lose data)

### Performance issues
- Database is optimized with indexes and WAL mode
- Activity cache provides O(1) autocomplete lookups
- If slow, check `logs/bot.log` for error patterns

## 💡 Tips

- **Autocomplete**: Use it when typing commands - saves time!
- **Web Dashboard**: Best for managing multiple activities at once
- **Discord Commands**: Great for quick single activity updates
- **VIP Status**: Toggle via web dashboard badge or `/setvip` command
- **Search**: Use the search box on dashboard for 40+ activities
- **Mobile**: Dashboard is fully responsive - use on any device
- **Completion History**: Completed tab shows most recent activities first

## 🔐 Security Notes

- Never commit `.env` file to git
- Keep `SECRET_KEY` random and secure (generate with `secrets.token_hex(32)`)
- Only share your bot token and client secret securely
- Use HTTPS in production (Cloudflare Tunnel provides this)
- Regularly update dependencies for security patches

## 🚀 Performance Features

- **Activity Caching**: Lightning-fast autocomplete with O(1) lookups
- **Database Indexing**: Specialized indexes for different query patterns
- **WAL Mode**: Concurrent access for bot + web server
- **Query Batching**: Efficient data retrieval
- **Connection Pooling**: Optimized database connections

## 📈 Recent Improvements

### v2.0 - Web Dashboard Release
- Complete web dashboard with Discord OAuth2
- Real-time activity updates
- Mobile-responsive design
- Activity search functionality
- Tabbed interface (Active/Completed)
- One-click VIP toggle

### v2.1 - Completion Tracking
- Added `completed_at` timestamps
- Completed activities sorted by most recent
- Database migration for existing installations

### v2.2 - UI Polish
- Platinum VIP badge styling
- Compact balance control layout
- Fixed emoji encoding issues
- Display name support (shows Discord display name)
- Improved mobile responsiveness

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Discord.py for the excellent Discord API wrapper
- Flask for the lightweight web framework
- SQLite for reliable embedded database
- The Discord community for feedback and suggestions

---

Made with ❤️ for tracking daily activities and staying motivated!