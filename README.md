# Bonus Points Web Dashboard

A web dashboard for tracking daily bonus points activities. Features VIP support, BP balance tracking, and an intuitive web interface for managing activities.

> **Note:** This is the web-only version. The Discord bot has been removed.

## Features

### Core Features
- **40+ Daily Activities** — Track solo and paired activities
- **BP Balance System** — Persistent balance tracking across days
- **VIP Support** — Double rewards for VIP users (toggleable)
- **x2 Events** — Per-user double BP events
- **Daily Reset** — Activities reset at 07:00 Moscow Time (04:00 UTC)
- **Completion Timestamps** — Shows local time when each activity was completed
- **Repeatable Activities** — Activities like "3 hours online" can be completed multiple times per day with +/- controls
- **Activity Help Tooltips** — Hover `?` icon for activity descriptions
- **Hidden Activities** — Hide irrelevant activities from your dashboard
- **Activity Reset** — Clear all today's completions without changing BP balance
- **First-Login Onboarding** — 3-step modal guides new users through setting BP balance, VIP, and event status

### Web Dashboard
- **Discord OAuth2 Login** — Secure authentication with your Discord account
- **Real-time Updates** — Dynamic activity management without page reloads
- **Mobile Responsive** — Clean interface that works on all devices
- **Activity Search** — Quickly find activities among 40+ options
- **Progress Tracking** — Visual progress bars and statistics
- **Tabbed Interface** — Separate views for active and completed activities
- **Settings Page** — VIP/event toggle, balance control, hidden activities, activity reset

### Performance & Infrastructure
- **Activity Caching** — O(1) lookups for fast operations
- **Database Indexing** — Optimized queries for fast performance
- **WAL Mode** — Better concurrent access for web server
- **Docker Support** — `docker-compose up --build` for containerized deployment
- **74 Tests** — Database, API, validation, and helper test coverage

## Quick Start

### Prerequisites

- Python 3.12 or higher
- Discord OAuth2 Application configured for web dashboard

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/JellyColonel/discord-bonus-points-bot.git
   cd discord-bonus-points-bot
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

### Docker Setup

1. **Configure the application**
   ```bash
   cp .env.example .env
   # Edit .env and add your configuration
   ```

2. **Build and run**
   ```bash
   docker-compose up --build
   ```

   The container runs Gunicorn with 4 workers on port 5000. Data and logs are persisted via volume mounts (`./data` and `./logs`).

   To run in the background:
   ```bash
   docker-compose up --build -d
   ```

   To stop:
   ```bash
   docker-compose down
   ```

   Common commands:
   ```bash
   docker-compose ps                  # Container status
   docker-compose logs -f             # Live log output
   docker-compose logs --tail 100     # Last 100 lines
   docker-compose exec web bash       # Shell into the container
   docker-compose up --build -d       # Rebuild after code changes
   ```

## Configuration

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
SESSION_LIFETIME_DAYS=30  # Optional, default 30
```

### Getting Discord OAuth2 Credentials

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application (or select existing)
3. Go to "OAuth2" section
4. Copy your Client ID and Client Secret
5. Add redirect URI: `http://localhost:5000/callback`
6. Under OAuth2 > URL Generator, select scopes: `identify`, `guilds`

## Web Dashboard

Access the web dashboard at `http://localhost:5000` (or your configured host).

### Features:
- **Activity Management** — Check/uncheck activities with real-time updates
- **Repeatable Activities** — +/- counter for activities that can be completed multiple times (e.g. "3 hours online")
- **Completion Timestamps** — Shows local time (e.g. "в 14:30") for each completed activity
- **Help Tooltips** — Hover the `?` icon on activities with descriptions
- **Search & Filter** — Find activities by name, type (solo/pair), or time investment
- **Two Tabs:**
  - **Active Activities** — Uncompleted activities in definition order
  - **Completed Activities** — Recently completed activities (newest first)
- **Statistics Cards** — Balance, progress bar, earned today, and remaining BP
- **Settings Page** — VIP/event toggle, balance control, hide activities, reset today's completions

### Deployment Options

