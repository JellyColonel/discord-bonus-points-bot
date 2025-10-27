# Web Dashboard Implementation Plan
## Discord Bonus Points Bot - Web Interface

---

## 📋 Overview

This plan will guide you through adding a web dashboard to your Discord bot, allowing users to complete activities, manage their balance, and view progress through a user-friendly web interface instead of slash commands.

**Timeline:** 6-10 hours total (can be done in phases)  
**Difficulty:** Intermediate  
**Cost:** $0 (using same server as bot)

---

## 🎯 Goals

- ✅ Web interface for all 41 activities with checkboxes
- ✅ Complete/uncomplete activities via web
- ✅ Set balance and toggle VIP status
- ✅ Discord OAuth2 authentication (users log in with Discord)
- ✅ Real-time updates to Discord dashboards
- ✅ Mobile-responsive design
- ✅ Runs on same server as bot (shared database)

---

## 📁 Final Project Structure

```
bonus_points_bot/
├── bot/                      # Existing bot code
│   ├── commands/
│   ├── core/
│   ├── data/
│   └── utils/
├── web/                      # NEW - Web dashboard
│   ├── __init__.py
│   ├── app.py               # Flask application
│   ├── auth.py              # Discord OAuth2
│   ├── config.py            # Web configuration
│   ├── templates/
│   │   ├── base.html        # Base template
│   │   ├── login.html       # Login page
│   │   └── dashboard.html   # Main dashboard
│   └── static/
│       ├── css/
│       │   └── style.css    # Styling
│       └── js/
│           └── dashboard.js # Interactivity
├── data/
│   └── bonus_points.db      # Shared database
├── .env                      # Add Discord OAuth credentials
├── requirements.txt          # Add Flask dependencies
└── run.py                    # Modified to run both bot and web
```

---

## Phase 1: Prerequisites & Setup (30 minutes)

### Step 1.1: Install Additional Dependencies

Add to `requirements.txt`:
```txt
# Existing dependencies
discord.py>=2.3.0
python-dotenv>=1.0.0

# NEW - Web dashboard dependencies
Flask>=3.0.0
Flask-Session>=0.5.0
requests>=2.31.0
gunicorn>=21.2.0
```

Install:
```bash
pip install -r requirements.txt
```

### Step 1.2: Create Discord OAuth2 Application

1. Go to https://discord.com/developers/applications
2. Select your bot application
3. Go to **OAuth2** → **General**
4. Add redirect URL: `http://localhost:5000/callback`
   - (Later add production URL: `https://yourdomain.com/callback`)
5. Copy **Client ID** and **Client Secret**
6. Go to **OAuth2** → **URL Generator**
   - Select scopes: `identify`, `guilds`
   - Copy the generated URL (for testing)

### Step 1.3: Update Environment Variables

Add to `.env`:
```env
# Existing bot config
DISCORD_TOKEN=...
GUILD_ID=...
ADMIN_ROLE_ID=...

# NEW - Web dashboard OAuth2
DISCORD_CLIENT_ID=your_client_id_here
DISCORD_CLIENT_SECRET=your_client_secret_here
DISCORD_REDIRECT_URI=http://localhost:5000/callback
SECRET_KEY=your_random_secret_key_here  # Generate with: python -c "import secrets; print(secrets.token_hex(32))"

# NEW - Web server settings
WEB_HOST=0.0.0.0
WEB_PORT=5000
WEB_DEBUG=False
```

Generate a secure secret key:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## Phase 2: Web Application Core (2-3 hours)

### Step 2.1: Create Web Configuration

**File:** `web/config.py`

```python
"""Web dashboard configuration."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

class WebConfig:
    """Web dashboard configuration."""
    
    # Flask settings
    SECRET_KEY = os.getenv("SECRET_KEY")
    SESSION_TYPE = "filesystem"
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    
    # Discord OAuth2
    DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
    DISCORD_CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")
    DISCORD_REDIRECT_URI = os.getenv("DISCORD_REDIRECT_URI")
    DISCORD_API_BASE = "https://discord.com/api/v10"
    DISCORD_OAUTH_URL = f"{DISCORD_API_BASE}/oauth2/authorize"
    DISCORD_TOKEN_URL = f"{DISCORD_API_BASE}/oauth2/token"
    DISCORD_USER_URL = f"{DISCORD_API_BASE}/users/@me"
    
    # Web server settings
    HOST = os.getenv("WEB_HOST", "0.0.0.0")
    PORT = int(os.getenv("WEB_PORT", 5000))
    DEBUG = os.getenv("WEB_DEBUG", "False") == "True"
    
    # Database path (shared with bot)
    ROOT_DIR = Path(__file__).parent.parent
    DB_PATH = ROOT_DIR / "data" / "bonus_points.db"
```

### Step 2.2: Create Discord OAuth2 Handler

**File:** `web/auth.py`

