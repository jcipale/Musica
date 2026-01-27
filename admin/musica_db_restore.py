#!/usr/bin/env python3
"""
musica_db_restore.py
Restore Musica DB from a .sql.gz backup (admin operation).
Translated from musica_db_restore.csh
"""

import os
import sys
import shutil
import subprocess
import gzip
from pathlib import Path


def error(msg, code=1):
    print(msg)
    sys.exit(code)


def load_config(path):
    """
    Load KEY=value pairs from musica.conf.
    Values are treated literally and exported to os.environ.
    """
    config = {}
    with path.open("r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, val = line.split("=", 1)
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            config[key] = val
            os.environ[key] = val
    return config


def main():
    # args
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <backup-file.sql.gz>")
        sys.exit(1)

    backup_file = Path(sys.argv[1])
    if not backup_file.is_file():
        error(f"Error: backup file not found: {backup_file}")

    # script_dir and base_dir
    script_dir = Path(__file__).resolve().parent
    base_dir = script_dir.parent

    # load config
    config_path = base_dir / "config" / "musica.conf"
    if not config_path.is_file():
        error(f"Error: config missing: {config_path}")

    config = load_config(config_path)

    db_name = config.get("MUSICA_DB_NAME")
    db_user = config.get("MUSICA_DB_USER", "")
    db_pass = config.get("MUSICA_DB_PASS", "")
    log_dir = Path(config.get("MUSICA_LOG_DIR", ""))

    if not db_name:
        error("MUSICA_DB_NAME not defined.")
    if not log_dir:
        error("MUSICA_LOG_DIR not defined.")

    log_dir.mkdir(parents=True, exist_ok=True)

    print(f"Restoring database {db_name} from {backup_file}")

    # choose DB client
    mariadb_cmd = shutil.which("mariadb") or shutil.which("mysql")
    if not mariadb_cmd:
        error("Error: mariadb/mysql client not found.")

    # drop and create database
    if db_pass == "":
        drop_cmd = ["sudo", mariadb_cmd, "-e", f"DROP DATABASE IF EXISTS {db_name};"]
        create_cmd = ["sudo", mariadb_cmd, "-e", f"CREATE DATABASE {db_name};"]
    else:
        drop_cmd = [
            mariadb_cmd,
            "-u", db_user,
            f"-p{db_pass}",
            "-e", f"DROP DATABASE IF EXISTS {db_name};",
        ]
        create_cmd = [
            mariadb_cmd,
            "-u", db_user,
            f"-p{db_pass}",
            "-e", f"CREATE DATABASE {db_name};",
        ]

    if subprocess.run(drop_cmd).returncode != 0:
        error("Error: failed to drop database.")

    if subprocess.run(create_cmd).returncode != 0:
        error("Error: failed to create database.")

    # restore
    try:
        with gzip.open(backup_file, "rb") as gz:
            if db_pass == "":
                restore_cmd = ["sudo", mariadb_cmd, db_name]
            else:
                restore_cmd = [
                    mariadb_cmd,
                    "-u", db_user,
                    f"-p{db_pass}",
                    db_name,
                ]

            proc = subprocess.run(
                restore_cmd,
                stdin=gz,
                check=False,
            )

        if proc.returncode != 0:
            error("Restore failed.")

    except Exception as e:
        error(f"Restore failed: {e}")

    print("Restore complete.")
    sys.exit(0)


if __name__ == "__main__":
    main()

