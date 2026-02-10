# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Bonus Points Web Dashboard — a Flask web app for tracking daily bonus points activities with Discord OAuth2 authentication. The UI is in Russian. There is no Discord bot; this is web-only.

## Commands

```bash
# Setup
python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # Linux/Mac
pip install -r requirements.txt
cp .env.example .env           # Then fill in Discord OAuth2 credentials + SECRET_KEY

# Run (dev)
python run.py                  # Starts Flask on http://localhost:5000

# Run (production)
gunicorn -w 4 -b 0.0.0.0:5000 web.app:app

# Docker
docker-compose up --build

# Tests
pip install -r requirements-dev.txt
pytest

# Lint
ruff check web/
```

## Architecture

**Entry point:** `run.py` → sets up logging (with rotation), then calls `web.app.run_web()`

**Backend (Python/Flask):**
- `web/app.py` — Flask app factory, registers blueprints, DB init, teardown (~60 lines)
- `web/routes/pages.py` — Page routes: `/`, `/login`, `/callback`, `/logout`, `/dashboard`, `/settings`
- `web/routes/api.py` — API routes: all `/api/*` JSON endpoints (toggle, repeatable, balance, VIP, event, hide/unhide, reset, stats)
- `web/middleware.py` — Request logging (before/after), session refresh
- `web/validation.py` — Input validators (`validate_activity_id`, `validate_boolean`, `validate_integer`), API response helpers (`api_success`, `api_error`)
- `web/auth.py` — Discord OAuth2 flow (`get_oauth_url`, `exchange_code`, `get_user_info`, `require_auth` decorator)
- `web/config.py` — `WebConfig` class reads from `.env` via python-dotenv; validates required vars on import
- `web/database.py` — `Database` class wrapping SQLite with thread-local connections, WAL mode, atomic BP operations, repeatable completions, activity reset
- `web/helpers.py` — Rate limiting (in-memory sliding window), BP calculation, dashboard/settings data preparation (including repeatable + timestamp flow)
- `web/activities.py` — Activity definitions list (`ACTIVITIES`) with cached O(1) lookup by ID, `is_repeatable()` helper

**Frontend (vanilla JS + Jinja2 templates):**
- `web/templates/base.html` — Base layout (navbar, footer, loads `common.js`)
- `web/templates/dashboard.html` — Main activity dashboard (compact control panel + tabs, repeatable +/- cards, timestamps, help tooltips)
- `web/templates/settings.html` — Settings page (VIP, events, balance, hidden activities, activity reset)
- `web/static/js/common.js` — Shared utilities (`getCsrfToken`, `showLoading`, `hideLoading`, `showToast`, `isLoading`)
- `web/static/js/dashboard.js` — Dashboard logic (toggle, search, filter, tabs, timestamps, repeatable activity controls)
- `web/static/js/settings.js` — Settings page logic (VIP/event toggle, balance, hide/unhide, reset today's activities)
- `web/static/css/style.css` — All styles, CSS variables for theming, mobile-first responsive

**Tests (22 total):**
- `tests/conftest.py` — Fixtures: temp DB, Flask test client, authenticated session
- `tests/test_database.py` — Database operation tests (atomicity, floor, idempotency, timestamps, repeatable completions, reset)
- `tests/test_api.py` — API endpoint tests (auth, validation, rate limiting, timestamps, repeatable activity, reset)

**Data:** SQLite DB at `data/bonus_points.db` (gitignored). Tables: `users`, `activities`, `hidden_activities`, `settings`, `repeatable_completions`.

## Key Design Decisions

- **BP snapshot on completion:** When an activity is completed, `bp_earned` is stored in the DB. Unchecking uses the stored value, not a recalculation.
- **Atomic BP operations:** `add_user_bp()` and `subtract_user_bp()` use single SQL statements (`bp_balance + ?` / `MAX(bp_balance - ?, 0)`) to prevent race conditions.
- **Per-user events:** The x2 BP event flag is per-user (`users.event_active`), not a global setting.
- **Daily reset:** Activities reset at 07:00 Moscow Time (04:00 UTC). Date boundary is calculated in `database.get_today_date()`.
- **Rate limiting:** Decorator-based, in-memory sliding window keyed by Discord user ID. Cleans up empty entries to prevent memory leaks.
- **Thread-local DB connections:** Each Flask worker thread gets its own SQLite connection via `threading.local()`, closed at request teardown.
- **Blueprint structure:** Page routes (`pages_bp`) and API routes (`api_bp` with `/api` prefix) are separated into blueprints. Templates use `url_for('pages.dashboard')` etc.
- **Repeatable activities:** Activities with `"repeatable": True` use a separate `repeatable_completions` table (not the UNIQUE-constrained `activities` table). They show +/- counter UI, always stay in the "active" tab, and don't count toward completion progress — only their earned BP adds to the total.
- **Activity help tooltips:** Optional `description` field on activity definitions, rendered as a `?` icon with `title` attribute on dashboard and settings pages.
- **Completion timestamps:** `completed_at` (UTC ISO) flows from DB → helpers → template → JS, which converts to local time "в HH:MM" display.
- **Activity reset:** Per-user self-reset on settings page clears all completions (regular + repeatable) for today WITHOUT modifying BP balance.

## API Response Format

All `/api/*` endpoints return JSON:
```json
{"success": true, "balance": 100, "message": "..."}
```
Errors: `{"success": false, "error": "..."}` with appropriate HTTP status.

## Adding Activities

Edit `web/activities.py` — append to the `ACTIVITIES` list:
```python
{"id": "unique_id", "name": "🎯 Display Name", "bp": 2, "type": "solo", "time": "low",
 "description": "Optional tooltip text", "repeatable": False}
```
Fields:
- `id` (alphanumeric + underscore, max 50) — unique identifier
- `name` — display name with emoji prefix
- `bp` (int) — base reward
- `type` ("solo" / "pair") — activity type filter
- `time` ("low" / "medium" / "high") — time investment filter
- `description` (optional str) — shown as `?` tooltip on hover
- `repeatable` (optional bool) — if `True`, uses +/- counter UI and separate DB table

## Git Workflow

- Never commit directly to main — always create a branch with the appropriate prefix
- Always `git pull origin main` before starting a new feature branch and after merging a PR
- Use full branch prefixes: `feature/`, `bugfix/`, `docs/`, `cleanup/` (never abbreviated like `feat/` or `fix/`)