```python
"""Discord OAuth2 authentication."""
import requests
from flask import session, redirect, url_for, request
from web.config import WebConfig

def get_oauth_url():
    """Generate Discord OAuth2 authorization URL."""
    params = {
        "client_id": WebConfig.DISCORD_CLIENT_ID,
        "redirect_uri": WebConfig.DISCORD_REDIRECT_URI,
        "response_type": "code",
        "scope": "identify guilds"
    }
    
    url = WebConfig.DISCORD_OAUTH_URL
    param_string = "&".join([f"{k}={v}" for k, v in params.items()])
    return f"{url}?{param_string}"

def exchange_code(code):
    """Exchange authorization code for access token."""
    data = {
        "client_id": WebConfig.DISCORD_CLIENT_ID,
        "client_secret": WebConfig.DISCORD_CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": WebConfig.DISCORD_REDIRECT_URI
    }
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    response = requests.post(WebConfig.DISCORD_TOKEN_URL, data=data, headers=headers)
    response.raise_for_status()
    return response.json()

def get_user_info(access_token):
    """Get user information from Discord."""
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    response = requests.get(WebConfig.DISCORD_USER_URL, headers=headers)
    response.raise_for_status()
    return response.json()

def require_auth(f):
    """Decorator to require authentication for routes."""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    
    return decorated_function
```

### Step 2.3: Create Flask Application

**File:** `web/app.py`

```python
"""Flask web application for Discord Bonus Points Bot dashboard."""
import logging
from pathlib import Path

from flask import Flask, render_template, session, redirect, url_for, request, jsonify
from flask_session import Session

from web.config import WebConfig
from web.auth import get_oauth_url, exchange_code, get_user_info, require_auth
from bot.core.database import Database, get_today_date
from bot.data import get_all_activities, get_activity_by_id, ACTIVITIES
from bot.utils.helpers import calculate_bp, is_event_active

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(WebConfig)
Session(app)

# Initialize database
db = Database(str(WebConfig.DB_PATH))
logger.info(f"Web dashboard using database: {WebConfig.DB_PATH}")

# ============================================================================
# Authentication Routes
# ============================================================================

@app.route("/")
def index():
    """Landing page - redirect to dashboard if logged in, otherwise show login."""
    if "user" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/login")
def login():
    """Login page with Discord OAuth2."""
    if "user" in session:
        return redirect(url_for("dashboard"))
    
    oauth_url = get_oauth_url()
    return render_template("login.html", oauth_url=oauth_url)

@app.route("/callback")
def callback():
    """OAuth2 callback handler."""
    code = request.args.get("code")
    
    if not code:
        return "Error: No authorization code provided", 400
    
    try:
        # Exchange code for token
        token_data = exchange_code(code)
        access_token = token_data.get("access_token")
        
        # Get user info
        user_info = get_user_info(access_token)
        
        # Store in session
        session["user"] = {
            "id": user_info["id"],
            "username": user_info["username"],
            "discriminator": user_info.get("discriminator", "0"),
            "avatar": user_info.get("avatar"),
            "access_token": access_token
        }
        
        logger.info(f"User {user_info['username']} logged in (ID: {user_info['id']})")
        return redirect(url_for("dashboard"))
        
    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        return f"Authentication failed: {str(e)}", 500

@app.route("/logout")
def logout():
    """Logout and clear session."""
    if "user" in session:
        logger.info(f"User {session['user']['username']} logged out")
    session.clear()
    return redirect(url_for("login"))

# ============================================================================
# Dashboard Routes
# ============================================================================

@app.route("/dashboard")
@require_auth
def dashboard():
    """Main dashboard page."""
    user = session["user"]
    user_id = int(user["id"])
    today = get_today_date()
    
    # Get user data
    vip_status = db.get_user_vip_status(user_id)
    balance = db.get_user_bp_balance(user_id)
    completed_activities = set(db.get_user_completed_activities(user_id, today))
    event_active = is_event_active(db)
    
    # Prepare activities by category with completion status
    activities_by_category = {}
    total_earned = 0
    total_remaining = 0
    
    for category, activities in ACTIVITIES.items():
        activities_with_status = []
        
        for activity in activities:
            is_completed = activity["id"] in completed_activities
            bp_value = calculate_bp(activity, vip_status, db)
            
            if is_completed:
                total_earned += bp_value
            else:
                total_remaining += bp_value
            
            activities_with_status.append({
                **activity,
                "completed": is_completed,
                "bp_value": bp_value
            })
        
        activities_by_category[category] = activities_with_status
    
    # Calculate progress
    total_activities = len(get_all_activities())
    completed_count = len(completed_activities)
    progress_percentage = int((completed_count / total_activities) * 100) if total_activities > 0 else 0
    
    return render_template(
        "dashboard.html",
        user=user,
        activities=activities_by_category,
        vip_status=vip_status,
        balance=balance,
        total_earned=total_earned,
        total_remaining=total_remaining,
        completed_count=completed_count,
        total_activities=total_activities,
        progress_percentage=progress_percentage,
        event_active=event_active
    )

# ============================================================================
# API Routes
# ============================================================================

@app.route("/api/toggle_activity", methods=["POST"])
@require_auth
def api_toggle_activity():
    """Toggle activity completion status."""
    user_id = int(session["user"]["id"])
    data = request.json
    
    activity_id = data.get("activity_id")
    completed = data.get("completed", False)
    
    if not activity_id:
        return jsonify({"error": "Missing activity_id"}), 400
    
    activity = get_activity_by_id(activity_id)
    if not activity:
        return jsonify({"error": "Activity not found"}), 404
    
    today = get_today_date()
    
    # Update activity status
    db.set_activity_status(user_id, activity_id, today, completed)
    
    # Update balance
    vip_status = db.get_user_vip_status(user_id)
    bp = calculate_bp(activity, vip_status, db)
    
    if completed:
        new_balance = db.add_user_bp(user_id, bp)
        logger.info(f"User {user_id} completed {activity_id}: +{bp} BP")
    else:
        new_balance = db.subtract_user_bp(user_id, bp)
        logger.info(f"User {user_id} uncompleted {activity_id}: -{bp} BP")
    
    # TODO: Trigger Discord dashboard update via webhook
    # await _update_activities_message(db, user_id, bot)
    
    return jsonify({
        "success": True,
        "new_balance": new_balance,
        "bp_change": bp if completed else -bp
    })

@app.route("/api/set_balance", methods=["POST"])
@require_auth
def api_set_balance():
    """Set user balance."""
    user_id = int(session["user"]["id"])
    data = request.json
    
    amount = data.get("amount")
    
    if amount is None:
        return jsonify({"error": "Missing amount"}), 400
    
    try:
        amount = int(amount)
    except ValueError:
        return jsonify({"error": "Invalid amount"}), 400
    
    if amount < 0:
        return jsonify({"error": "Amount cannot be negative"}), 400
    
    if amount > 1000000:
        return jsonify({"error": "Amount cannot exceed 1,000,000"}), 400
    
    db.set_user_bp_balance(user_id, amount)
    logger.info(f"User {user_id} set balance to {amount} BP")
    
    # TODO: Trigger Discord dashboard update
    
    return jsonify({
        "success": True,
        "new_balance": amount
    })

@app.route("/api/toggle_vip", methods=["POST"])
@require_auth
def api_toggle_vip():
    """Toggle VIP status."""
    user_id = int(session["user"]["id"])
    data = request.json
    
    vip_status = data.get("vip_status", False)
    
    db.set_user_vip_status(user_id, vip_status)
    logger.info(f"User {user_id} set VIP status to {vip_status}")
    
    # TODO: Trigger Discord dashboard update
    
    return jsonify({
        "success": True,
        "vip_status": vip_status
    })

@app.route("/api/user_data", methods=["GET"])
@require_auth
def api_user_data():
    """Get current user data (for refreshing dashboard)."""
    user_id = int(session["user"]["id"])
    today = get_today_date()
    
    vip_status = db.get_user_vip_status(user_id)
    balance = db.get_user_bp_balance(user_id)
    completed_activities = db.get_user_completed_activities(user_id, today)
    event_active = is_event_active(db)
    
    return jsonify({
        "vip_status": vip_status,
        "balance": balance,
        "completed_activities": completed_activities,
        "event_active": event_active
    })

# ============================================================================
# Run Web Server
# ============================================================================

def run_web():
    """Run the Flask web server."""
    logger.info("=" * 80)
    logger.info("🌐 Starting Web Dashboard...")
    logger.info(f"   Host: {WebConfig.HOST}")
    logger.info(f"   Port: {WebConfig.PORT}")
    logger.info(f"   Database: {WebConfig.DB_PATH}")
    logger.info("=" * 80)
    
    app.run(
        host=WebConfig.HOST,
        port=WebConfig.PORT,
        debug=WebConfig.DEBUG,
        use_reloader=False  # Important when running with bot
    )

if __name__ == "__main__":
    run_web()
```

