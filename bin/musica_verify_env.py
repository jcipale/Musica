#!/opt/Musica/venv/bin/python

"""
musica_verify.py
Verify Musica directory layout, config and DB client/service presence.
Translated from musica_verify.csh
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path


def error(msg, code=1):
    print(msg)
    sys.exit(code)


def load_config(path):
    """
    Load a csh-style KEY=value config file.
    Lines starting with # are ignored.
    Values are treated as literal strings.
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
            os.environ[key] = val  # preserve env-style behavior

    return config


def main():
    # script_dir and base_dir
    script_dir = Path(__file__).resolve().parent
    base_dir = script_dir.parent

    # load config
    config_path = base_dir / "config" / "musica.conf"
    if not config_path.is_file():
        error(f"Error: configuration file not found: {config_path}")

    config = load_config(config_path)

    # required directories
    required_vars = [
        "MUSICA_DATA_DIR",
        "MUSICA_IMPORT_DIR",
        "MUSICA_EXPORT_DIR",
        "MUSICA_ARCHIVE_DIR",
        "MUSICA_BIN_DIR",
        "MUSICA_SQL_DIR",
        "MUSICA_LOG_DIR",
    ]

    for var in required_vars:
        d = config.get(var)
        if not d or not Path(d).is_dir():
            error(f"Missing directory: {d}")

    # check DB client presence
    has_client = False
    if shutil.which("mariadb"):
        has_client = True
    elif shutil.which("mysql"):
        has_client = True

    if not has_client:
        error("Error: no mariadb/mysql client found in PATH.")

    # check DB service if using mariadb/mysql
    db_type = config.get("MUSICA_DB_TYPE", "")
    if db_type in ("mariadb", "mysql"):
        # systemctl only exists on Linux with systemd
        systemctl = shutil.which("systemctl")
        if systemctl:
            try:
                result = subprocess.run(
                    [systemctl, "is-active", db_type],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    text=True,
                    check=False,
                )
                svc = result.stdout.strip()
                if svc != "active":
                    print(f"Warning: {db_type} service not active.")
            except Exception:
                print(f"Warning: unable to determine {db_type} service status.")
        else:
            # macOS / Windows / non-systemd Linux
            print(f"Warning: cannot check {db_type} service status on this platform.")

    print("Environment verification: OK")
    sys.exit(0)


if __name__ == "__main__":
    main()
`

