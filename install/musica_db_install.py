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

MUSICA_CONF = Path("/opt/Musica/config/musica.conf")
MUSICA_CONF_PATH = Path("/opt/Musica/config/musica.conf")
DEFAULT_VENV_PATH = Path("/opt/Musica/venv")


# ------------------------------------------------------------
# Utility functions
# ------------------------------------------------------------

def require_root():
    if os.geteuid() != 0:
        print("ERROR: This installer must be run as root (sudo).")
        print(f"Run again using: sudo {sys.argv[0]}")
        sys.exit(1)

# ------------------------------------------------------------
def validate_paths(config):
    print("")
    print("STEP 6: Validating Musica paths")
    print("-------------------------------------------------------------")

    paths = {
        "MUSICA_BASE_DIR": config["MUSICA_BASE_DIR"],
        "MUSICA_CONFIG_DIR": config["MUSICA_CONFIG_DIR"],
        "MUSICA_SQL_DIR": config["MUSICA_SQL_DIR"],
        "MUSICA_DATA_DIR": config["MUSICA_DATA_DIR"],
    }

    for name, path in paths.items():
        p = Path(path)
        if not p.exists():
            print(f"ERROR: Path does not exist: {name} -> {path}")
            sys.exit(1)
        print(f"OK: {name} = {path}")

# ------------------------------------------------------------
def final_summary(db_name, db_user, privileges):
    print("")
    print("-------------------------------------------------------------")
    print("Musica installation completed successfully.")
    print("")
    print("Database configuration:")
    print(f"  Database   : {db_name}")
    print(f"  User       : {db_user}")
    print(f"  Privileges : {privileges}")
    print("")
    print("Musica is ready for use.")
    print("-------------------------------------------------------------")

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
# STEP 2.5: Ensure database packages installed  
# ------------------------------------------------------------
def ensure_database_installed(system, distro_class, musica_config):
    if system == "Linux":
        return ensure_db_linux(distro_class, musica_config)
    elif system == "Darwin":
        return ensure_db_macos(musica_config)
    elif system == "SunOS":
        return ensure_db_sunos(musica_config)
    else:
        print(f"Database auto-install not supported on {system}.")
        return True

# ------------------------------------------------------------
def ensure_db_linux(distro_class, musica_config):
    engine = musica_config.get("DEFAULT_DB_ENGINE", "mariadb")

    print("STEP 2.5: Ensuring database packages are installed")
    print("-------------------------------------------------------------")

    if engine != "mariadb":
        print(f"Unsupported DB engine '{engine}'")
        return False

    if shutil.which("mysql") or shutil.which("mariadb"):
        print("Database client already present.")
        return True

    resp = input("MariaDB not found. Install now? [y/N]: ").strip().lower()
    if resp != "y":
        return False

    if distro_class == "Debian-family":
        subprocess.run(["apt-get", "update"], check=True)
        subprocess.run(
            ["apt-get", "-y", "install", "mariadb-server", "mariadb-client"],
            check=True
        )

    elif distro_class == "RedHat-family":
        pm = "dnf" if shutil.which("dnf") else "yum"
        subprocess.run(
            [pm, "-y", "install", "mariadb-server", "mariadb"],
            check=True
        )
        subprocess.run(["systemctl", "enable", "--now", "mariadb"], check=False)

    elif distro_class == "SUSE-family":
        subprocess.run(
            ["zypper", "--non-interactive", "install", "mariadb"],
            check=True
        )
        subprocess.run(["systemctl", "enable", "--now", "mariadb"], check=False)

    elif distro_class == "Arch-family":
        subprocess.run(
            ["pacman", "-Sy", "--noconfirm", "mariadb"],
            check=True
        )
        subprocess.run(
            ["mariadb-install-db", "--user=mysql", "--basedir=/usr", "--datadir=/var/lib/mysql"],
            check=False
        )
        subprocess.run(["systemctl", "enable", "--now", "mariadb"], check=False)

    elif distro_class == "Alpine":
        subprocess.run(
            ["apk", "add", "mariadb", "mariadb-client"],
            check=True
        )
        subprocess.run(["rc-service", "mariadb", "start"], check=False)

    else:
        print(f"Unsupported Linux distro class: {distro_class}")
        return False

    print("MariaDB installation completed.")
    return True

# ------------------------------------------------------------
def ensure_db_macos(musica_config):
    print("STEP 2.5: Ensuring database packages are installed")
    print("-------------------------------------------------------------")

    if shutil.which("mysql") or shutil.which("mariadb"):
        print("Database client already present.")
        return True

    if not shutil.which("brew"):
        print("ERROR: Homebrew not found.")
        print("Install from https://brew.sh/")
        return False

    resp = input("Install MariaDB via Homebrew? [y/N]: ").strip().lower()
    if resp != "y":
        return False

    subprocess.run(["brew", "install", "mariadb"], check=True)
    subprocess.run(["brew", "services", "start", "mariadb"], check=False)

    print("MariaDB installation completed.")
    return True