---

## Phase 3: Frontend Templates (2-3 hours)

### Step 3.1: Create Base Template

**File:** `web/templates/base.html`

```html
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Bonus Points Dashboard{% endblock %}</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
    {% block extra_css %}{% endblock %}
</head>
<body>
    <nav class="navbar">
        <div class="nav-container">
            <div class="nav-brand">
                <h1>💎 Bonus Points</h1>
            </div>
            {% if session.user %}
            <div class="nav-user">
                <span class="username">{{ session.user.username }}</span>
                <a href="{{ url_for('logout') }}" class="btn btn-secondary">Logout</a>
            </div>
            {% endif %}
        </div>
    </nav>

    <main class="container">
        {% block content %}{% endblock %}
    </main>

    <footer class="footer">
        <p>&copy; 2025 Bonus Points Bot. Made with ❤️ for your Discord server.</p>
    </footer>

    {% block extra_js %}{% endblock %}
</body>
</html>
```

### Step 3.2: Create Login Page

**File:** `web/templates/login.html`

```html
{% extends "base.html" %}

{% block title %}Login - Bonus Points Dashboard{% endblock %}

{% block content %}
<div class="login-container">
    <div class="login-card">
        <h2>Welcome to Bonus Points Dashboard</h2>
        <p>Login with your Discord account to manage your activities</p>
        
        <a href="{{ oauth_url }}" class="btn btn-discord">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                <path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515a.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0a12.64 12.64 0 0 0-.617-1.25a.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057a19.9 19.9 0 0 0 5.993 3.03a.078.078 0 0 0 .084-.028a14.09 14.09 0 0 0 1.226-1.994a.076.076 0 0 0-.041-.106a13.107 13.107 0 0 1-1.872-.892a.077.077 0 0 1-.008-.128a10.2 10.2 0 0 0 .372-.292a.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127a12.299 12.299 0 0 1-1.873.892a.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028a19.839 19.839 0 0 0 6.002-3.03a.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419c0-1.333.956-2.419 2.157-2.419c1.21 0 2.176 1.096 2.157 2.42c0 1.333-.956 2.418-2.157 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419c0-1.333.955-2.419 2.157-2.419c1.21 0 2.176 1.096 2.157 2.42c0 1.333-.946 2.418-2.157 2.418z"/>
            </svg>
            Login with Discord
        </a>
        
        <div class="features">
            <h3>Features:</h3>
            <ul>
                <li>✅ Complete activities with one click</li>
                <li>📊 Track your progress in real-time</li>
                <li>💰 Manage your BP balance</li>
                <li>📱 Mobile-friendly interface</li>
                <li>🔄 Syncs with Discord bot</li>
            </ul>
        </div>
    </div>
</div>
{% endblock %}
```

