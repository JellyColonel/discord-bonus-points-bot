# 💎 Bonus Points Web Dashboard

A web dashboard for tracking daily bonus points activities. Features VIP support, BP balance tracking, and an intuitive web interface for managing activities.

> **Note:** This is the web-only version. The Discord bot has been removed.

## ✨ Features

### Core Features
- **40+ Daily Activities** - Track solo and paired activities
- **BP Balance System** - Persistent balance tracking across days
- **VIP Support** - Double rewards for VIP users (toggleable)
- **x2 Events** - Admin-toggleable double BP events
- **Daily Reset** - Activities reset at 07:00 Moscow Time (04:00 UTC)
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
- **Activity Caching** - O(1) lookups for fast operations
- **Database Indexing** - Optimized queries for fast performance
- **WAL Mode** - Better concurrent access for web server

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Discord OAuth2 Application configured for web dashboard

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/bonus_points_web.git
   cd bonus_points_web
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   venv\Scripts\activate  # Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure the application**
   ```bash
   cp .env.example .env
   # Edit .env and add your configuration
   ```

5. **Run the web server**
   ```bash
   python run.py
   ```
   
   The web dashboard will be available at http://localhost:5000

## ⚙️ Configuration

Create a `.env` file with the following variables:

```env
# Discord OAuth2 (Get from: https://discord.com/developers/applications)
DISCORD_CLIENT_ID=your_client_id_here
DISCORD_CLIENT_SECRET=your_client_secret_here
DISCORD_REDIRECT_URI=http://localhost:5000/callback

# Flask Secret Key (Generate with: python -c "import secrets; print(secrets.token_hex(32))")
SECRET_KEY=your_random_secret_key_here

# Web Server Settings (Optional)
WEB_HOST=0.0.0.0
WEB_PORT=5000
WEB_DEBUG=False
```

### Getting Discord OAuth2 Credentials

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application (or select existing)
3. Go to "OAuth2" section
4. Copy your Client ID and Client Secret
5. Add redirect URI: `http://localhost:5000/callback`
6. Under OAuth2 > URL Generator, select scopes: `identify`, `guilds`

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

#### Option 1: Local Development
```bash
python run.py
```

#### Option 2: Production with Gunicorn
```bash
gunicorn -w 4 -b 0.0.0.0:5000 web.app:app
```

#### Option 3: Cloudflare Tunnel (Recommended for Public Access)
No VPS or port forwarding needed:
```bash
cloudflared tunnel --url http://localhost:5000
```

## 🎯 BP Balance System

The dashboard tracks your total BP balance persistently:

1. **Initial Setup**: Set your starting balance using the balance control
2. **Earn BP**: Complete activities to add BP
3. **Track Progress**: View progress bars and statistics
4. **Undo Mistakes**: Uncheck activities to remove BP

### BP Calculation

- **Base activity**: 2 BP (or custom value per activity)
- **With VIP**: 2x multiplier
- **With Event**: 2x multiplier
- **VIP + Event**: 4x multiplier

## 🎉 Event System

Administrators can enable x2 BP events that double all rewards. Events persist across restarts and are stored in the database.

To toggle events, use the API endpoint:
```bash
POST /api/toggle_event
Body: {"event_status": true}
```

## 📊 Database Schema

The application uses SQLite with the following tables:

- **users** - Stores user VIP status and BP balance
- **activities** - Tracks daily activity completions with timestamps
- **settings** - Persistent configuration (event status, etc.)

## 📁 Project Structure

```
bonus_points_web/
├── web/                    # Web dashboard code
│   ├── __init__.py
│   ├── app.py             # Flask application
│   ├── auth.py            # Discord OAuth2
│   ├── config.py          # Web configuration
│   ├── database.py        # Database operations
│   ├── activities.py      # Activity definitions
│   ├── helpers.py         # Helper functions
│   ├── templates/         # HTML templates
│   │   ├── base.html     # Base template
│   │   ├── dashboard.html # Main dashboard
│   │   └── login.html    # Login page
│   └── static/           # Static assets
│       ├── css/
│       │   └── style.css # Dashboard styles
│       └── js/
│           └── dashboard.js # Dashboard logic
├── data/                  # Runtime data (not in git)
│   └── bonus_points.db   # SQLite database
├── logs/                 # Log files (not in git)
│   └── web.log          # Activity logs
├── .env                  # Environment variables (not in git)
├── .env.example         # Example environment file
├── .gitignore          # Git ignore rules
├── README.md           # This file
├── requirements.txt    # Python dependencies
└── run.py             # Main entry point
```

## 🔧 Development

### Adding New Activities

Edit `web/activities.py`:

```python
{
    "id": "unique_id",
    "name": "Activity Name",
    "bp": 2,      # Base BP reward
    "bp_vip": 4,  # VIP BP reward
}
```

### Customizing the Dashboard

- **Styles**: Edit `web/static/css/style.css`
- **Layout**: Edit `web/templates/dashboard.html`
- **Behavior**: Edit `web/static/js/dashboard.js`
- **Colors**: Modify CSS variables in `:root` selector

## 📝 Logging

Logs are stored in `logs/web.log` with:
- Server startup and shutdown
- User login/logout
- Activity completions
- Balance changes
- Error messages with stack traces

## 🛠 Troubleshooting

### Web dashboard not accessible
- Ensure Flask is running (check console output)
- Verify port 5000 is not in use
- Check Discord OAuth2 redirect URI matches your configuration
- For public access, use Cloudflare Tunnel

### Database errors
- Ensure `data/` directory exists and is writable
- Check file permissions on `bonus_points.db`
- For corruption, backup and delete database (will lose data)

### OAuth2 Issues
- **Error: "Redirect URI mismatch"**
  - Ensure redirect URI in `.env` matches Discord Developer Portal exactly
  - Include protocol (http:// or https://)

## 💡 Tips

- **Web Dashboard**: Best for managing multiple activities at once
- **VIP Status**: Toggle via the VIP badge on dashboard
- **Search**: Use the search box for 40+ activities
- **Mobile**: Dashboard is fully responsive - use on any device
- **Completion History**: Completed tab shows most recent activities first

## 🔐 Security Notes

- Never commit `.env` file to git
- Keep `SECRET_KEY` random and secure (generate with `secrets.token_hex(32)`)
- Only share your client secret securely
- Use HTTPS in production (Cloudflare Tunnel provides this)
- Regularly update dependencies for security patches

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

Made with ❤️ for tracking daily activities and staying motivated!
