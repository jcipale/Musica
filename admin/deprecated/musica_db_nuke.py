#!/opt/Musica/venv/bin/python

"""
musica_db_nuke.py

!!! DANGER !!!
Completely destroys the Musica database AND database user.
"""

import os
import subprocess
import sys
from pathlib import Path

# -----------------------------
# Helpers
# -----------------------------

def run(cmd, capture=False):
    return subprocess.run(
        cmd,
        shell=True,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
    )


# -----------------------------
# Load config (same contract)
# -----------------------------

if "MUSICA_DB_NAME" not in os.environ:
    conf = Path(__file__).resolve().parent.parent / "config" / "musica.conf"
    if conf.exists():
        cmd = f"set -a && . '{conf}' && env"
        res = run(cmd, capture=True)
        for line in res.stdout.splitlines():
            if "=" in line:
                k, v = line.split("=", 1)
                os.environ[k] = v
    else:
        print("ERROR: musica.conf not found")
        sys.exit(1)

MUSICA_DB_NAME = os.environ["MUSICA_DB_NAME"]
MUSICA_DB_USER = os.environ["MUSICA_DB_USER"]
MUSICA_DB_HOST = os.environ.get("MUSICA_DB_HOST", "localhost")

# -----------------------------
# Nuclear warning
# -----------------------------

print("==================================================")
print("!!! DANGER: MUSICA DATABASE NUCLEAR RESET !!!")
print("")
print("This will PERMANENTLY DESTROY:")
print(f"  - Database: {MUSICA_DB_NAME}")
print(f"  - User:     {MUSICA_DB_USER}@{MUSICA_DB_HOST}")
print("")
print("This action CANNOT be undone.")
print("==================================================")
confirm = input("Type NUKE to continue: ").strip()

if confirm != "NUKE":
    print("Aborted.")
    sys.exit(1)

# -----------------------------
# Drop user
# -----------------------------

print(f"Dropping user '{MUSICA_DB_USER}'@'{MUSICA_DB_HOST}'...")

run(
    f"sudo mariadb -e "
    f"\"DROP USER IF EXISTS '{MUSICA_DB_USER}'@'{MUSICA_DB_HOST}';\""
)

# Verify user removal
res = run(
    "sudo mariadb -N -B -e "
    f"\"SELECT COUNT(*) FROM mysql.user "
    f"WHERE User='{MUSICA_DB_USER}' AND Host='{MUSICA_DB_HOST}';\"",
    capture=True,
)

user_count = res.stdout.strip()

if user_count != "0":
    print(f"ERROR: User '{MUSICA_DB_USER}@{MUSICA_DB_HOST}' still exists")
    sys.exit(1)

print("User successfully removed.")

run("sudo mariadb -e \"FLUSH PRIVILEGES;\"")

# -----------------------------
# Drop database
# -----------------------------

print("Dropping database...")

run(
    f"sudo mariadb -e "
    f"\"DROP DATABASE IF EXISTS {MUSICA_DB_NAME};\""
)

res = run(
    "sudo mariadb -N -B -e "
    f"\"SELECT COUNT(*) FROM information_schema.SCHEMATA "
    f"WHERE SCHEMA_NAME='{MUSICA_DB_NAME}';\"",
    capture=True,
)

db_count = res.stdout.strip()

if db_count != "0":
    print(f"ERROR: Database '{MUSICA_DB_NAME}' still exists")
    sys.exit(1)

print("Database successfully removed.")
sys.exit(0)