### Step 3.3: Create Dashboard Page

**File:** `web/templates/dashboard.html`

```html
{% extends "base.html" %}

{% block title %}Dashboard - Bonus Points{% endblock %}

{% block content %}
<div class="dashboard">
    <!-- Stats Header -->
    <div class="stats-header">
        <div class="stat-card">
            <h3>💰 Balance</h3>
            <p class="stat-value" id="balance-display">{{ balance }}</p>
            <span class="stat-label">BP</span>
        </div>
        
        <div class="stat-card">
            <h3>📊 Progress</h3>
            <div class="progress-bar">
                <div class="progress-fill" style="width: {{ progress_percentage }}%"></div>
            </div>
            <p class="stat-value">{{ completed_count }} / {{ total_activities }}</p>
        </div>
        
        <div class="stat-card">
            <h3>✨ Earned Today</h3>
            <p class="stat-value earned" id="earned-display">{{ total_earned }}</p>
            <span class="stat-label">BP</span>
        </div>
        
        <div class="stat-card">
            <h3>🎯 Remaining</h3>
            <p class="stat-value remaining" id="remaining-display">{{ total_remaining }}</p>
            <span class="stat-label">BP</span>
        </div>
    </div>

    <!-- Status Badges -->
    <div class="status-badges">
        <div class="badge {% if vip_status %}badge-vip{% else %}badge-inactive{% endif %}" id="vip-badge">
            {% if vip_status %}⭐ VIP Active{% else %}VIP Inactive{% endif %}
        </div>
        {% if event_active %}
        <div class="badge badge-event">🎉 x2 BP Event Active!</div>
        {% endif %}
    </div>

    <!-- Controls -->
    <div class="controls">
        <div class="control-group">
            <label for="balance-input">Set Balance:</label>
            <input type="number" id="balance-input" placeholder="Enter amount" min="0" max="1000000">
            <button onclick="setBalance()" class="btn btn-primary">Update</button>
        </div>
        
        <div class="control-group">
            <button onclick="toggleVIP()" class="btn btn-secondary" id="vip-toggle-btn">
                Toggle VIP Status
            </button>
        </div>
    </div>

    <!-- Activities by Category -->
    {% for category, category_activities in activities.items() %}
    <div class="activity-category">
        <h2 class="category-title">{{ category }}</h2>
        <div class="activity-grid">
            {% for activity in category_activities %}
            <div class="activity-card {% if activity.completed %}completed{% endif %}" 
                 data-activity-id="{{ activity.id }}">
                <div class="activity-header">
                    <input type="checkbox" 
                           id="activity-{{ activity.id }}" 
                           {% if activity.completed %}checked{% endif %}
                           onchange="toggleActivity('{{ activity.id }}', this.checked)">
                    <label for="activity-{{ activity.id }}">
                        {{ activity.name }}
                    </label>
                </div>
                <div class="activity-bp">
                    <span class="bp-value">{{ activity.bp_value }} BP</span>
                </div>
            </div>
            {% endfor %}
        </div>
    </div>
    {% endfor %}

    <!-- Loading Overlay -->
    <div id="loading-overlay" class="loading-overlay" style="display: none;">
        <div class="spinner"></div>
    </div>
</div>
{% endblock %}

{% block extra_js %}
<script src="{{ url_for('static', filename='js/dashboard.js') }}"></script>
{% endblock %}
```

---

## Phase 4: Frontend Styling & JavaScript (1-2 hours)

### Step 4.1: Create CSS Styles

**File:** `web/static/css/style.css`

