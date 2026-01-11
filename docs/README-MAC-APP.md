# Life Admin System - Mac Menu Bar App

A native macOS menu bar application for managing your Life Admin System.

## Features

- **Server Control**: Start, stop, and restart the web server
- **Quick Actions**:
  - Sync Gmail manually
  - Generate insights on demand
  - Backup database
- **Quick Access**:
  - Open dashboard in browser
  - Open vault in browser
  - View logs
- **Status Monitoring**: Real-time server status indicator
- **Notifications**: macOS native notifications for all actions

## Quick Start

### 1. Launch the App

**Option A: From Terminal**
```bash
cd /path/to/life-admin-system
./launch.sh
```

**Option B: Double-click**
- Right-click `launch.sh` in Finder
- Choose "Open With" → "Terminal"
- (First time only: Allow in System Preferences → Security & Privacy)

**Option C: Create a clickable app**
1. Open Automator
2. Create new "Application"
3. Add "Run Shell Script" action
4. Paste: `/path/to/life-admin-system/launch.sh`
5. Save as "Life Admin.app" to Applications folder
6. Now you can launch from Spotlight or Dock!

### 2. Using the Menu Bar App

Once running, you'll see a 📁 icon in your menu bar.

**Click it to see options with live indicators:**

#### Status (Auto-updates every 30 seconds)
- **Server Status** - Shows if server is running (🟢/🔴)
- **Total Documents: 125** - Count of all documents in vault
  - Updates after Gmail sync or uploads

#### Server Control
- **Start Server** - Launch the web server
- **Stop Server** - Stop the web server
- **Restart Server** - Restart the web server

#### Jobs (with smart indicators)
- **Sync Gmail Now** - Manually trigger Gmail ingestion
  - Updates document count after completion
- **Generate All Summaries (54)** - Opens web UI with batch modal
  - Shows how many need summaries in parentheses
  - Changes to "✓" when all summaries are generated
  - **Automatically opens browser** with progress UI
  - Updates menu indicators after completion
- **Generate Insights (3 active)** - Generate then show dashboard
  - Shows count of active insights
  - Runs in background with **📁 ⏳** indicator
  - **Automatically opens dashboard** when complete
  - Hidden if no insights exist
- **Backup Database** - Manually backup database to R2

#### Quick Access
- **Open Dashboard** - Opens http://localhost:8000/dashboard in browser
- **Open Vault** - Opens http://localhost:8000 in browser
- **View Logs** - Opens the logs directory in Finder

## Live Indicators

The menu bar app shows **real-time statistics** to help you see what needs attention:

- **📊 Total Documents** - Updates after sync or uploads
- **⚡ Summaries Needed** - Shows "(54)" if summaries are needed, "✓" when complete
- **💡 Active Insights** - Shows "(3 active)" if insights exist

**Auto-refresh**: Indicators update every 30 seconds automatically, or immediately after you run an action.

## Keyboard Shortcuts (in Web UI)

When using the web interface:

- `Cmd+K` - Focus search
- `Cmd+U` - Open upload modal
- `Cmd+D` - Go to dashboard
- `Cmd+H` - Go to home/vault
- `Esc` - Close modals

## UI Enhancements

The web interface now includes:

### Toast Notifications
- Success/error messages appear in top-right corner
- Auto-dismiss after 4 seconds
- Click to dismiss manually

### Loading States
- Buttons show spinner while processing
- Prevents accidental double-clicks
- Clear visual feedback

### Smooth Animations
- Slide-in toasts
- Fade-in empty states
- Smooth row expansion
- Progress bar on page loads

### Mobile Support
- Responsive sidebar
- Mobile-friendly menu button
- Touch-optimized interactions

## Auto-Start on Login (Optional)

To have the server start automatically when you log in:

### macOS Automator Method (Easiest)
1. Create "Life Admin.app" using Automator (see above)
2. Go to System Preferences → Users & Groups → Login Items
3. Click "+" and add "Life Admin.app"
4. Server will now start when you log in

### launchd Method (Advanced)
See `docs/50-deployment.md` for launchd configuration

## Troubleshooting

### Menu bar app won't start
- Make sure you're in the project directory
- Check virtual environment exists: `ls .venv/bin/python`
- Run directly: `.venv/bin/python life_admin_app.py`

### Server won't start from app
- Check logs: Click "View Logs" in menu
- Try starting manually: `.venv/bin/uvicorn app.main:app --port 8000`
- Check port not in use: `lsof -i :8000`

### Jobs fail when triggered
- Make sure server is running first (needed for some jobs)
- Check individual log files in `logs/` directory
- Run jobs manually to see error output

### Toast notifications don't appear
- Check browser console for errors (F12)
- Verify static files are loading: http://localhost:8000/static/js/enhancements.js

## Logs

All logs are stored in `logs/`:
- `server.log` - Web server output
- `gmail_sync.log` - Gmail ingestion
- `backup.log` - Database backups
- `insights.log` - Insight generation (when using cron)

Click "View Logs" in the menu bar app to open this directory.

## Notes

- The menu bar app keeps the server running in the background
- Server automatically stops when you quit the app
- You can still use cron jobs while the app is running
- The app runs on port 8000 by default (http://localhost:8000)
