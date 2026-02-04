#!/usr/bin/env python3

"""
Clean_Slate Protocol for Musica
--------------------------------
Completely wipes a selected Musica database and optionally
associated users, leaving all other databases intact.
"""

import subprocess
import sys
import getpass

def require_root():
    if not getpass.getuser() == "root":
        print("ERROR: This script should be run as root or with sudo.")
        sys.exit(1)

def prompt_database_name():
    while True:
        db_name = input("Enter the database to completely wipe: ").strip()
        if db_name:
            return db_name
        print("Database name cannot be empty.")

def confirm_action(db_name):
    print(f"\nWARNING: This will completely DESTROY database '{db_name}'!")
    resp = input("Are you ABSOLUTELY sure? [type 'YES' to proceed]: ").strip()
    if resp != "YES":
        print("Aborting clean-slate operation.")
        sys.exit(0)

def get_users_for_db(db_name):
    """
    Returns a list of MySQL users with privileges on the given DB.
    """
    try:
        result = subprocess.run(
            ["mysql", "-u", "root", "-e",
             f"SELECT DISTINCT user, host FROM mysql.db WHERE Db='{db_name}';"],
            capture_output=True,
            text=True,
            check=True
        )
        lines = result.stdout.strip().splitlines()
        # Skip header line
        users = [line.split() for line in lines[1:]]
        return users  # list of [user, host]
    except subprocess.CalledProcessError:
        print("ERROR: Unable to query users for database.")
        return []

def drop_database(db_name):
    try:
        subprocess.run(
            ["mysql", "-u", "root", "-e", f"DROP DATABASE IF EXISTS `{db_name}`;"],
            check=True
        )
        print(f"Database '{db_name}' dropped successfully.")
    except subprocess.CalledProcessError:
        print(f"ERROR: Failed to drop database '{db_name}'.")

def drop_users(users):
    for user, host in users:
        try:
            subprocess.run(
                ["mysql", "-u", "root", "-e",
                 f"DROP USER IF EXISTS '{user}'@'{host}';"],
                check=True
            )
            print(f"Dropped user '{user}'@'{host}'")
        except subprocess.CalledProcessError:
            print(f"ERROR: Failed to drop user '{user}'@'{host}'.")

def flush_privileges():
    try:
        subprocess.run(
            ["mysql", "-u", "root", "-e", "FLUSH PRIVILEGES;"],
            check=True
        )
        print("Privileges flushed successfully.")
    except subprocess.CalledProcessError:
        print("ERROR: Failed to flush privileges.")

def main():
    require_root()
    db_name = prompt_database_name()
    confirm_action(db_name)

    # --- Identify associated users ---
    users = get_users_for_db(db_name)
    if users:
        print("\nThe following users have privileges on this database:")
        for u, h in users:
            print(f"  - {u}@{h}")

        resp = input("\nDrop these users as well? [y/N]: ").strip().lower()
        if resp == "y":
            drop_users(users)
        else:
            print("Users retained.")

    # --- Drop the database ---
    drop_database(db_name)

    # --- Flush privileges ---
    flush_privileges()

    print("\nClean-slate operation completed successfully.")

if __name__ == "__main__":
    main()

