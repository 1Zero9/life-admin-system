# Deployment Guide - Life Admin System

## Overview

This system is designed to run 24/7 on a personal computer or home server. It consists of:
- **Web UI**: FastAPI server (port 8000)
- **Gmail Sync**: Automated script (runs every 15 minutes)
- **Database Backups**: Daily backups to R2

## Requirements

- Python 3.11+
- Always-on machine (Mac Mini, Raspberry Pi, NAS, or cloud VM)
- Internet connection
- Cloudflare R2 account (or S3-compatible storage)
- Google Gmail API credentials

## Initial Setup

### 1. Clone and Install

```bash
cd ~
git clone https://github.com/1Zero9/life-admin-system.git
cd life-admin-system

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and add your credentials:

```bash
# Cloudflare R2 (or S3-compatible storage)
R2_ENDPOINT=https://YOUR_ACCOUNT_ID.r2.cloudflarestorage.com
R2_ACCESS_KEY_ID=your_access_key
R2_SECRET_ACCESS_KEY=your_secret_key
R2_BUCKET=life-admin-documents
R2_PREFIX=documents

# Anthropic Claude API (optional - for AI summaries)
ANTHROPIC_API_KEY=sk-ant-api03-...
```

### 3. Set Up Gmail API

1. Go to https://console.cloud.google.com/
2. Create a new project (or use existing)
3. Enable Gmail API
4. Create OAuth 2.0 credentials (Desktop app)
5. Download `credentials.json` to project root
6. Run initial authentication:

```bash
.venv/bin/python scripts/gmail_ingest.py
```

This will open a browser for Gmail authorization. After authorizing, a `token.json` file will be created.

### 4. Create Gmail Label

In Gmail, create a label called **LifeAdmin** and apply it to emails you want to ingest. The system only processes emails with this label.

### 5. Initialize Database

```bash
.venv/bin/python -c "from app.db import Base, engine; Base.metadata.create_all(engine)"
```

## Running the System

### Option A: Development Mode (Testing)

```bash
# Terminal 1: Start web server
.venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Manual Gmail sync (test)
.venv/bin/python scripts/gmail_sync.py

# Terminal 3: Manual backup (test)
.venv/bin/python scripts/backup_db.py
```

Access UI at: http://localhost:8000

### Option B: Production Mode (24/7 Operation)

#### Start Web Server as Background Service

**Using systemd (Linux):**

Create `/etc/systemd/system/life-admin.service`:

```ini
[Unit]
Description=Life Admin System Web Server
After=network.target

[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/home/YOUR_USERNAME/life-admin-system
Environment="PATH=/home/YOUR_USERNAME/life-admin-system/.venv/bin"
ExecStart=/home/YOUR_USERNAME/life-admin-system/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable life-admin
sudo systemctl start life-admin
sudo systemctl status life-admin
```

**Using launchd (macOS):**

Create `~/Library/LaunchAgents/com.life-admin.webserver.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.life-admin.webserver</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/YOUR_USERNAME/life-admin-system/.venv/bin/uvicorn</string>
        <string>app.main:app</string>
        <string>--host</string>
        <string>0.0.0.0</string>
        <string>--port</string>
        <string>8000</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/Users/YOUR_USERNAME/life-admin-system</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/Users/YOUR_USERNAME/life-admin-system/logs/webserver.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/YOUR_USERNAME/life-admin-system/logs/webserver.err</string>
</dict>
</plist>
```

Load and start:

```bash
launchctl load ~/Library/LaunchAgents/com.life-admin.webserver.plist
launchctl start com.life-admin.webserver
```

#### Set Up Automated Tasks (cron)

Edit crontab:

```bash
crontab -e
```

Add these lines (update paths to match your installation):

```bash
# Gmail sync - every 15 minutes
*/15 * * * * cd /Users/YOUR_USERNAME/life-admin-system && .venv/bin/python scripts/gmail_sync.py >> logs/cron.log 2>&1

# Database backup - daily at 3 AM
0 3 * * * cd /Users/YOUR_USERNAME/life-admin-system && .venv/bin/python scripts/backup_db.py >> logs/cron.log 2>&1
```

Verify cron jobs:

```bash
crontab -l
```

## Monitoring

### Check Logs

```bash
# Web server logs (if using systemd/launchd)
tail -f logs/webserver.log

# Gmail sync logs
tail -f logs/gmail_sync.log

# Backup logs
tail -f logs/backup.log

# Cron logs
tail -f logs/cron.log
```

### Verify System is Running

```bash
# Check web server is responding
curl http://localhost:8000/health

# Check recent Gmail syncs
tail -20 logs/gmail_sync.log | grep "Sync complete"

# Check recent backups
tail -20 logs/backup.log | grep "Backup complete"
```

### Common Issues

**Gmail sync not working:**
- Check `token.json` exists and is valid
- Check Gmail API quota (15,000 requests/day)
- Verify LifeAdmin label exists
- Check logs: `tail -50 logs/gmail_sync.log`

**Web UI not accessible:**
- Check server is running: `curl http://localhost:8000/health`
- Check port 8000 is not in use: `lsof -i :8000`
- Check firewall allows port 8000

**Backups failing:**
- Verify R2 credentials in `.env`
- Check R2 bucket exists
- Check logs: `tail -50 logs/backup.log`

## Upgrading

```bash
cd ~/life-admin-system
git pull
source .venv/bin/activate
pip install -r requirements.txt

# Restart services
sudo systemctl restart life-admin  # Linux
# OR
launchctl stop com.life-admin.webserver && launchctl start com.life-admin.webserver  # macOS
```

## Security Notes

- **Local network only**: By default, the system listens on `0.0.0.0:8000`. This is accessible from your local network only.
- **No authentication**: The system has no login. Do not expose to the internet without adding authentication.
- **Credentials**: `.env`, `credentials.json`, and `token.json` contain sensitive data. Keep them secure.
- **Backups**: Database backups in R2 contain all your documents. Secure your R2 account.

## Performance

- **Database size**: SQLite handles millions of rows. No issues for household use.
- **Storage**: Documents stored in R2. No local storage limits.
- **Memory**: FastAPI server uses ~100MB RAM.
- **CPU**: Minimal. Spikes during OCR operations only.

## Backup & Recovery

### Manual Backup

```bash
# Create backup now
.venv/bin/python scripts/backup_db.py
```

### Restore from Backup

```bash
# Download backup from R2 (via web UI or aws-cli)
# Then:
cp path/to/backup.sqlite3 data/life_admin.sqlite3

# Restart server
sudo systemctl restart life-admin
```

### Disaster Recovery

All documents are in R2 (immutable). Database can be rebuilt from R2 objects if needed. SQLite backup files are also in R2 under `backups/` prefix.

## Network Access

To access from other devices on your network:

1. Find your machine's IP: `hostname -I` (Linux) or `ifconfig` (macOS)
2. Access from another device: `http://YOUR_IP:8000`

**Example**: If your server IP is `192.168.1.100`:
- Access from phone/tablet: `http://192.168.1.100:8000`
- Bookmark for easy access

## Next Steps

- Test Gmail sync: Apply LifeAdmin label to an email
- Wait 15 minutes (or run manual sync)
- Check web UI for new document
- Generate AI summary
- Test backup: Check R2 bucket after 3 AM

## Support

Logs are your friend:
- `logs/gmail_sync.log` - Gmail ingestion
- `logs/backup.log` - Database backups
- `logs/cron.log` - Cron job execution
- `logs/webserver.log` - Web server (if configured)

For issues, check logs first. Most problems are:
1. Missing/expired credentials
2. Wrong paths in cron/systemd config
3. Port conflicts
