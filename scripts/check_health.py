#!/usr/bin/env python3
"""
System health check script.
Can be run manually or via cron to monitor system health.
"""

import sys
import requests
from pathlib import Path
from datetime import datetime, timedelta

# Configuration
SERVER_URL = "http://localhost:8000"
LOG_DIR = Path(__file__).parent.parent / "logs"

# Log file age thresholds (in hours)
MAX_LOG_AGE = {
    "gmail_sync.log": 1,  # Should sync every 15 min
    "backup.log": 25,      # Daily at 3 AM
}


def check_web_server():
    """Check if web server is responding."""
    try:
        response = requests.get(f"{SERVER_URL}/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            print("✓ Web server: HEALTHY")
            print(f"  - Database: {'OK' if health_data['database']['healthy'] else 'ERROR'}")
            print(f"  - Items: {health_data['database']['items']}")
            print(f"  - R2 Storage: {'Configured' if health_data['storage']['configured'] else 'Not configured'}")
            print(f"  - AI: {'Enabled' if health_data['ai']['enabled'] else 'Disabled'}")
            return True
        else:
            print(f"✗ Web server: ERROR (HTTP {response.status_code})")
            return False
    except Exception as e:
        print(f"✗ Web server: UNREACHABLE ({e})")
        return False


def check_logs():
    """Check if log files are being updated recently."""
    print("\nLog freshness:")
    all_ok = True

    for log_file, max_age_hours in MAX_LOG_AGE.items():
        log_path = LOG_DIR / log_file

        if not log_path.exists():
            print(f"  ⚠ {log_file}: NOT FOUND")
            all_ok = False
            continue

        # Check last modified time
        mtime = datetime.fromtimestamp(log_path.stat().st_mtime)
        age = datetime.now() - mtime
        max_age = timedelta(hours=max_age_hours)

        if age > max_age:
            print(f"  ✗ {log_file}: STALE (last updated {age.total_seconds() / 3600:.1f}h ago)")
            all_ok = False
        else:
            print(f"  ✓ {log_file}: OK (updated {age.total_seconds() / 60:.0f}m ago)")

    return all_ok


def check_disk_space():
    """Check available disk space."""
    import shutil

    try:
        project_root = Path(__file__).parent.parent
        total, used, free = shutil.disk_usage(project_root)

        free_gb = free // (2**30)
        free_percent = (free / total) * 100

        print(f"\nDisk space:")
        if free_percent < 10:
            print(f"  ✗ LOW SPACE: {free_gb}GB free ({free_percent:.1f}%)")
            return False
        else:
            print(f"  ✓ {free_gb}GB free ({free_percent:.1f}%)")
            return True
    except Exception as e:
        print(f"  ⚠ Could not check disk space: {e}")
        return True  # Don't fail on this


def main():
    """Run all health checks."""
    print("=" * 60)
    print(f"Life Admin System - Health Check")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    checks = [
        ("Web Server", check_web_server),
        ("Log Files", check_logs),
        ("Disk Space", check_disk_space),
    ]

    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append(result)
        except Exception as e:
            print(f"\n✗ {name}: ERROR - {e}")
            results.append(False)

    print("\n" + "=" * 60)
    if all(results):
        print("✓ All checks passed")
        return 0
    else:
        print("✗ Some checks failed")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
