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
#   - Load install-time SQL artifacts (views, staging, triggers)
#   - Create ~/.my.cnf for Linux user
#
# ------------------------------------------------------------

from pathlib import Path
import subprocess
import getpass
import sys
import os
import pwd

# ------------------------------------------------------------
# Constants
# ------------------------------------------------------------
MUSICA_CONF = Path("/opt/Musica/config/musica.conf")

INSTALL_SQL = [
    "Audit_Recordings.sql",
    "Create_Schema.sql",
    "Create_Staging.sql",
    "v_recordings_display.sql",
]

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

    if "MUSICA_SQL_DIR" not in config:
        print("ERROR: Missing required config key: MUSICA_SQL_DIR")
        sys.exit(1)

    return config

# ------------------------------------------------------------
# MySQL helpers
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

    print(f"Loading schema: {schema_file.name}")

    try:
        subprocess.run(
            ["mysql", "-u", "root", db_name],
            stdin=schema_file.open("r"),
            check=True
        )
    except subprocess.CalledProcessError:
        print("ERROR: Failed to load schema.")
        sys.exit(1)

# ------------------------------------------------------------
# Install-time SQL loader
# ------------------------------------------------------------
def load_install_sql(db_name, sql_dir):
    for sql_file in INSTALL_SQL:
        sql_path = Path(sql_dir) / sql_file

        if not sql_path.is_file():
            print(f"ERROR: Missing install SQL file: {sql_path}")
            sys.exit(1)

        print(f"Loading install SQL: {sql_file}")

        try:
            subprocess.run(
                ["mysql", "-u", "root", db_name],
                stdin=sql_path.open("r"),
                check=True
            )
        except subprocess.CalledProcessError:
            print(f"ERROR: Failed loading {sql_file}")
            sys.exit(1)

# ------------------------------------------------------------
# .my.cnf Creator
# ------------------------------------------------------------
# Create ~/.my.cnf for invoking OS user
# ------------------------------------------------------------
def create_my_cnf(db_name, db_user, db_password):
    sudo_user = os.environ.get("SUDO_USER")

    if not sudo_user:
        print("ERROR: Cannot determine invoking user (run via sudo).")
        sys.exit(1)

    user_home = Path("/home") / sudo_user
    cnf_path = user_home / ".my.cnf"

    print(f"Creating MySQL client config: {cnf_path}")

    content = f"""[client]
user={db_user}
password={db_password}
host=localhost
database={db_name}
"""

    try:
        with cnf_path.open("w") as f:
            f.write(content)

        # Correct ownership
        import pwd
        user_info = pwd.getpwnam(sudo_user)
        os.chown(cnf_path, user_info.pw_uid, user_info.pw_gid)

        # Secure permissions
        os.chmod(cnf_path, 0o600)

    except Exception as e:
        print(f"ERROR: Failed to create .my.cnf: {e}")
        sys.exit(1)

    print(".my.cnf created successfully.")

# ------------------------------------------------------------
# Interactive provisioning
# ------------------------------------------------------------
def provision_database(config):
    print("")
    print("Musica Database Provisioning")
    print("-------------------------------------------------------------")

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

    resp = input("Create or update a database user? [y/N]: ").strip().lower()
    if resp != "y":
        return db_name, None, None, None

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
        print(f"User '{user}' already exists. Updating password.")
        mysql_exec(
            f"ALTER USER '{user}'@'localhost' IDENTIFIED BY '{password}';"
        )
    else:
        mysql_exec(
            f"CREATE USER '{user}'@'localhost' IDENTIFIED BY '{password}';"
        )

    print("")
    print("Select privilege level:")
    print("  1) DBA")
    print("  2) USER")
    print("  3) READ-ONLY")

    priv_map = {
        "1": "ALL PRIVILEGES",
        "2": "SELECT, INSERT, UPDATE, DELETE",
        "3": "SELECT"
    }

    while True:
        choice = input("Enter choice [1-3]: ").strip()
        if choice in priv_map:
            grant = priv_map[choice]
            break

    mysql_exec(f"REVOKE ALL PRIVILEGES, GRANT OPTION FROM '{user}'@'localhost';")
    mysql_exec(f"GRANT {grant} ON `{db_name}`.* TO '{user}'@'localhost';")
    mysql_exec("FLUSH PRIVILEGES;")

    print("")
    print("Provisioning complete.")
    print(f"Database   : {db_name}")
    print(f"User       : {user}")
    print(f"Privileges : {grant}")
    print("-------------------------------------------------------------")

    return db_name, user, password, grant

# ------------------------------------------------------------
# Main
# ------------------------------------------------------------
def main():
    require_root()
    require_venv()

    config = load_musica_config()

    db_name, user, password, priv = provision_database(config)

    load_install_sql(db_name, config["MUSICA_SQL_DIR"])

    if user:
        create_my_cnf(db_name, user, password)

    print("Database provisioned successfully.")

# ------------------------------------------------------------
if __name__ == "__main__":
    main()