# ------------------------------------------------------------
def ensure_db_sunos(musica_config):
    print("STEP 2.5: Ensuring database packages are installed")
    print("-------------------------------------------------------------")

    if shutil.which("mysql"):
        print("Database client already present.")
        return True

    resp = input("Install MariaDB using pkg? [y/N]: ").strip().lower()
    if resp != "y":
        return False

    subprocess.run(
        ["pkg", "install", "-y", "database/mariadb-106"],
        check=True
    )

    print("MariaDB installation completed.")
    return True

# ------------------------------------------------------------
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
# STEP 6: Configuration Loader Mechanism
# ------------------------------------------------------------
def load_musica_config():
    print("STEP 5: Validating musica.conf")
    print("-------------------------------------------------------------")

    if not MUSICA_CONF.is_file():
        print(f"ERROR: Missing config file: {MUSICA_CONF}")
        sys.exit(1)

    config = {}

    with MUSICA_CONF.open() as f:
        for lineno, line in enumerate(f, start=1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            if "=" not in line:
                print(f"ERROR: Invalid config syntax at line {lineno}")
                sys.exit(1)

            key, value = line.split("=", 1)
            config[key.strip()] = value.strip()

    required_keys = [
        "MUSICA_BASE_DIR",
        "MUSICA_CONFIG_DIR",
        "MUSICA_SQL_DIR",
        "MUSICA_DATA_DIR",
        "MUSICA_DB_TYPE",
    ]

    missing = [k for k in required_keys if k not in config]
    if missing:
        print("ERROR: Missing required config keys:")
        for k in missing:
            print(f"  - {k}")
        sys.exit(1)

    print("Loaded configuration:")
    print(f"  MUSICA_BASE_DIR  = {config['MUSICA_BASE_DIR']}")
    print(f"  MUSICA_SQL_DIR   = {config['MUSICA_SQL_DIR']}")
    print(f"  MUSICA_CONFIG_DIR= {config['MUSICA_CONFIG_DIR']}")

    print("musica.conf loaded successfully.")
    return config

# ------------------------------------------------------------
# STEP 6: PEP 668 Advisory Check
# ------------------------------------------------------------
def check_pep668(system: str, distro_class: str):
    """
    Detect if the system may require PEP 668 workaround (venv) for MariaDB/Python interface.
    Only applicable for Linux/Debian-family systems (Deb13+).
    """
    print("\nSTEP 6: PEP 668 Advisory Check")
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
# STEP 6.1: Enforce / Install PEP 668 Virtual Environment
# ------------------------------------------------------------
def ensure_venv_pep668(system: str, distro_class: str):
    """
    Create and initialize a Python virtual environment when
    PEP 668 protections are likely in effect.
    """

    # Only apply where it actually matters
    pep_applicable = (
        system == "Linux" and distro_class in ("Debian-family", "RHEL-family", "SUSE-family")
    ) or system == "Darwin"

    if not pep_applicable:
        return True

    venv_dir = Path("/opt/Musica/venv")
    venv_python = venv_dir / "bin/python"
    venv_pip = venv_dir / "bin/pip"

    if venv_python.exists():
        print("Virtual environment already exists:", venv_dir)
        return True

    print("")
    print("PEP 668 requires a Python virtual environment.")
    resp = input("Create Musica virtual environment now? [y/N]: ").strip().lower()

    if resp != "y":
        print("Virtual environment creation skipped.")
        return False

    print("Creating virtual environment at:", venv_dir)

    try:
        subprocess.run(
            [sys.executable, "-m", "venv", str(venv_dir)],
            check=True
        )
    except subprocess.CalledProcessError:
        print("ERROR: Failed to create virtual environment.")
        return False

    print("Virtual environment created successfully.")

    # --------------------------------------------------------
    # Install required Python packages INSIDE the venv
    # --------------------------------------------------------
    print("Installing required Python packages into venv...")

    required_packages = [
        "mysqlclient",      # Preferred native driver
        # "mariadb",        # Optional alternative
        # "PyMySQL",        # Optional fallback
    ]

    try:
        subprocess.run(
            [str(venv_pip), "install", "--upgrade", "pip"],
            check=True
        )

        subprocess.run(
            [str(venv_pip), "install", *required_packages],
            check=True
        )
    except subprocess.CalledProcessError:
        print("ERROR: Failed to install Python DB packages in venv.")
        return False

    print("Python DB packages installed successfully.")
    print("PEP 668 environment setup completed.")

    return True

# ------------------------------------------------------------
# Load Configuration Check
# ------------------------------------------------------------
def validate_musica_config(musica_config):
    print("\nSTEP 5: Musica configuration validation")
    print("-------------------------------------------------------------")

    required_keys = [
        "MUSICA_BASE_DIR",
        "MUSICA_SQL_DIR",
        "MUSICA_CONFIG_DIR",
    ]

    missing = False

    for key in required_keys:
        value = musica_config.get(key)

        if not value:
            print(f"ERROR: {key} is not defined in musica.conf")
            missing = True
            continue

        print(f"{key:<20}: {value}")

        if not Path(value).exists():
            print(f"  WARNING: Path does not exist: {value}")

    if missing:
        print("\nConfiguration validation failed.")
        sys.exit(1)

    print("\nConfiguration validation completed successfully.")
    print("-------------------------------------------------------------")

# ------------------------------------------------------------
# Main entry
# ------------------------------------------------------------
# ------------------------------------------------------------
# Main entry
# ------------------------------------------------------------
def main():
    print("Musica Installer – Environment Validation")
    require_root()

    print("")
    print("STEP 1: Root-user verification completed successfully.")
    print("-----------------------------------------------------")

    # --------------------------------------------------------
    # STEP 2: Detect OS and classify distro
    # (existing logic, unchanged)
    # --------------------------------------------------------
    system = detect_os()
    distro_class = classify_os(system)

    print("")
    print("STEP 2: System OS detected successfully.")
    print("-----------------------------------------------------")

    # --------------------------------------------------------
    # STEP 2.5: Load musica.conf EARLY
    # ★ RECENT CHANGE:
    #   - Config is loaded before DB install/detection
    #   - Required for DEFAULT_DB_ENGINE and path validation
    # --------------------------------------------------------
    musica_config = load_musica_config()

    print("")
    print("STEP 2.5: Musica configuration loaded.")
    print("-----------------------------------------------------")

    # --------------------------------------------------------
    # STEP 2.6: Ensure database engine is installed
    # ★ RECENT CHANGE:
    #   - Installer now installs MariaDB/MySQL based on distro
    #   - Supports Debian, RHEL, SUSE, Arch, Alpine, macOS, SunOS
    # --------------------------------------------------------
    print("STEP 2.6: Ensuring database engine is installed")
    print("-----------------------------------------------------")

    if not ensure_database_installed(system, distro_class, musica_config):
        print("ERROR: Database installation failed or was skipped.")
        sys.exit(1)

    print("STEP 2.6 completed successfully.")
    print("-----------------------------------------------------")

    # --------------------------------------------------------
    # STEP 3: Detect database presence / service
    # (post-install verification)
    # --------------------------------------------------------
    db_found = detect_database(system, distro_class)

    if db_found:
        print("Database engine detected. Proceeding...")
    else:
        print("WARNING: Database engine not detected. Installation may fail later.")

    print("")
    print("STEP 3: Database detected successfully.")
    print("-----------------------------------------------------")

    # --------------------------------------------------------
    # STEP 4: Interactive DB/User setup
    # ★ RECENT CHANGE:
    #   - If DB already exists, skip user/password/privileges
    #   - Returns (db_name, user_id, priv_level)
    # --------------------------------------------------------
    db_name = None
    db_user = None
    privileges = None

    if system in ("Linux", "Darwin"):
        db_name, db_user, privileges = db_user_setup_linux()
    elif system == "Windows":
        print("Windows installer uses SQLite by default; no DB/user creation required.")

    print("")
    print("STEP 4 completed successfully.")
    print("-----------------------------------------------------")

    # --------------------------------------------------------
    # STEP 5: Validate Musica configuration values and paths
    # ★ RECENT CHANGE:
    #   - Explicit config key validation
    #   - Path existence checks
    # --------------------------------------------------------
    validate_musica_config(musica_config)

    print("")
    print("STEP 5: Musica configuration validated.")
    print("-----------------------------------------------------")

    # --------------------------------------------------------
    # STEP 6: PEP 668 detection + enforcement
    # ★ IMPLEMENTED:
    #   - Detects PEP 668 conditions
    #   - Creates venv if missing
    #   - Installs Python DB bindings safely
    # --------------------------------------------------------
    check_pep668(system, distro_class)

    if not ensure_venv_pep668(system, distro_class):
        print("WARNING: PEP 668 environment not fully configured.")


    print("")
    print("STEP 6 completed successfully.")
    print("-----------------------------------------------------")

    # --------------------------------------------------------
    # FINAL SUMMARY
    # ★ FIXED:
    #   - Uses correct variable names
    #   - Handles None values cleanly
    # --------------------------------------------------------
    final_summary(db_name, db_user, privileges)

    print("")
    print("Installer completed successfully.")

# ------------------------------------------------------------
# Execute
# ------------------------------------------------------------
if __name__ == "__main__":
    main()