```css
/* =================================================================
   Global Styles
   ================================================================= */

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

:root {
    --primary-color: #5865F2;
    --secondary-color: #3BA55D;
    --danger-color: #ED4245;
    --warning-color: #FEE75C;
    --background: #23272A;
    --surface: #2C2F33;
    --surface-light: #36393F;
    --text-primary: #FFFFFF;
    --text-secondary: #B9BBBE;
    --border: #202225;
    --success: #3BA55D;
    --vip-color: #FFD700;
}

body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    background: var(--background);
    color: var(--text-primary);
    line-height: 1.6;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
}

.container {
    max-width: 1400px;
    margin: 0 auto;
    padding: 20px;
    flex: 1;
}

/* =================================================================
   Navigation
   ================================================================= */

.navbar {
    background: var(--surface);
    border-bottom: 2px solid var(--border);
    padding: 15px 0;
}

.nav-container {
    max-width: 1400px;
    margin: 0 auto;
    padding: 0 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.nav-brand h1 {
    font-size: 24px;
    color: var(--text-primary);
}

.nav-user {
    display: flex;
    align-items: center;
    gap: 15px;
}

.username {
    color: var(--text-secondary);
    font-weight: 500;
}

/* =================================================================
   Buttons
   ================================================================= */

.btn {
    padding: 12px 24px;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    font-size: 16px;
    font-weight: 600;
    transition: all 0.3s ease;
    text-decoration: none;
    display: inline-flex;
    align-items: center;
    gap: 8px;
}

.btn-primary {
    background: var(--primary-color);
    color: white;
}

.btn-primary:hover {
    background: #4752C4;
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(88, 101, 242, 0.4);
}

.btn-secondary {
    background: var(--surface-light);
    color: var(--text-primary);
}

.btn-secondary:hover {
    background: #40444B;
}

.btn-discord {
    background: var(--primary-color);
    color: white;
    padding: 16px 32px;
    font-size: 18px;
}

.btn-discord svg {
    width: 24px;
    height: 24px;
}

/* =================================================================
   Login Page
   ================================================================= */

.login-container {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: calc(100vh - 200px);
    padding: 20px;
}

.login-card {
    background: var(--surface);
    border-radius: 16px;
    padding: 48px;
    max-width: 500px;
    width: 100%;
    text-align: center;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}

.login-card h2 {
    font-size: 32px;
    margin-bottom: 16px;
}

.login-card p {
    color: var(--text-secondary);
    margin-bottom: 32px;
}

.features {
    margin-top: 40px;
    text-align: left;
}

.features h3 {
    font-size: 20px;
    margin-bottom: 16px;
}

.features ul {
    list-style: none;
    padding: 0;
}

.features li {
    padding: 8px 0;
    color: var(--text-secondary);
}

/* =================================================================
   Dashboard
   ================================================================= */

.dashboard {
    padding: 20px 0;
}

/* Stats Header */
.stats-header {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 20px;
    margin-bottom: 30px;
}

.stat-card {
    background: var(--surface);
    border-radius: 12px;
    padding: 24px;
    text-align: center;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.stat-card h3 {
    font-size: 16px;
    color: var(--text-secondary);
    margin-bottom: 12px;
    text-transform: uppercase;
    letter-spacing: 1px;
}

.stat-value {
    font-size: 36px;
    font-weight: bold;
    color: var(--text-primary);
    margin: 8px 0;
}

.stat-value.earned {
    color: var(--success);
}

.stat-value.remaining {
    color: var(--warning-color);
}

.stat-label {
    font-size: 14px;
    color: var(--text-secondary);
}

/* Progress Bar */
.progress-bar {
    width: 100%;
    height: 12px;
    background: var(--surface-light);
    border-radius: 6px;
    overflow: hidden;
    margin: 12px 0;
}

.progress-fill {
    height: 100%;
    background: linear-gradient(90deg, var(--primary-color), var(--secondary-color));
    transition: width 0.3s ease;
}

/* Status Badges */
.status-badges {
    display: flex;
    gap: 12px;
    margin-bottom: 30px;
    flex-wrap: wrap;
}

.badge {
    padding: 10px 20px;
    border-radius: 8px;
    font-weight: 600;
    font-size: 14px;
}

.badge-vip {
    background: linear-gradient(135deg, var(--vip-color), #FFA500);
    color: var(--background);
}

.badge-inactive {
    background: var(--surface-light);
    color: var(--text-secondary);
}

.badge-event {
    background: linear-gradient(135deg, #FF6B6B, #FF8E53);
    color: white;
    animation: pulse 2s infinite;
}

@keyframes pulse {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.05); }
}

/* Controls */
.controls {
    background: var(--surface);
    border-radius: 12px;
    padding: 24px;
    margin-bottom: 30px;
    display: flex;
    gap: 24px;
    flex-wrap: wrap;
}

.control-group {
    display: flex;
    align-items: center;
    gap: 12px;
    flex: 1;
    min-width: 300px;
}

.control-group label {
    font-weight: 600;
    white-space: nowrap;
}

.control-group input {
    flex: 1;
    padding: 10px 16px;
    background: var(--surface-light);
    border: 2px solid var(--border);
    border-radius: 8px;
    color: var(--text-primary);
    font-size: 16px;
}

.control-group input:focus {
    outline: none;
    border-color: var(--primary-color);
}

/* Activity Categories */
.activity-category {
    margin-bottom: 40px;
}

.category-title {
    font-size: 24px;
    margin-bottom: 20px;
    padding-bottom: 12px;
    border-bottom: 2px solid var(--border);
}

.activity-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 16px;
}

.activity-card {
    background: var(--surface);
    border-radius: 10px;
    padding: 16px;
    border: 2px solid var(--border);
    transition: all 0.3s ease;
}

.activity-card:hover {
    border-color: var(--primary-color);
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(88, 101, 242, 0.2);
}

.activity-card.completed {
    border-color: var(--success);
    background: linear-gradient(135deg, var(--surface) 0%, rgba(59, 165, 93, 0.1) 100%);
}

.activity-header {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    margin-bottom: 12px;
}

.activity-header input[type="checkbox"] {
    width: 24px;
    height: 24px;
    cursor: pointer;
    accent-color: var(--success);
    flex-shrink: 0;
    margin-top: 2px;
}

.activity-header label {
    flex: 1;
    cursor: pointer;
    font-size: 15px;
    line-height: 1.4;
}

.activity-card.completed label {
    text-decoration: line-through;
    opacity: 0.7;
}

.activity-bp {
    display: flex;
    justify-content: flex-end;
}

.bp-value {
    background: var(--primary-color);
    color: white;
    padding: 6px 12px;
    border-radius: 6px;
    font-weight: 600;
    font-size: 14px;
}

.activity-card.completed .bp-value {
    background: var(--success);
}

/* Loading Overlay */
.loading-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.7);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 9999;
}

.spinner {
    width: 50px;
    height: 50px;
    border: 4px solid var(--surface-light);
    border-top: 4px solid var(--primary-color);
    border-radius: 50%;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

/* Footer */
.footer {
    background: var(--surface);
    border-top: 2px solid var(--border);
    padding: 20px;
    text-align: center;
    color: var(--text-secondary);
    margin-top: auto;
}

/* =================================================================
   Responsive Design
   ================================================================= */

@media (max-width: 768px) {
    .nav-container {
        flex-direction: column;
        gap: 15px;
    }
    
    .stats-header {
        grid-template-columns: 1fr;
    }
    
    .controls {
        flex-direction: column;
    }
    
    .control-group {
        min-width: 100%;
    }
    
    .activity-grid {
        grid-template-columns: 1fr;
    }
    
    .login-card {
        padding: 32px 24px;
    }
}

/* =================================================================
   Notifications/Toasts (for success/error messages)
   ================================================================= */

.toast {
    position: fixed;
    bottom: 24px;
    right: 24px;
    background: var(--surface);
    color: var(--text-primary);
    padding: 16px 24px;
    border-radius: 8px;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
    z-index: 10000;
    animation: slideIn 0.3s ease;
}

.toast.success {
    border-left: 4px solid var(--success);
}

.toast.error {
    border-left: 4px solid var(--danger-color);
}

@keyframes slideIn {
    from {
        transform: translateX(400px);
        opacity: 0;
    }
    to {
        transform: translateX(0);
        opacity: 1;
    }
}
```

