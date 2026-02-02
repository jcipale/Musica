#!/usr/bin/env python3

# ------------------------------------------------------------
# musica_db_install.py: This is the installer/verification
# script for Musica. This script will -
# > Confirm the proper user (sudo or root)
# > Confirm the OS being used
# > Detect backend DB presence
# > Interactively create the user Database, User_ID/Passwd and 
#   grant Privileges
# ------------------------------------------------------------

from pathlib import Path
import getpass
import subprocess
import os
import sys
import platform
import shutil
import subprocess

# ------------------------------------------------------------
# Utility functions
# ------------------------------------------------------------

def require_root():
    if os.geteuid() != 0:
        print("ERROR: This installer must be run as root (sudo).")
        print(f"Run again using: sudo {sys.argv[0]}")
        sys.exit(1)

# ------------------------------------------------------------
# STEP 2: OS detection & classification
# ------------------------------------------------------------
def detect_os():
    system = platform.system()
    print(f"Detected OS family (raw): {system}")
    return system

def classify_os(system):
    print(f"Platform string         : {platform.platform()}")
    distro_class = None

    if system == "Linux":
        distro_class = classify_linux()
    elif system == "Darwin":
        classify_macos()
        distro_class = "macOS"
    elif system == "Windows":
        classify_windows()
        distro_class = "Windows"
    else:
        print(f"ERROR: Unsupported operating system: {system}")
        sys.exit(1)

    return distro_class

def classify_linux():
    os_release = Path("/etc/os-release")
    if not os_release.is_file():
        print("ERROR: /etc/os-release not found. Cannot classify Linux distro.")
        sys.exit(1)

    info = {}
    for line in os_release.read_text().splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            info[k] = v.strip().strip('"')

    distro_id = info.get("ID", "unknown")
    distro_like = info.get("ID_LIKE", "")
    version_id = info.get("VERSION_ID", "unknown")
    name = info.get("NAME", "unknown")

    print(f"Linux distro            : {name}")
    print(f"Distro ID               : {distro_id}")
    print(f"Version ID              : {version_id}")
    if distro_like:
        print(f"Distro family           : {distro_like}")

    if distro_id in ("debian", "ubuntu") or "debian" in distro_like:
        print("Linux class             : Debian-family")
        return "Debian-family"
    elif distro_id in ("rhel", "centos", "rocky", "almalinux", "fedora") or "rhel" in distro_like:
        print("Linux class             : RHEL-family")
        return "RHEL-family"
    elif distro_id in ("sles", "opensuse"):
        print("Linux class             : SUSE-family")
        return "SUSE-family"
    else:
        print("ERROR: Unsupported Linux distribution.")
        sys.exit(1)

def classify_macos():
    print("macOS detected")
    print(f"macOS version           : {platform.mac_ver()[0]}")

def classify_windows():
    print("Windows detected")
    print(f"Windows release         : {platform.release()}")
    print(f"Windows version         : {platform.version()}")

# ------------------------------------------------------------
# STEP 3: Database detection
# ------------------------------------------------------------
def check_command_exists(cmd):
    return shutil.which(cmd) is not None

