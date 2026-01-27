#!/usr/bin/env python3
"""
Musica Database Cleanup Utility
Compatible with: MariaDB, MySQL, SQLite
"""

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

print("")
print("Musica Database Cleanup Utility")
print("----------------------------------")

# --------------------------------------------------------------
# Detect OS
# --------------------------------------------------------------
os_type = platform.system()
print(f"Detected OS: {os_type}")

# --------------------------------------------------------------
# Step 1: Detect supported database
# --------------------------------------------------------------
def command_exists(cmd):
    return shutil.which(cmd) is not None

db_type = ""

# Match original logic as closely as possible
if command_exists("mariadb"):
    db_type = "mariadb"
elif command_exists("mysql"):
    db_type = "mysql"
elif command_exists("sqlite3"):
    db_type = "sqlite"

if not db_type:
    print("No supported database found (MariaDB/MySQL/SQLite).")
    sys.exit(1)

# --------------------------------------------------------------
# Step 2: Confirm user intent
# --------------------------------------------------------------
confirm = input(
    "Are you sure you want to DESTROY the Musica database? (y/N): "
).strip()

if confirm.lower() != "y":
    print("Aborted by user.")
    sys.exit(0)

# --------------------------------------------------------------
# Step 3: Execute cleanup
# --------------------------------------------------------------
exit_status = 0

try:
    if db_type in ("mariadb", "mysql"):
        print(f"Dropping Musica schema from {db_type}...")
        result = subprocess.run(
            ["sudo", db_type, "-u", "root", "-e", "DROP DATABASE IF EXISTS Musica;"],
            check=False
        )
        exit_status = result.returncode

    elif db_type == "sqlite":
        db_file = Path("Musica.db")
        print("Removing SQLite database file...")
        if db_file.exists():
            db_file.unlink()
            print("Musica.db deleted.")
            exit_status = 0
        else:
            print("Musica.db not found. Nothing to delete.")
            exit_status = 0

except Exception as e:
    print(f"Cleanup failed: {e}")
    sys.exit(1)

# --------------------------------------------------------------
# Step 4: Wrap up
# --------------------------------------------------------------
if exit_status == 0:
    print("Cleanup completed successfully.")
else:
    print(f"Cleanup encountered an error (exit code {exit_status}).")

sys.exit(exit_status)