### Step 4.2: Create JavaScript

**File:** `web/static/js/dashboard.js`

```javascript
// =================================================================
// Dashboard Interactivity
// =================================================================

// Global state
let isLoading = false;

// Show/hide loading overlay
function showLoading() {
    document.getElementById('loading-overlay').style.display = 'flex';
    isLoading = true;
}

function hideLoading() {
    document.getElementById('loading-overlay').style.display = 'none';
    isLoading = false;
}

// Show toast notification
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.remove();
    }, 3000);
}

// Toggle activity completion
async function toggleActivity(activityId, completed) {
    if (isLoading) return;
    
    showLoading();
    
    try {
        const response = await fetch('/api/toggle_activity', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                activity_id: activityId,
                completed: completed
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Update balance display
            document.getElementById('balance-display').textContent = data.new_balance;
            
            // Update activity card styling
            const card = document.querySelector(`[data-activity-id="${activityId}"]`);
            if (completed) {
                card.classList.add('completed');
            } else {
                card.classList.remove('completed');
            }
            
            // Refresh stats
            await refreshStats();
            
            showToast(
                `Activity ${completed ? 'completed' : 'uncompleted'} (+${data.bp_change} BP)`,
                'success'
            );
        } else {
            throw new Error(data.error || 'Unknown error');
        }
    } catch (error) {
        console.error('Error toggling activity:', error);
        showToast('Failed to update activity', 'error');
        
        // Revert checkbox
        const checkbox = document.getElementById(`activity-${activityId}`);
        checkbox.checked = !completed;
    } finally {
        hideLoading();
    }
}

// Set balance
async function setBalance() {
    const input = document.getElementById('balance-input');
    const amount = parseInt(input.value);
    
    if (isNaN(amount) || amount < 0) {
        showToast('Please enter a valid amount', 'error');
        return;
    }
    
    if (amount > 1000000) {
        showToast('Amount cannot exceed 1,000,000 BP', 'error');
        return;
    }
    
    showLoading();
    
    try {
        const response = await fetch('/api/set_balance', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ amount: amount })
        });
        
        const data = await response.json();
        
        if (data.success) {
            document.getElementById('balance-display').textContent = data.new_balance;
            input.value = '';
            showToast(`Balance updated to ${data.new_balance} BP`, 'success');
        } else {
            throw new Error(data.error || 'Unknown error');
        }
    } catch (error) {
        console.error('Error setting balance:', error);
        showToast('Failed to update balance', 'error');
    } finally {
        hideLoading();
    }
}

// Toggle VIP status
async function toggleVIP() {
    showLoading();
    
    try {
        // Get current VIP status from badge
        const vipBadge = document.getElementById('vip-badge');
        const currentVIP = vipBadge.classList.contains('badge-vip');
        const newVIP = !currentVIP;
        
        const response = await fetch('/api/toggle_vip', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ vip_status: newVIP })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Update badge
            if (data.vip_status) {
                vipBadge.classList.remove('badge-inactive');
                vipBadge.classList.add('badge-vip');
                vipBadge.textContent = '⭐ VIP Active';
            } else {
                vipBadge.classList.remove('badge-vip');
                vipBadge.classList.add('badge-inactive');
                vipBadge.textContent = 'VIP Inactive';
            }
            
            showToast(`VIP status ${data.vip_status ? 'activated' : 'deactivated'}`, 'success');
            
            // Refresh page to update BP values
            setTimeout(() => location.reload(), 1000);
        } else {
            throw new Error(data.error || 'Unknown error');
        }
    } catch (error) {
        console.error('Error toggling VIP:', error);
        showToast('Failed to toggle VIP status', 'error');
    } finally {
        hideLoading();
    }
}

// Refresh statistics
async function refreshStats() {
    try {
        const response = await fetch('/api/user_data');
        const data = await response.json();
        
        // Update balance
        document.getElementById('balance-display').textContent = data.balance;
        
        // TODO: Update earned/remaining (requires recalculation)
        
    } catch (error) {
        console.error('Error refreshing stats:', error);
    }
}

// Allow Enter key to submit balance
document.addEventListener('DOMContentLoaded', () => {
    const balanceInput = document.getElementById('balance-input');
    if (balanceInput) {
        balanceInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                setBalance();
            }
        });
    }
});

// Auto-refresh every 30 seconds (optional)
// setInterval(refreshStats, 30000);
```

