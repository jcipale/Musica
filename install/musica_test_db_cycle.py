#!/usr/bin/env python3
"""
Musica DB Test Cycle Utility
Version: 1.1

End-to-end database lifecycle validation:
  1) Create schema
  2) Verify schema
  3) Drop schema
  4) Verify removal
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


def run_capture(cmd):
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)


# ------------------------------------------------------------
# Intro
# ------------------------------------------------------------
print()
print("Musica DB Test Cycle Utility")
print("----------------------------------------")

# --- Script paths ---
create_script = Path("./Run_Create_Schema.csh")
drop_script   = Path("./Run_Drop_Schema.csh")

# --- Check scripts exist ---
if not create_script.exists():
    print(f"Error: Missing schema creation script: {create_script}")
    sys.exit(1)

if not drop_script.exists():
    print(f"Error: Missing schema drop script: {drop_script}")
    sys.exit(1)

# ------------------------------------------------------------
# Step 1: Create schema
# ------------------------------------------------------------
print()
print("Step 1: Creating schema...")
result = run([str(create_script)])

if result.returncode != 0:
    print("Schema creation failed. Exiting test.")
    sys.exit(1)

# ------------------------------------------------------------
# Step 2: Verify schema exists
# ------------------------------------------------------------
print()
print("Step 2: Verifying schema existence...")

if cmd_exists("mariadb"):
    res = run_capture(["sudo", "mariadb", "-e", "SHOW DATABASES LIKE 'musica';"])
    if b"musica" in res.stdout.lower():
        print("Schema 'musica' verified in MariaDB.")
    else:
        print("Schema 'musica' not found in MariaDB.")
        sys.exit(1)

elif cmd_exists("mysql"):
    res = run_capture(["sudo", "mysql", "-e", "SHOW DATABASES LIKE 'musica';"])
    if b"musica" in res.stdout.lower():
        print("Schema 'musica' verified in MySQL.")
    else:
        print("Schema 'musica' not found in MySQL.")
        sys.exit(1)

elif cmd_exists("sqlite3"):
    sqlite_db = Path("../data/musica.db")
    if sqlite_db.exists():
        print("SQLite database file verified.")
    else:
        print("SQLite database file missing.")
        sys.exit(1)

else:
    print("No supported database found for verification.")
    sys.exit(1)

# ------------------------------------------------------------
# Step 3: Drop schema
# ------------------------------------------------------------
print()
print("Step 3: Dropping schema...")
result = run([str(drop_script)])

if result.returncode != 0:
    print("Schema drop failed. Exiting test.")
    sys.exit(1)

# ------------------------------------------------------------
# Step 4: Verify removal
# ------------------------------------------------------------
print()
print("Step 4: Verifying schema removal...")

if cmd_exists("mariadb"):
    res = run_capture(["sudo", "mariadb", "-e", "SHOW DATABASES LIKE 'musica';"])
    if b"musica" in res.stdout.lower():
        print("Schema 'musica' still present — cleanup failed.")
        sys.exit(1)
    else:
        print("Schema successfully removed from MariaDB.")

elif cmd_exists("mysql"):
    res = run_capture(["sudo", "mysql", "-e", "SHOW DATABASES LIKE 'musica';"])
    if b"musica" in res.stdout.lower():
        print("Schema 'musica' still present — cleanup failed.")
        sys.exit(1)
    else:
        print("Schema successfully removed from MySQL.")

elif cmd_exists("sqlite3"):
    sqlite_db = Path("../data/musica.db")
    if sqlite_db.exists():
        print("SQLite DB file still exists — cleanup failed.")
        sys.exit(1)
    else:
        print("SQLite database file successfully removed.")

else:
    print("No supported database found for verification.")
    sys.exit(1)

# ------------------------------------------------------------
# Success
# ------------------------------------------------------------
print()
print("----------------------------------------")
print("Database lifecycle test completed successfully.")
sys.exit(0)

