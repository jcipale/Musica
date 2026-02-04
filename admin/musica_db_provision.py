#!/opt/Musica/venv/bin/python3
# ------------------------------------------------------------
# musica_db_provision.py
#
# Interactive database provisioning tool for Musica
#
# Responsibilities:
#   - Create database
#   - Load schema
#   - Create user
#   - Assign privileges
#
# Assumptions:
#   - Installer already ran
#   - MariaDB/MySQL already installed & running
#   - Musica venv already exists (PEP 668)
#   - musica.conf already exists
#
# This script is intentionally INTERACTIVE ONLY.
# ------------------------------------------------------------

from pathlib import Path
import subprocess
import getpass
import sys
import os

MUSICA_CONF = Path("/opt/Musica/config/musica.conf")

# ------------------------------------------------------------
# Safety checks
# ------------------------------------------------------------
def require_root():
    if os.geteuid() != 0:
        print("ERROR: This script must be run as root (sudo).")
        sys.exit(1)

def require_venv():
    expected_python = Path("/opt/Musica/venv/bin/python3")
    if Path(sys.executable) != expected_python:
        print("ERROR: This script MUST be run using the Musica venv.")
        print(f"Expected: {expected_python}")
        print(f"Running : {sys.executable}")
        sys.exit(1)

# ------------------------------------------------------------
# Config loader
# ------------------------------------------------------------
def load_musica_config():
    if not MUSICA_CONF.is_file():
        print(f"ERROR: Missing config file: {MUSICA_CONF}")
        sys.exit(1)

    config = {}
    with MUSICA_CONF.open() as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            k, v = line.split("=", 1)
            config[k.strip()] = v.strip()

    required = ["MUSICA_SQL_DIR"]
    for key in required:
        if key not in config:
            print(f"ERROR: Missing required config key: {key}")
            sys.exit(1)

    return config

# ------------------------------------------------------------
# DB helpers
# ------------------------------------------------------------
def mysql_exec(sql, database=None):
    cmd = ["mysql", "-u", "root"]
    if database:
        cmd.append(database)

    result = subprocess.run(
        cmd + ["-e", sql],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print("MySQL ERROR:")
        print(result.stderr.strip())
        sys.exit(1)

    return result.stdout

def database_exists(db_name):
    out = mysql_exec(f"SHOW DATABASES LIKE '{db_name}';")
    return db_name in out

def user_exists(user):
    out = mysql_exec(f"SELECT User FROM mysql.user WHERE User='{user}';")
    return user in out

# ------------------------------------------------------------
# Schema loader
# ------------------------------------------------------------
def load_schema(db_name, sql_dir):
    schema_file = Path(sql_dir) / "Create_Schema.sql"

    if not schema_file.is_file():
        print(f"ERROR: Schema file not found: {schema_file}")
        sys.exit(1)

    print(f"Loading schema from {schema_file}")

    try:
        subprocess.run(
            ["mysql", "-u", "root", db_name],
            stdin=schema_file.open("r"),
            check=True
        )
    except subprocess.CalledProcessError:
        print("ERROR: Failed to load schema.")
        sys.exit(1)

    print("Schema loaded successfully.")

# ------------------------------------------------------------
# Interactive provisioning
# ------------------------------------------------------------
def provision_database(config):
    print("")
    print("Musica Database Provisioning")
    print("-------------------------------------------------------------")

    # Database name
    while True:
        db_name = input("Enter database name to provision: ").strip()
        if db_name:
            break

    if database_exists(db_name):
        print(f"Database '{db_name}' already exists.")
        resp = input("Load schema anyway? [y/N]: ").strip().lower()
        if resp == "y":
            load_schema(db_name, config["MUSICA_SQL_DIR"])
    else:
        print(f"Creating database '{db_name}'")
        mysql_exec(f"CREATE DATABASE `{db_name}`;")
        load_schema(db_name, config["MUSICA_SQL_DIR"])

    # User creation
    resp = input("Create or update a database user? [y/N]: ").strip().lower()
    if resp != "y":
        return db_name, None, None

    while True:
        user = input("Enter username: ").strip()
        if user:
            break

    password = getpass.getpass("Enter password: ").strip()
    confirm = getpass.getpass("Confirm password: ").strip()

    if password != confirm or not password:
        print("ERROR: Passwords do not match.")
        sys.exit(1)

    if user_exists(user):
        print(f"User '{user}' already exists.")
        mysql_exec(f"ALTER USER '{user}'@'localhost' IDENTIFIED BY '{password}';")
    else:
        mysql_exec(
            f"CREATE USER '{user}'@'localhost' IDENTIFIED BY '{password}';"
        )

    # Privileges
    print("")
    print("Select privilege level:")
    print("  1) DBA")
    print("  2) USER")
    print("  3) READ-ONLY")

    priv_map = {
        "1": "DBA",
        "2": "USER",
        "3": "READ-ONLY"
    }

    while True:
        choice = input("Enter choice [1-3]: ").strip()
        if choice in priv_map:
            priv_level = priv_map[choice]
            break

    mysql_exec(f"REVOKE ALL PRIVILEGES, GRANT OPTION FROM '{user}'@'localhost';")

    if priv_level == "DBA":
        grant = "ALL PRIVILEGES"
    elif priv_level == "USER":
        grant = "SELECT, INSERT, UPDATE, DELETE"
    else:
        grant = "SELECT"

    mysql_exec(
        f"GRANT {grant} ON `{db_name}`.* TO '{user}'@'localhost';"
    )
    mysql_exec("FLUSH PRIVILEGES;")

    print("")
    print("Provisioning complete.")
    print(f"Database   : {db_name}")
    print(f"User       : {user}")
    print(f"Privileges : {priv_level}")
    print("-------------------------------------------------------------")

    return db_name, user, priv_level

# ------------------------------------------------------------
# Main
# ------------------------------------------------------------
def main():
    require_root()
    require_venv()

    config = load_musica_config()
    provision_database(config)

if __name__ == "__main__":
    main()