---

## Phase 5: Integration with Bot (1 hour)

### Step 5.1: Modify `run.py` to Start Both Bot and Web

**File:** `run.py`

```python
#!/usr/bin/env python3
"""
Discord Bonus Points Bot
Main entry point for running the bot AND web dashboard.
"""

import logging
from threading import Thread
from bot.main import main as bot_main
from web.app import run_web

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("=" * 80)
    logger.info("🚀 Starting Bonus Points Bot + Web Dashboard")
    logger.info("=" * 80)
    
    # Start web server in background thread
    web_thread = Thread(target=run_web, daemon=True)
    web_thread.start()
    logger.info("✅ Web dashboard thread started")
    
    # Start bot (this blocks until bot stops)
    logger.info("🤖 Starting Discord bot...")
    bot_main()
    
    logger.info("=" * 80)
    logger.info("👋 Both bot and web dashboard have stopped")
    logger.info("=" * 80)
```

### Step 5.2: Create Web Package Init

**File:** `web/__init__.py`

```python
"""Web dashboard package for Discord Bonus Points Bot."""

__version__ = "1.0.0"
```

---

## Phase 6: Testing & Deployment (1-2 hours)

### Step 6.1: Local Testing

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Update `.env` with OAuth credentials:**
```env
DISCORD_CLIENT_ID=your_client_id
DISCORD_CLIENT_SECRET=your_client_secret
DISCORD_REDIRECT_URI=http://localhost:5000/callback
SECRET_KEY=generated_secret_key
```

3. **Run the bot:**
```bash
python run.py
```

4. **Test web dashboard:**
- Open browser: `http://localhost:5000`
- Click "Login with Discord"
- Complete OAuth flow
- Test activity completion
- Test balance setting
- Test VIP toggle

### Step 6.2: Production Deployment

**Option 1: Same server as bot (Recommended)**

1. **Update `.env` for production:**
```env
DISCORD_REDIRECT_URI=https://yourdomain.com/callback
WEB_DEBUG=False
```

