#!/usr/bin/env python3
"""
musica_db_backup.py
Create a timestamped compressed SQL backup into MUSICA_ARCHIVE_DIR.
Translated from musica_db_backup.csh
"""

import os
import sys
import shutil
import subprocess
import gzip
from pathlib import Path
from datetime import datetime


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
    # script_dir and base_dir
    script_dir = Path(__file__).resolve().parent
    base_dir = script_dir.parent

    # load config
    config_path = base_dir / "config" / "musica.conf"
    if not config_path.is_file():
        error(f"Error: config missing: {config_path}")

    config = load_config(config_path)

    log_dir = Path(config.get("MUSICA_LOG_DIR", ""))
    if not log_dir:
        error("MUSICA_LOG_DIR not defined.")

    log_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = log_dir / f"musica_backup_{timestamp}.sql.gz"
    log_file = log_dir / f"musica_backup_{timestamp}.log"

    # choose dump command
    dump_cmd = None
    if shutil.which("mysqldump"):
        dump_cmd = "mysqldump"
    elif shutil.which("mariadb-dump"):
        dump_cmd = "mariadb-dump"

    if not dump_cmd:
        error("Error: mysqldump/mariadb-dump not found.")

    db_name = config.get("MUSICA_DB_NAME")
    db_user = config.get("MUSICA_DB_USER", "")
    db_pass = config.get("MUSICA_DB_PASS", "")

    if not db_name:
        error("MUSICA_DB_NAME not defined.")

    print(f"Backing up database {db_name} to {backup_file}")

    # temp dump file (portable replacement for /tmp)
    tmp_dump = Path(os.environ.get("TEMP", "/tmp")) / "musica_dump.sql"

    try:
        with log_file.open("w") as logf, tmp_dump.open("w") as dumpf:
            if db_pass == "":
                cmd = [
                    dump_cmd,
                    "--databases",
                    db_name,
                ]
            else:
                cmd = [
                    dump_cmd,
                    f"--user={db_user}",
                    f"--password={db_pass}",
                    "--databases",
                    db_name,
                ]

            result = subprocess.run(
                cmd,
                stdout=dumpf,
                stderr=logf,
                check=False,
                text=True,
            )

        if result.returncode != 0:
            tmp_dump.unlink(missing_ok=True)
            error(f"Error during dump. See {log_file}")

        # compress
        with tmp_dump.open("rb") as src, gzip.open(backup_file, "wb") as dst:
            shutil.copyfileobj(src, dst)

    except Exception as e:
        tmp_dump.unlink(missing_ok=True)
        error(f"Error during backup: {e}")

    finally:
        tmp_dump.unlink(missing_ok=True)

    print(f"Backup complete: {backup_file}")
    print(f"Log: {log_file}")
    sys.exit(0)


if __name__ == "__main__":
    main()

