#!/opt/Musica/venv/bin/python

"""
Clean_Slate Protocol for Musica
--------------------------------
Completely wipes a selected Musica database and optionally
associated users, leaving all other databases intact.

This script intentionally replaces any DROP DATABASE SQL.
Destructive operations must be interactive and explicit.

"""

import subprocess
import sys
import os
from pathlib import Path

# ------------------------------------------------------------
# Safety
# ------------------------------------------------------------
def require_root():
    if os.geteuid() != 0:
        print("ERROR: This script must be run as root (sudo).")
        sys.exit(1)

def enforce_venv():
    expected = Path("/opt/Musica/venv/bin/python")
    if Path(sys.executable) != expected:
        print("ERROR: This script must be run using the Musica venv.")
        sys.exit(1)

# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------
def prompt_database_name():
    while True:
        db_name = input("Enter the database to completely wipe: ").strip()
        if db_name:
            return db_name
        print("Database name cannot be empty.")

def confirm_action(db_name):
    print(f"\nWARNING: This will completely DESTROY database '{db_name}'!")
    resp = input("Type 'YES' to proceed: ").strip()
    if resp != "YES":
        print("Aborting clean-slate operation.")
        sys.exit(0)

def mysql_exec(sql):
    result = subprocess.run(
        ["mysql", "-u", "root", "-e", sql],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        print("MySQL ERROR:")
        print(result.stderr.strip())
        sys.exit(1)
    return result.stdout

def get_users_for_db(db_name):
    out = mysql_exec(
        f"SELECT DISTINCT User, Host FROM mysql.db WHERE Db='{db_name}';"
    )
    users = []
    for line in out.splitlines()[1:]:
        user, host = line.split()
        users.append((user, host))
    return users

# ------------------------------------------------------------
# Destruction
# ------------------------------------------------------------
def drop_users(users):
    for user, host in users:
        mysql_exec(f"DROP USER IF EXISTS '{user}'@'{host}';")
        print(f"Dropped user '{user}'@'{host}'")

def drop_database(db_name):
    mysql_exec(f"DROP DATABASE IF EXISTS `{db_name}`;")
    print(f"Database '{db_name}' dropped.")

# ------------------------------------------------------------
# Main
# ------------------------------------------------------------
def main():
    require_root()
    enforce_venv()

    db_name = prompt_database_name()
    confirm_action(db_name)

    users = get_users_for_db(db_name)
    if users:
        print("\nUsers with privileges on this DB:")
        for u, h in users:
            print(f"  - {u}@{h}")

        resp = input("\nDrop these users as well? [y/N]: ").strip().lower()
        if resp == "y":
            drop_users(users)
        else:
            print("Users retained.")

    drop_database(db_name)
    mysql_exec("FLUSH PRIVILEGES;")

    print("\nClean-slate operation completed successfully.")

if __name__ == "__main__":
    main()