2. **Use production WSGI server:**
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 web.app:app
```

3. **Setup reverse proxy (nginx):**
```nginx
server {
    listen 80;
    server_name dashboard.yourdomain.com;
    
    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

4. **Setup SSL with Let's Encrypt:**
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d dashboard.yourdomain.com
```

**Option 2: Using Cloudflare Tunnel (Free, Easy)**

1. **Install cloudflared:**
```bash
# Linux
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared-linux-amd64.deb
```

2. **Create tunnel:**
```bash
cloudflared tunnel create bonus-dashboard
```

3. **Configure tunnel:**
```yaml
# ~/.cloudflared/config.yml
tunnel: your-tunnel-id
credentials-file: /home/user/.cloudflared/your-tunnel-id.json

ingress:
  - hostname: dashboard.yourdomain.com
    service: http://localhost:5000
  - service: http_status:404
```

4. **Route DNS:**
```bash
cloudflared tunnel route dns bonus-dashboard dashboard.yourdomain.com
```

5. **Run tunnel:**
```bash
cloudflared tunnel run bonus-dashboard
```

### Step 6.3: Update Discord OAuth Redirect URLs

In Discord Developer Portal:
1. Go to OAuth2 → General
2. Add production redirect URL: `https://dashboard.yourdomain.com/callback`
3. Keep localhost URL for testing

---

## Phase 7: Bot Integration - Real-time Discord Updates (Optional - 1-2 hours)

This phase enables the web dashboard to update Discord dashboard messages in real-time.

### Step 7.1: Add Webhook Endpoint to Bot

**File:** `bot/core/bot.py` (add to BonusPointsBot class)

```python
from aiohttp import web
import asyncio

class BonusPointsBot(discord.Client):
    def __init__(self, db: Database, config):
        # ... existing code ...
        self.web_runner = None
        
    async def setup_webhook_server(self):
        """Setup webhook server for web dashboard integration."""
        app = web.Application()
        app.router.add_post('/webhook/update_dashboard', self.handle_dashboard_update)
        
        runner = web.AppRunner(app)
        await runner.setup()
        
        site = web.TCPSite(runner, 'localhost', 5001)
        await site.start()
        
        self.web_runner = runner
        logger.info("✅ Webhook server started on http://localhost:5001")
    
    async def handle_dashboard_update(self, request):
        """Handle dashboard update request from web."""
        try:
            data = await request.json()
            user_id = int(data.get('user_id'))
            
            # Import here to avoid circular imports
            from bot.commands.activities import _update_activities_message
            
            # Update Discord dashboard
            await _update_activities_message(self.db, user_id, self)
            
            return web.json_response({"success": True})
        except Exception as e:
            logger.error(f"Webhook error: {e}", exc_info=True)
            return web.json_response({"success": False, "error": str(e)}, status=500)
    
    async def on_ready(self):
        # ... existing on_ready code ...
        
        # Start webhook server
        await self.setup_webhook_server()
```

### Step 7.2: Update Web App to Notify Bot

**In `web/app.py`**, add after each API endpoint that modifies data:

```python
import requests

def notify_bot_update(user_id):
    """Notify bot to update Discord dashboard."""
    try:
        requests.post(
            'http://localhost:5001/webhook/update_dashboard',
            json={'user_id': user_id},
            timeout=2
        )
    except Exception as e:
        logger.error(f"Failed to notify bot: {e}")

# Update all API endpoints:
@app.route("/api/toggle_activity", methods=["POST"])
@require_auth
def api_toggle_activity():
    # ... existing code ...
    
    # Notify bot to update Discord dashboard
    notify_bot_update(user_id)
    
    return jsonify({...})
```

---

## 📝 Summary Checklist

### Phase 1: Prerequisites ✅
- [ ] Install Flask and dependencies
- [ ] Create Discord OAuth2 application
- [ ] Update `.env` with credentials
- [ ] Generate SECRET_KEY

### Phase 2: Backend ✅
- [ ] Create `web/config.py`
- [ ] Create `web/auth.py`
- [ ] Create `web/app.py`

### Phase 3: Frontend Templates ✅
- [ ] Create `web/templates/base.html`
- [ ] Create `web/templates/login.html`
- [ ] Create `web/templates/dashboard.html`

### Phase 4: Styling & JavaScript ✅
- [ ] Create `web/static/css/style.css`
- [ ] Create `web/static/js/dashboard.js`

### Phase 5: Integration ✅
- [ ] Modify `run.py`
- [ ] Create `web/__init__.py`

### Phase 6: Testing ✅
- [ ] Test local login flow
- [ ] Test activity completion
- [ ] Test balance management
- [ ] Test VIP toggle
- [ ] Test mobile responsiveness

### Phase 7: Deployment ✅
- [ ] Configure production URLs
- [ ] Setup reverse proxy or Cloudflare Tunnel
- [ ] Setup SSL certificate
- [ ] Test production deployment

### Phase 8: Bot Integration (Optional) ✅
- [ ] Add webhook server to bot
- [ ] Update web app to notify bot
- [ ] Test real-time Discord updates

---

## 🎉 Completion

After completing all phases, you'll have:
- ✅ Fully functional web dashboard
- ✅ Discord OAuth2 authentication
- ✅ Complete/uncomplete activities via web
- ✅ Balance management
- ✅ VIP status toggle
- ✅ Mobile-responsive design
- ✅ Real-time updates to Discord (optional)
- ✅ Production-ready deployment

---

## 🐛 Troubleshooting

### OAuth2 Issues
- **Error: "Redirect URI mismatch"**
  - Ensure redirect URI in `.env` matches Discord Developer Portal exactly
  - Include protocol (http:// or https://)

### Database Access
- **Error: "Database is locked"**
  - Ensure bot and web aren't using different database files
  - Check file permissions

### Port Conflicts
- **Error: "Port 5000 already in use"**
  - Change `WEB_PORT` in `.env`
  - Kill existing process: `lsof -i :5000` then `kill <PID>`

### Session Issues
- **User gets logged out frequently**
  - Ensure `SECRET_KEY` is set and persistent
  - Check `SESSION_TYPE` is set to "filesystem"

---

## 📚 Additional Resources

- [Flask Documentation](https://flask.palletsprojects.com/)
- [Discord OAuth2 Guide](https://discord.com/developers/docs/topics/oauth2)
- [Cloudflare Tunnel Docs](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/)

---

**Estimated Total Time:** 6-10 hours (depending on experience level)  
**Difficulty:** Intermediate  
**Cost:** $0 (can be hosted on same server as bot)

Good luck with your implementation! 🚀
