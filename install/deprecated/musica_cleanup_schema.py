#!/opt/Musica/venv/bin/python

"""
Musica Database Cleanup Utility (Python)
Replaces musica_cleanup_schema.csh
"""

import os
import sys
import shutil
import subprocess

# ------------------------------------------------------------
# Load Musica configuration
# ------------------------------------------------------------
def load_config():
    candidates = [
        os.path.join(os.getcwd(), "config", "musica.conf"),
        os.path.join(os.path.dirname(__file__), "..", "config", "musica.conf"),
    ]

    for cfg in candidates:
        if os.path.isfile(cfg):
            with open(cfg) as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        k, v = line.split("=", 1)
                        os.environ[k.strip()] = v.strip().strip('"')
            return cfg

    print("ERROR: musica.conf not found")
    sys.exit(1)


config_path = load_config()

# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------
def cmd_exists(cmd):
    return shutil.which(cmd) is not None


def run(cmd, *, input_text=None):
    result = subprocess.run(
        cmd,
        input=input_text,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result


# ------------------------------------------------------------
# Detect DB engine
# ------------------------------------------------------------
if cmd_exists("mariadb"):
    db_type = "mariadb"
elif cmd_exists("mysql"):
    db_type = "mysql"
elif cmd_exists("sqlite3"):
    db_type = "sqlite3"
else:
    print("No supported database engine found.")
    sys.exit(1)

print("\n🧹 Musica Database Cleanup Utility")
print("----------------------------------")
print(f"Detected database engine: {db_type}")
print(f"Config loaded from: {config_path}\n")

# ------------------------------------------------------------
# Confirmation
# ------------------------------------------------------------
ans = input("This will permanently remove the Musica database. Continue? (y/N): ")
if ans.lower() != "y":
    print("Cleanup aborted.")
    sys.exit(0)

# ------------------------------------------------------------
# Cleanup logic
# ------------------------------------------------------------
db_name = os.environ.get("MUSICA_DB_NAME", "Musica")
sqlite_db = os.environ.get("MUSICA_SQLITE_DB", "musica.db")

if db_type in ("mariadb", "mysql"):
    print(f"Dropping database '{db_name}' from {db_type}...")

    result = run(
        [db_type, "-u", "root", "-e", f"DROP DATABASE IF EXISTS {db_name};"]
    )

    if result.returncode != 0:
        print("ERROR: Failed to drop database")
        print(result.stderr)
        sys.exit(1)

elif db_type == "sqlite3":
    print(f"Removing SQLite database file: {sqlite_db}")

    if not os.path.isfile(sqlite_db):
        print("No SQLite database file found.")
    else:
        try:
            os.remove(sqlite_db)
        except OSError as e:
            print(f"ERROR: Failed to remove {sqlite_db}: {e}")
            sys.exit(1)

print("\nMusica database cleanup complete.")
sys.exit(0)

