#!/usr/bin/env python3
"""
Life Admin System - Mac Menu Bar App

A native macOS menu bar application for managing the Life Admin System.
Provides quick access to server controls, job triggers, and status monitoring.
"""

import os
import sys
import signal
import subprocess
import webbrowser
import rumps
from pathlib import Path
from datetime import datetime

# Ensure we're in the project directory
PROJECT_DIR = Path(__file__).parent
os.chdir(PROJECT_DIR)

# Paths
VENV_PYTHON = PROJECT_DIR / ".venv" / "bin" / "python"
VENV_UVICORN = PROJECT_DIR / ".venv" / "bin" / "uvicorn"
LOG_DIR = PROJECT_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Server config
SERVER_HOST = "localhost"
SERVER_PORT = 8000
SERVER_URL = f"http://{SERVER_HOST}:{SERVER_PORT}"


class LifeAdminApp(rumps.App):
    def __init__(self):
        super(LifeAdminApp, self).__init__(
            "📁",  # Title shown in menu bar
            icon=None,  # No custom icon (will use title text)
            quit_button=None,  # Custom quit handler
        )

        self.server_process = None
        self.last_sync = None
        self.last_backup = None

        # Stats cache
        self.stats = {
            'total_items': 0,
            'items_needing_summaries': 0,
            'active_insights': 0,
        }

        # Build menu
        self.menu = [
            rumps.MenuItem("Server Status", callback=None),
            rumps.MenuItem("Total Documents: 0", callback=None),
            rumps.separator,
            rumps.MenuItem("Start Server", callback=self.start_server),
            rumps.MenuItem("Stop Server", callback=self.stop_server),
            rumps.MenuItem("Restart Server", callback=self.restart_server),
            rumps.separator,
            rumps.MenuItem("Sync Gmail Now", callback=self.sync_gmail),
            rumps.MenuItem("Generate All Summaries", callback=self.generate_all_summaries),
            rumps.MenuItem("Generate Insights", callback=self.generate_insights),
            rumps.MenuItem("Backup Database", callback=self.backup_database),
            rumps.separator,
            rumps.MenuItem("Open Dashboard", callback=self.open_dashboard),
            rumps.MenuItem("Open Vault", callback=self.open_vault),
            rumps.separator,
            rumps.MenuItem("View Logs", callback=self.view_logs),
            rumps.separator,
            rumps.MenuItem("Quit", callback=self.quit_app),
        ]

        # Update status on startup
        self.update_status()

        # Set up periodic status updates (every 30 seconds)
        self.status_timer = rumps.Timer(self.update_status, 30)
        self.status_timer.start()

    def update_status(self, _=None):
        """Update server status display."""
        is_running = self.check_server_running()

        if is_running:
            status = "🟢 Server Running"
            self.menu["Start Server"].set_callback(None)
            self.menu["Stop Server"].set_callback(self.stop_server)
            self.menu["Restart Server"].set_callback(self.restart_server)

            # Fetch stats when server is running
            self.fetch_stats()
        else:
            status = "🔴 Server Stopped"
            self.menu["Start Server"].set_callback(self.start_server)
            self.menu["Stop Server"].set_callback(None)
            self.menu["Restart Server"].set_callback(None)

        self.menu["Server Status"].title = status
        self.update_menu_titles()

    def fetch_stats(self):
        """Fetch statistics from the server."""
        try:
            import urllib.request
            import json

            # Get summary stats
            req = urllib.request.urlopen(f"{SERVER_URL}/summaries/stats", timeout=3)
            summary_stats = json.loads(req.read().decode())

            if summary_stats.get('ok'):
                self.stats['total_items'] = summary_stats.get('total_items', 0)
                self.stats['items_needing_summaries'] = summary_stats.get('items_needing_summaries', 0)

            # Get insights count
            req = urllib.request.urlopen(f"{SERVER_URL}/insights", timeout=3)
            insights_data = json.loads(req.read().decode())

            if insights_data.get('ok'):
                self.stats['active_insights'] = len(insights_data.get('insights', []))

        except Exception:
            # Silently fail if we can't fetch stats
            pass

    def update_menu_titles(self):
        """Update menu item titles with current stats."""
        # Update document count
        doc_count = self.stats['total_items']
        old_title = None
        for item in self.menu.values():
            if hasattr(item, 'title') and item.title.startswith('Total Documents:'):
                old_title = item.title
                break

        if old_title:
            self.menu[old_title].title = f"Total Documents: {doc_count}"

        # Update summaries count
        summary_count = self.stats['items_needing_summaries']
        old_title = None
        for item in self.menu.values():
            if hasattr(item, 'title') and 'Generate All Summaries' in item.title:
                old_title = item.title
                break

        if old_title:
            if summary_count > 0:
                new_title = f"Generate All Summaries ({summary_count})"
            else:
                new_title = "Generate All Summaries ✓"
            self.menu[old_title].title = new_title

        # Update insights count
        insight_count = self.stats['active_insights']
        old_title = None
        for item in self.menu.values():
            if hasattr(item, 'title') and 'Generate Insights' in item.title:
                old_title = item.title
                break

        if old_title:
            if insight_count > 0:
                new_title = f"Generate Insights ({insight_count} active)"
            else:
                new_title = "Generate Insights"
            self.menu[old_title].title = new_title

    def check_server_running(self):
        """Check if the server is responding."""
        try:
            import urllib.request
            urllib.request.urlopen(f"{SERVER_URL}/health", timeout=2)
            return True
        except:
            return False

    def start_server(self, _):
        """Start the web server."""
        if self.server_process and self.server_process.poll() is None:
            rumps.notification(
                "Life Admin System",
                "Server Already Running",
                "The server is already running"
            )
            return

        try:
            # Start server in background
            log_file = LOG_DIR / "server.log"
            with open(log_file, "a") as f:
                f.write(f"\n{'='*60}\n")
                f.write(f"Server started at {datetime.now()}\n")
                f.write(f"{'='*60}\n")

                self.server_process = subprocess.Popen(
                    [
                        str(VENV_UVICORN),
                        "app.main:app",
                        "--host", SERVER_HOST,
                        "--port", str(SERVER_PORT),
                    ],
                    stdout=f,
                    stderr=subprocess.STDOUT,
                    cwd=str(PROJECT_DIR),
                )

            # Wait a moment and check if it started
            import time
            time.sleep(2)

            if self.check_server_running():
                rumps.notification(
                    "Life Admin System",
                    "Server Started",
                    f"Server is running at {SERVER_URL}"
                )
                self.update_status()
            else:
                rumps.notification(
                    "Life Admin System",
                    "Server Failed to Start",
                    "Check logs for details"
                )
        except Exception as e:
            rumps.alert(
                "Failed to Start Server",
                f"Error: {e}\n\nCheck that you're in the project directory."
            )

    def stop_server(self, _):
        """Stop the web server."""
        if self.server_process and self.server_process.poll() is None:
            self.server_process.terminate()
            try:
                self.server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.server_process.kill()

            rumps.notification(
                "Life Admin System",
                "Server Stopped",
                "The web server has been stopped"
            )
            self.server_process = None
            self.update_status()
        else:
            rumps.notification(
                "Life Admin System",
                "Server Not Running",
                "The server is not currently running"
            )

    def restart_server(self, _):
        """Restart the web server."""
        rumps.notification(
            "Life Admin System",
            "Restarting Server",
            "Please wait..."
        )
        self.stop_server(None)
        import time
        time.sleep(1)
        self.start_server(None)

    def sync_gmail(self, _):
        """Run Gmail sync manually."""
        if not self.check_server_running():
            rumps.alert("Server Not Running", "Please start the server first.")
            return

        rumps.notification(
            "Life Admin System",
            "Gmail Sync Started",
            "Syncing emails from Gmail..."
        )

        try:
            result = subprocess.run(
                [str(VENV_PYTHON), "scripts/gmail_sync.py"],
                cwd=str(PROJECT_DIR),
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode == 0:
                # Parse output for summary
                lines = result.stdout.strip().split('\n')
                summary = lines[-1] if lines else "Sync completed"

                rumps.notification(
                    "Life Admin System",
                    "Gmail Sync Complete",
                    summary
                )
                self.last_sync = datetime.now()
                # Refresh stats immediately
                self.update_status()
            else:
                rumps.notification(
                    "Life Admin System",
                    "Gmail Sync Failed",
                    "Check logs for details"
                )
        except subprocess.TimeoutExpired:
            rumps.notification(
                "Life Admin System",
                "Gmail Sync Timeout",
                "Sync is taking longer than expected"
            )
        except Exception as e:
            rumps.alert("Gmail Sync Error", str(e))

    def generate_all_summaries(self, _):
        """Generate AI summaries for all items - opens web UI."""
        if not self.check_server_running():
            rumps.alert("Server Not Running", "Please start the server first.")
            return

        # Open vault with auto-open modal parameter
        webbrowser.open(f"{SERVER_URL}/?show_summaries=true")

    def generate_insights(self, _):
        """Generate insights manually - runs in background then opens dashboard."""
        if not self.check_server_running():
            rumps.alert("Server Not Running", "Please start the server first.")
            return

        # Update title to show processing
        self.title = "📁 ⏳"

        rumps.notification(
            "Life Admin System",
            "Generating Insights",
            "Analyzing documents..."
        )

        # Run in separate thread
        import threading

        def generate():
            try:
                result = subprocess.run(
                    [
                        str(VENV_PYTHON),
                        "-c",
                        "from app.insights import generate_all_insights; total = generate_all_insights(); print(f'Generated {total} insights')",
                    ],
                    cwd=str(PROJECT_DIR),
                    capture_output=True,
                    text=True,
                    timeout=30,
                )

                # Reset title
                self.title = "📁"

                if result.returncode == 0:
                    # Get the last line (summary)
                    lines = result.stdout.strip().split('\n')
                    summary = [l for l in lines if 'Generated' in l][-1] if lines else "Insights generated"

                    rumps.notification(
                        "Life Admin System",
                        "✓ Insights Generated",
                        summary
                    )
                    # Refresh stats immediately
                    self.update_status()

                    # Open dashboard to show insights
                    webbrowser.open(f"{SERVER_URL}/dashboard")
                else:
                    rumps.notification(
                        "Life Admin System",
                        "Insight Generation Failed",
                        "Check logs for details"
                    )
            except Exception as e:
                # Reset title
                self.title = "📁"
                rumps.notification(
                    "Life Admin System",
                    "Generation Error",
                    str(e)
                )

        thread = threading.Thread(target=generate)
        thread.daemon = True
        thread.start()

    def backup_database(self, _):
        """Run database backup manually."""
        rumps.notification(
            "Life Admin System",
            "Backup Started",
            "Creating database backup..."
        )

        try:
            result = subprocess.run(
                [str(VENV_PYTHON), "scripts/backup_db.py"],
                cwd=str(PROJECT_DIR),
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                rumps.notification(
                    "Life Admin System",
                    "Backup Complete",
                    "Database backed up to R2"
                )
                self.last_backup = datetime.now()
            else:
                rumps.notification(
                    "Life Admin System",
                    "Backup Failed",
                    "Check logs for details"
                )
        except Exception as e:
            rumps.alert("Backup Error", str(e))

    def open_dashboard(self, _):
        """Open dashboard in default browser."""
        if not self.check_server_running():
            rumps.alert("Server Not Running", "Please start the server first.")
            return

        webbrowser.open(f"{SERVER_URL}/dashboard")

    def open_vault(self, _):
        """Open vault in default browser."""
        if not self.check_server_running():
            rumps.alert("Server Not Running", "Please start the server first.")
            return

        webbrowser.open(SERVER_URL)

    def view_logs(self, _):
        """Open logs directory in Finder."""
        subprocess.run(["open", str(LOG_DIR)])

    def quit_app(self, _):
        """Quit the application."""
        # Stop server if running
        if self.server_process and self.server_process.poll() is None:
            response = rumps.alert(
                "Quit Life Admin System",
                "The server is currently running. Stop it before quitting?",
                ok="Stop and Quit",
                cancel="Cancel",
            )

            if response == 1:  # OK clicked
                self.stop_server(None)
            else:
                return  # Cancel quit

        rumps.quit_application()


if __name__ == "__main__":
    # Check we're running on macOS
    if sys.platform != "darwin":
        print("Error: This app is only for macOS")
        sys.exit(1)

    # Check virtual environment exists
    if not VENV_PYTHON.exists():
        print("Error: Virtual environment not found. Run: python3 -m venv .venv")
        sys.exit(1)

    # Create and run app
    app = LifeAdminApp()
    app.run()
