#!/usr/bin/env python3
"""
Phase 3A — MariaDB Environment Check & Optional Installation
Translated from musica_db_check_env.csh
"""

import os
import sys
import shutil
import subprocess
import platform
from pathlib import Path
from datetime import datetime


def exit_error(msg, logfile=None):
    if logfile:
        with logfile.open("a") as f:
            f.write(f"ERROR: {msg}\n")
    print(f"ERROR: {msg}")
    sys.exit(1)


def log(msg, logfile):
    print(msg)
    with logfile.open("a") as f:
        f.write(msg + "\n")


def load_config(conf_path):
    config = {}
    with conf_path.open() as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            k, v = line.split("=", 1)
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            config[k] = v
            os.environ[k] = v
    return config


def run(cmd, logfile, check=False):
    proc = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    with logfile.open("a") as f:
        f.write(proc.stdout)
    if check and proc.returncode != 0:
        exit_error(f"Command failed: {' '.join(cmd)}", logfile)
    return proc.returncode


def main():
    # ------------------------------------------------------------
    # Load configuration (must be first)
    # ------------------------------------------------------------
    if "MUSICA_BASE_DIR" not in os.environ:
        conf_path = Path(__file__).resolve().parent.parent / "config" / "musica.conf"
        if not conf_path.is_file():
            exit_error("musica.conf not found")
        load_config(conf_path)

    base_dir = Path(os.environ["MUSICA_BASE_DIR"])
    log_dir = base_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "db_env_check.log"

    log("===== Phase 3A: MariaDB Environment Check =====", log_file)
    log(f"Started: {datetime.now()}", log_file)

    # ----------------------------
    # STEP 1 — OS argument check
    # ----------------------------
    os_arg = sys.argv[1] if len(sys.argv) >= 2 else ""
    if os_arg:
        log(f"OS argument supplied: {os_arg}", log_file)

    # ----------------------------
    # STEP 2 — Auto-detect OS
    # ----------------------------
    os_detect = ""
    if not os_arg:
        if Path("/etc/os-release").is_file():
            try:
                for line in Path("/etc/os-release").read_text().splitlines():
                    if line.startswith("ID="):
                        os_detect = line.split("=", 1)[1].strip().strip('"')
                        break
                if os_detect:
                    log(f"Auto-detected OS: {os_detect}", log_file)
            except Exception:
                pass

    # ----------------------------------------
    # STEP 3 — User menu if detection fails
    # ----------------------------------------
    if not os_arg and not os_detect:
        log("OS auto-detect failed — prompting user.", log_file)
        print("\nSelect your operating system:")
        options = [
            ("1", "debian"),
            ("2", "rhel"),
            ("3", "fedora"),
            ("4", "opensuse"),
            ("5", "arch"),
            ("6", "macos"),
            ("7", "cancel"),
        ]
        for n, name in options:
            print(f"{n}) {name}")
        choice = input("Enter choice [1-7]: ").strip()
        mapping = dict(options)
        if choice not in mapping or mapping[choice] == "cancel":
            log("User cancelled. Exiting.", log_file)
            sys.exit(1)
        os_detect = mapping[choice]

    os_name = os_arg if os_arg else os_detect
    log(f"Using OS setting: {os_name}", log_file)
    print()

    # ----------------------------------------
    # STEP 4 — Check MariaDB client presence
    # ----------------------------------------
    log("Checking MariaDB client tools...", log_file)
    mariadb_cmd = shutil.which("mariadb")

    if mariadb_cmd:
        log(f"MariaDB client found: {mariadb_cmd}", log_file)
    else:
        log("MariaDB client NOT found.", log_file)
        ans = input("Install MariaDB now? (y/n): ").strip()
        if ans.lower() != "y":
            log("User declined MariaDB install. Aborting.", log_file)
            sys.exit(1)

        log("User approved MariaDB installation.", log_file)

        if os_name in ("debian", "ubuntu"):
            run(["sudo", "apt", "update"], log_file, True)
            run(
                ["sudo", "apt", "install", "-y", "mariadb-server", "mariadb-client"],
                log_file,
                True,
            )
        elif os_name in ("rhel", "centos"):
            run(
                ["sudo", "yum", "install", "-y", "mariadb-server", "mariadb"],
                log_file,
                True,
            )
        elif os_name == "fedora":
            run(
                ["sudo", "dnf", "install", "-y", "mariadb-server", "mariadb"],
                log_file,
                True,
            )
        elif os_name == "opensuse":
            run(["sudo", "zypper", "install", "-y", "mariadb"], log_file, True)
        elif os_name == "arch":
            run(
                ["sudo", "pacman", "-Sy", "--noconfirm", "mariadb"],
                log_file,
                True,
            )
        elif os_name == "macos":
            run(["brew", "install", "mariadb"], log_file, True)
        else:
            exit_error(f"Unsupported OS: {os_name}", log_file)

    # ----------------------------------------
    # STEP 5 — Ensure MariaDB server is running
    # ----------------------------------------
    log("Checking MariaDB service status...", log_file)

    systemctl = shutil.which("systemctl")
    if systemctl:
        proc = subprocess.run(
            ["systemctl", "is-active", "mariadb"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        if proc.stdout.strip() != "active":
            print("MariaDB is not running.")
            ans = input("Start MariaDB now? (y/n): ").strip()
            if ans.lower() == "y":
                run(["sudo", "systemctl", "start", "mariadb"], log_file, True)
            else:
                log("User declined to start MariaDB. Exiting.", log_file)
                sys.exit(1)
        else:
            log("MariaDB service is active.", log_file)
    else:
        log("systemctl not available — skipping service check.", log_file)

    # ----------------------------------------
    # STEP 6 — Deferred checks
    # ----------------------------------------
    log("Database checks deferred to Phase 3B.", log_file)

    log("Phase 3A complete. Environment ready for Phase 3B.", log_file)
    sys.exit(0)


if __name__ == "__main__":
    main()

