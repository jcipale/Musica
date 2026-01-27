#!/usr/bin/env python3
"""
musica_db_query.py
Execute an ad-hoc SQL query and print results.
Translated from musica_db_query.csh
"""

import os
import sys
import subprocess
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
    # script_dir and base_dir
    script_dir = Path(__file__).resolve().parent
    base_dir = script_dir.parent

    # load config
    config_path = base_dir / "config" / "musica.conf"
    if not config_path.is_file():
        error(f"Error: config missing: {config_path}")

    config = load_config(config_path)

    # run environment verification
    verify_script = base_dir / "bin" / "musica_verify_env.py"
    if not verify_script.is_file():
        error("Environment verification script not found.")

    result = subprocess.run(
        [sys.executable, str(verify_script)],
        check=False
    )
    if result.returncode != 0:
        error("Environment verification failed.")

    # arguments
    if len(sys.argv) < 2:
        print(f'Usage: {sys.argv[0]} "SQL_QUERY"')
        sys.exit(1)

    # join all args into one query string
    query = " ".join(sys.argv[1:])

    db_type = config.get("MUSICA_DB_TYPE")
    db_name = config.get("MUSICA_DB_NAME")
    db_user = config.get("MUSICA_DB_USER", "")
    db_pass = config.get("MUSICA_DB_PASS", "")

    if not db_type or not db_name:
        error("Database configuration incomplete.")

    # build command
    if db_pass == "":
        # matches: sudo $MUSICA_DB_TYPE -D DB -e "query"
        cmd = [
            "sudo",
            db_type,
            "-D",
            db_name,
            "-e",
            query,
        ]
    else:
        # matches: mysql/mariadb -u user -ppass -D DB -e "query"
        cmd = [
            db_type,
            "-u",
            db_user,
            f"-p{db_pass}",
            "-D",
            db_name,
            "-e",
            query,
        ]

    result = subprocess.run(cmd)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()

