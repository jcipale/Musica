#!/usr/bin/env python3
"""
musica_db_destroy.py
Completely destroy the Musica database for QA/dev reset.
Translated from musica_db_destroy.csh
"""

import sys
import subprocess
from pathlib import Path
from datetime import datetime


def log(msg, logfile):
    print(msg)
    with logfile.open("a") as f:
        f.write(msg + "\n")


def exit_error(msg, logfile=None):
    if logfile:
        log(f"ERROR: {msg}", logfile)
    else:
        print(f"ERROR: {msg}")
    sys.exit(1)


def main():
    # ----------------------------------------------
    # Script path & base_dir setup (faithful)
    # ----------------------------------------------
    if len(sys.argv) >= 2:
        script_name = sys.argv[0]
    else:
        script_name = "musica_db_destroy.py"

    script_path = Path.cwd() / script_name
    script_dir = script_path.parent
    base_dir = (script_dir / "..").resolve()

    log_dir = base_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "db_destroy.log"

    log("===== Musica DB Destroy =====", log_file)
    log(f"Started: {datetime.now()}", log_file)

    # ----------------------------------------
    # Safety Confirmation
    # ----------------------------------------
    print("\nWARNING: This will permanently delete the Musica database.")
    confirm = input("Type 'DESTROY' to continue:\n> ").strip()

    if confirm != "DESTROY":
        log("Invalid confirmation. Aborting.", log_file)
        sys.exit(1)

    log("User confirmed destruction.", log_file)

    # ----------------------------------------
    # Check MariaDB root access
    # ----------------------------------------
    log("Testing MariaDB root login...", log_file)

    test_proc = subprocess.run(
        ["mariadb", "-u", "root"],
        input="SELECT 1;\n",
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        text=True,
    )

    if test_proc.returncode != 0:
        exit_error("Cannot authenticate to MariaDB as root.", log_file)

    # ----------------------------------------
    # Check if DB exists
    # ----------------------------------------
    log("Checking if Musica DB exists...", log_file)

    check_proc = subprocess.run(
        ["mariadb", "-u", "root"],
        input="SHOW DATABASES LIKE 'Musica';\n",
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
    )

    if "Musica" not in check_proc.stdout:
        log("Musica database does not exist. Nothing to destroy.", log_file)
        sys.exit(0)

    # ----------------------------------------
    # Drop DB
    # ----------------------------------------
    log("Dropping Musica database...", log_file)

    drop_proc = subprocess.run(
        ["mariadb", "-u", "root"],
        input="DROP DATABASE Musica;\n",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    with log_file.open("a") as f:
        f.write(drop_proc.stdout)

    if drop_proc.returncode != 0:
        exit_error("Failed to drop Musica DB.", log_file)

    log("Musica DB successfully removed.", log_file)
    log(f"Completed: {datetime.now()}", log_file)

    sys.exit(0)


if __name__ == "__main__":
    main()