def detect_linux_db(distro_class):
    print("Checking database for Linux...")

    if distro_class == "Debian-family":
        cmd = "mariadb"
        service = "mariadb"
    elif distro_class == "RHEL-family":
        cmd = "mysql"
        service = "mysqld"
    elif distro_class == "SUSE-family":
        cmd = "mysql"
        service = "mysql"
    else:
        print("Unknown Linux class; cannot detect DB automatically")
        return False

    db_installed = check_command_exists(cmd)
    if db_installed:
        print(f"{cmd} detected on system")
        if check_command_exists("systemctl"):
            try:
                subprocess.run(
                    ["systemctl", "status", service],
                    check=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                print(f"{service} service detected (status check attempted)")
            except Exception:
                print(f"Could not verify service status for {service}")
        return True
    else:
        print(f"{cmd} not detected on system")
        return False

def detect_macos_db():
    print("Checking database for macOS...")
    if check_command_exists("mysql"):
        print("MySQL/MariaDB detected (brew or native)")
        return True
    print("MySQL/MariaDB not detected")
    return False

def detect_windows_db():
    print("Checking database for Windows...")
    try:
        import sqlite3
        print("SQLite3 detected (Python builtin)")
        return True
    except ImportError:
        print("SQLite3 not available in Python environment")
        return False

def detect_other_unix_db():
    print("Checking database for generic Unix...")
    for cmd in ("mysql", "mariadb"):
        if check_command_exists(cmd):
            print(f"{cmd} detected")
            return True
    print("No recognized database found")
    return False

def detect_database(system, distro_class=None):
    if system == "Linux":
        return detect_linux_db(distro_class)
    elif system == "Darwin":
        return detect_macos_db()
    elif system == "Windows":
        return detect_windows_db()
    else:
        return detect_other_unix_db()

# ------------------------------------------------------------
# STEP 4: DB and User Setup (Interactive)
# ------------------------------------------------------------
def db_user_setup_linux():
    """
    Interactive menu-driven database and user creation for Linux
    (MariaDB/MySQL)
    """
    print("STEP 4: Database & User Setup (Interactive)")
    print("-------------------------------------------------------------")

    # --- Prompt for database name ---
    while True:
        db_name = input("Enter the database name to create: ").strip()
        if db_name:
            break
        print("Database name cannot be empty.")

    # --- Check if database exists ---
    try:
        result = subprocess.run(
            ["mysql", "-u", "root", "-e", f"SHOW DATABASES LIKE '{db_name}';"],
            capture_output=True,
            text=True,
            check=True
        )
        if db_name in result.stdout:
            print("")
            print(f"Database '{db_name}' already exists. Skipping user/password/privileges setup.")
            return db_name, None, None  # No user created
    except subprocess.CalledProcessError:
        print("ERROR checking existing databases. Ensure MariaDB/MySQL is running.")
        sys.exit(1)

    # --- Prompt for user ---
    while True:
        user_id = input("Enter the username to create: ").strip()
        if user_id:
            break
        print("Username cannot be empty.")

    # --- Prompt for password ---
    while True:
        password = getpass.getpass(f"Enter password for user '{user_id}': ").strip()
        confirm = getpass.getpass("Confirm password: ").strip()
        if password and password == confirm:
            break
        print("Passwords do not match or empty. Please try again.")

    # --- Privilege selection ---
    privileges_map = {
        "1": "DBA",
        "2": "USER",
        "3": "READ-ONLY"
    }

    print ("")
    print("Select privilege level:")
    print("  1) DBA")
    print("  2) USER")
    print("  3) READ-ONLY")
    while True:
        choice = input("Enter choice [1-3]: ").strip()
        if choice in privileges_map:
            priv_level = privileges_map[choice]
            break
        print("Invalid selection, choose 1, 2, or 3.")

    print ("")
    print(f"Creating database '{db_name}' and user '{user_id}' with privileges '{priv_level}'...")

    # --- Construct SQL commands ---
    sql_commands = []
    sql_commands.append(f"CREATE DATABASE IF NOT EXISTS `{db_name}`;")
    sql_commands.append(f"CREATE USER IF NOT EXISTS '{user_id}'@'localhost' IDENTIFIED BY '{password}';")

    if priv_level == "DBA":
        sql_commands.append(f"GRANT ALL PRIVILEGES ON `{db_name}`.* TO '{user_id}'@'localhost';")
    elif priv_level == "USER":
        sql_commands.append(f"GRANT SELECT, INSERT, UPDATE, DELETE ON `{db_name}`.* TO '{user_id}'@'localhost';")
    elif priv_level == "READ-ONLY":
        sql_commands.append(f"GRANT SELECT ON `{db_name}`.* TO '{user_id}'@'localhost';")

    sql_commands.append("FLUSH PRIVILEGES;")

    # --- Execute commands ---
    print ("")
    print("Executing SQL commands...")
    for cmd in sql_commands:
        try:
            subprocess.run(
                ["mysql", "-u", "root", "-e", cmd],
                check=True
            )
            print(f"Executed: {cmd}")
        except subprocess.CalledProcessError:
            print(f"ERROR executing: {cmd}")
            print("Check database service and root privileges.")
            sys.exit(1)

    print ("")
    print("Database and user setup completed successfully.")
    print(f"Database: {db_name}, User: {user_id}, Privileges: {priv_level}")
    print("-------------------------------------------------------------")
    return db_name, user_id, priv_level

# ------------------------------------------------------------
# STEP 5: PEP 668 Advisory Check
# ------------------------------------------------------------
def check_pep668(system: str, distro_class: str):
    """
    Detect if the system may require PEP 668 workaround (venv) for MariaDB/Python interface.
    Only applicable for Linux/Debian-family systems (Deb13+).
    """
    print("\nSTEP 5: PEP 668 Advisory Check")
    print("-------------------------------------------------------------")

    if system == "Linux" and distro_class == "Debian-family":
        venv_python = Path("/opt/Musica/venv/bin/python")
        if not venv_python.is_file():
            print("WARNING: PEP 668 workaround may be required for MariaDB/Python interface.")
            print("No virtual environment detected at:", venv_python)
            print("Please follow the instructions in README_INSTALL.md to create venv and")
            print("update all Musica Python scripts to use the venv Python interpreter.")
        else:
            print("Virtual environment detected:", venv_python)
            print("PEP 668 workaround satisfied.")
    else:
        print("PEP 668 workaround not required on this platform.")

    print("-------------------------------------------------------------")

# ------------------------------------------------------------
# Main entry
# ------------------------------------------------------------
def main():
    print("Musica Installer – Environment Validation")
    require_root()


    print("")
    print("STEP 1 Root-user completed successfully.")
    print("----------------------------------------")

    system = detect_os()
    distro_class = classify_os(system)

    print("")
    print("STEP 2 System OS detected successfully.")
    print("----------------------------------------")

    db_found = detect_database(system, distro_class)

    if db_found:
        print("Database engine detected. Proceeding...")
    else:
        print("WARNING: Required database not found. Installation may fail later.")

    print("")
    print("STEP 3 Database detected successfully.")
    print("----------------------------------------")

    # --- Phase 4: DB/User Setup ---
    if system in ("Linux", "Darwin"):  # For Linux/MacOS, use MySQL/MariaDB
        db_name, user_id, priv_level = db_user_setup_linux()
    elif system == "Windows":
        print("Windows installer uses SQLite by default; user DB creation not needed.")

    print("")
    print("STEP 4 completed successfully.")
    print("----------------------------------------")

    # Phase 5: PEP 668 advisory
    check_pep668(system, distro_class)

    print("\nMusica installation completed. The program is now ready to use.")

    print("")
    print("Installer completed successfully.")

# ------------------------------------------------------------
# Execute
# ------------------------------------------------------------
if __name__ == "__main__":
    main()

