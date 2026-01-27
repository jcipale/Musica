#!/usr/bin/env python3
"""
Musica DB Destroy Utility (Dangerous)
Removes entire Musica DB — use for testing only
"""

import shutil
import subprocess
import sys
from pathlib import Path

# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------
def cmd_exists(cmd: str) -> bool:
    return shutil.which(cmd) is not None


def run(cmd):
    return subprocess.run(cmd, check=False)


# ------------------------------------------------------------
# Safety confirmation
# ------------------------------------------------------------
print("WARNING: This will permanently delete the Musica database.")
confirm = input("Type 'DESTROY' to continue: ").strip()

if confirm != "DESTROY":
    print("Aborting.")
    sys.exit(0)

# ------------------------------------------------------------
# Detect database type
# ------------------------------------------------------------
db_type = ""

if cmd_exists("mariadb"):
    db_type = "mariadb"
elif cmd_exists("mysql"):
    db_type = "mysql"
elif cmd_exists("sqlite3"):
    db_type = "sqlite"

if not db_type:
    print("No supported database found.")
    sys.exit(1)

# ------------------------------------------------------------
# Destroy database
# ------------------------------------------------------------
if db_type == "mariadb":
    run(["sudo", "mariadb", "-e", "DROP DATABASE IF EXISTS Musica;"])

elif db_type == "mysql":
    run(["sudo", "mysql", "-e", "DROP DATABASE IF EXISTS Musica;"])

elif db_type == "sqlite":
    sqlite_db = Path("./Musica.sqlite3")
    if sqlite_db.exists():
        sqlite_db.unlink()

print("\nDatabase destroyed.")