#### Local Development
Activate the virtual environment first (see [Installation](#installation)), then:
```bash
python run.py
```

#### Production with PM2

PM2 manages the process with auto-restart and log rotation.

**Option A — Gunicorn (recommended for production):**
```bash
pm2 start "gunicorn -w 4 -b 0.0.0.0:5000 web.app:app" --name bonus-points
```

**Option B — Flask dev server (simpler, fine for low traffic):**
```bash
pm2 start run.py --name bonus-points --interpreter ./venv/bin/python
```
This runs Flask's built-in single-threaded server. It works for a personal dashboard but doesn't handle concurrent requests.

**Persist across reboots:**
```bash
pm2 save
pm2 startup   # Run the command it outputs
```

Common commands:
```bash
pm2 status                          # Process list
pm2 show bonus-points               # Detailed info
pm2 logs bonus-points               # Live log output
pm2 logs bonus-points --lines 100   # Last 100 lines
pm2 monit                           # CPU/RAM monitor
pm2 restart bonus-points
pm2 stop bonus-points
pm2 delete bonus-points             # Remove from PM2
```

**Deploying updates:**
```bash
git pull origin main
pip install -r requirements.txt   # If dependencies changed
pm2 restart bonus-points
pm2 logs bonus-points --lines 20  # Verify no errors
```

**Deploying with database schema changes:**
```bash
pm2 stop bonus-points
cp data/bonus_points.db data/backup_$(date +%Y%m%d_%H%M%S).db
git pull origin main
pip install -r requirements.txt
pm2 start bonus-points
pm2 logs bonus-points --lines 20
```
Schema migrations run automatically on startup via `init_db()`.

#### Docker
```bash
docker-compose up --build -d
```

#### Cloudflare Tunnel (Recommended for Public Access)

No VPS or port forwarding needed. Quick mode for development:
```bash
cloudflared tunnel --url http://localhost:5000
```

For a persistent tunnel, create a named tunnel and configure it as a systemd service:
```bash
cloudflared tunnel create my-tunnel
```

Config file (`/etc/cloudflared/config.yml`):
```yaml
tunnel: <tunnel-id>
credentials-file: /root/.cloudflared/<tunnel-id>.json

ingress:
  - hostname: your.domain.com
    service: http://127.0.0.1:5000
  - service: http_status:404
```

```bash
sudo cloudflared service install
sudo systemctl enable cloudflared
sudo systemctl start cloudflared
```

> **Note:** The systemd service reads from `/etc/cloudflared/config.yml`, not `~/.cloudflared/config.yml`. Always edit the correct file.

## BP Balance System

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

## Event System

Each user can toggle their own x2 BP event via the Settings page. Events are per-user (not global) and persist across restarts in the database.

To toggle events programmatically:
```bash
POST /api/toggle_event
Body: {"event_status": true}
```

## Database Schema

The application uses SQLite with the following tables:

- **users** — VIP status (`vip_status`), BP balance (`bp_balance`), event flag (`event_active`)
- **activities** — Daily activity completions with `completed_at` timestamp and `bp_earned` snapshot. UNIQUE on `(user_id, activity_id, date)`
- **repeatable_completions** — Multiple completions per activity per day (e.g. "3 hours online"). Each row stores `bp_earned` and `completed_at`
- **hidden_activities** — Per-user hidden activity preferences
- **settings** — Key-value persistent configuration

## Project Structure

```
bonus_points_bot/
├── web/                        # Web dashboard code
│   ├── __init__.py
│   ├── app.py                 # Flask app factory, blueprint registration
│   ├── auth.py                # Discord OAuth2 flow + require_auth decorator
│   ├── config.py              # WebConfig from .env
│   ├── database.py            # Database class (SQLite, thread-local, WAL)
│   ├── activities.py          # Activity definitions + cached lookups
│   ├── helpers.py             # Rate limiting, BP calc, data preparation
│   ├── middleware.py          # Request logging, session refresh
│   ├── validation.py          # Input validators, API response helpers
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── pages.py           # Page routes (login, dashboard, settings)
│   │   └── api.py             # API routes (/api/* JSON endpoints)
│   ├── templates/
│   │   ├── base.html          # Base layout (navbar, footer)
│   │   ├── dashboard.html     # Activity dashboard (tabs, cards, filters)
│   │   ├── settings.html      # Settings page (VIP, balance, reset)
│   │   ├── login.html         # Login page
│   │   └── errors/
│   │       ├── 404.html       # Not found error page
│   │       └── 500.html       # Server error page
│   └── static/
│       ├── css/
│       │   └── style.css      # All styles, CSS variables, responsive
│       └── js/
│           ├── common.js      # Shared utilities (CSRF, loading, toasts)
│           ├── dashboard.js   # Dashboard logic (toggle, filter, repeat)
│           └── settings.js    # Settings logic (VIP, balance, reset)
├── tests/
│   ├── __init__.py
│   ├── conftest.py            # Fixtures (temp DB, test client, auth)
│   ├── test_database.py       # DB operation tests
│   ├── test_api.py            # API endpoint tests
│   ├── test_validation.py     # Input validator tests
│   └── test_helpers.py        # Helper function tests
├── data/                      # Runtime data (gitignored)
│   └── bonus_points.db
├── logs/                      # Log files (gitignored)
├── Dockerfile
├── docker-compose.yml
├── requirements.txt           # Production dependencies (pinned)
├── requirements-dev.txt       # Dev dependencies (pytest, ruff)
├── pyproject.toml             # Ruff + pytest config
├── run.py                     # Entry point
├── CLAUDE.md                  # AI assistant instructions
├── .env.example               # Environment variable template
├── .gitignore
├── .dockerignore
├── .editorconfig
└── LICENSE                    # MIT License
```

## Development

### Adding New Activities

Edit `web/activities.py` — append to the `ACTIVITIES` list:

```python
{
    "id": "unique_id",           # Alphanumeric + underscore, max 50 chars
    "name": "Display Name",      # Shown on dashboard
    "bp": 2,                     # Base BP reward
    "type": "solo",              # "solo" or "pair"
    "time": "low",               # "low", "medium", or "high"
    "description": "Optional",   # Shown as ? tooltip (optional)
    "repeatable": False,         # True for +/- counter UI (optional)
}
```

### Running Tests

```bash
pip install -r requirements-dev.txt
pytest tests/ -v    # 74 tests
ruff check web/     # Linter
```

### Customizing the Dashboard

- **Styles**: Edit `web/static/css/style.css`
- **Layout**: Edit `web/templates/dashboard.html`
- **Behavior**: Edit `web/static/js/dashboard.js`
- **Colors**: Modify CSS variables in `:root` selector

## Logging

Logs are stored in `logs/web.log` with:
- Server startup and shutdown
- User login/logout
- Activity completions
- Balance changes
- Error messages with stack traces

## Troubleshooting

### Web dashboard not accessible
1. Check if the app is running: `pm2 list`
2. Check app logs: `pm2 logs bonus-points --lines 50`
3. If using Cloudflare Tunnel, check tunnel status: `systemctl status cloudflared`
4. Check tunnel logs: `journalctl -u cloudflared -n 50`
5. Verify port 5000 is not in use by another process

### Database errors
- Ensure `data/` directory exists and is writable
- Check file permissions on `bonus_points.db`
- Backup before destructive actions: `cp data/bonus_points.db data/backup_$(date +%Y%m%d_%H%M%S).db`
- Schema auto-migrates on startup via `init_db()`

### OAuth2 Issues
- Ensure `DISCORD_REDIRECT_URI` in `.env` matches exactly what's registered in Discord Developer Portal
- Include protocol (http:// or https://) — use https if behind Cloudflare Tunnel

### After server reboot
Both PM2 and cloudflared start automatically on boot if configured correctly. Verify:
```bash
pm2 list
systemctl status cloudflared
```

## Tips

- **Web Dashboard**: Best for managing multiple activities at once
- **VIP Status**: Toggle via the VIP badge on dashboard
- **Search**: Use the search box for 40+ activities
- **Mobile**: Dashboard is fully responsive - use on any device
- **Completion History**: Completed tab shows most recent activities first

## Security Notes

- Never commit `.env` file to git
- Keep `SECRET_KEY` random and secure (generate with `secrets.token_hex(32)`)
- Only share your client secret securely
- Use HTTPS in production (Cloudflare Tunnel provides this)
- Regularly update dependencies for security patches

## License

This project is licensed under the MIT License - see the LICENSE file for details.
