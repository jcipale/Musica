#!/usr/bin/env python3

import mariadb
import getpass
import sys
import os
from datetime import datetime

# -------------------------
# Configuration
# -------------------------

CONFIG_FILE = "/opt/Musica/config/musica.conf"

ADMIN_SQL = [
    "/opt/Musica/admin/Create_Staging.sql",
    "/opt/Musica/admin/v_recordings_display.sql"
]

REQUIRED_CONFIG_VARS = [
    "MUSICA_HOME",
    "DB_HOST"
]

# -------------------------
# Utility functions
# -------------------------

def fail(msg):
    print(f"\nERROR: {msg}")
    sys.exit(1)

def load_config(path):
    """
    Load shell-style KEY=VALUE pairs from musica.conf
    """
    if not os.path.isfile(path):
        fail(f"Configuration file not found: {path}")

    config = {}

    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            if "=" not in line:
                fail(f"Invalid config line: {line}")

            key, val = line.split("=", 1)
            config[key.strip()] = val.strip()

    for key in REQUIRED_CONFIG_VARS:
        if key not in config or not config[key]:
            fail(f"Required config variable missing: {key}")

    return config

def prompt(label, required=True):
    val = input(label).strip()
    if required and not val:
        fail("Required input missing.")
    return val

def connect_admin(user, password, host):
    try:
        return mariadb.connect(
            user=user,
            password=password,
            host=host,
            autocommit=True
        )
    except mariadb.Error as e:
        fail(f"Admin connection failed: {e}")

def run_sql_file(cursor, path):
    try:
        with open(path, "r") as f:
            sql = f.read()
        cursor.execute(sql)
    except FileNotFoundError:
        fail(f"SQL file not found: {path}")
    except mariadb.Error as e:
        fail(f"Failed executing {path}: {e}")

# -------------------------
# Main
# -------------------------

def main():
    print("\nMusica Database Initialization")
    print("------------------------------")

    # Load configuration
    config = load_config(CONFIG_FILE)
    musica_home = config["MUSICA_HOME"]
    db_host = config["DB_HOST"]

    print(f"Using configuration from: {CONFIG_FILE}")
    print(f"MUSICA_HOME = {musica_home}")
    print(f"DB_HOST     = {db_host}")

    admin_user = prompt("Admin DB user: ")
    admin_pass = getpass.getpass("Admin password: ")

    db_name = prompt("New database name: ")
    app_user = prompt("Application user name: ")
    app_pass = getpass.getpass("Application user password: ")

    print("\nSelect permission profile:")
    print("1) Read/Write (no schema changes)")
    print("2) Read-Only")

    role = prompt("Choice [1/2]: ")

    conn = connect_admin(admin_user, admin_pass, db_host)
    cur = conn.cursor()

    # Create database
    cur.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}`")
    print(f"Database `{db_name}` created.")

    # Create user
    cur.execute(
        f"CREATE USER IF NOT EXISTS '{app_user}'@'localhost' IDENTIFIED BY '{app_pass}'"
    )
    print(f"User `{app_user}` created.")

    # Grant permissions
    if role == "1":
        cur.execute(
            f"GRANT SELECT, INSERT, UPDATE, DELETE ON `{db_name}`.* TO '{app_user}'@'localhost'"
        )
        role_desc = "Read/Write"
    elif role == "2":
        cur.execute(
            f"GRANT SELECT ON `{db_name}`.* TO '{app_user}'@'localhost'"
        )
        role_desc = "Read-Only"
    else:
        fail("Invalid role selection.")

    print(f"Permissions granted: {role_desc}")

    # Switch database
    cur.execute(f"USE `{db_name}`")

    # Apply admin SQL
    for sql_file in ADMIN_SQL:
        run_sql_file(cur, sql_file)
        print(f"Applied: {sql_file}")

    ts = datetime.utcnow().strftime("%m-%d-%Y GMT %H:%M")

    print("\nInitialization Complete")
    print("-----------------------")
    print(f"Database: {db_name}")
    print(f"User: {app_user}")
    print("Schema objects: created")
    print(f"Timestamp: {ts}")

    conn.close()

if __name__ == "__main__":
    main()

