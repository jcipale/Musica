#!/opt/Musica/venv/bin/python

"""
musica_db_create.py
Phase 3B — Create Musica database and load schema
"""

import os
import subprocess
import sys
from pathlib import Path

# -----------------------------
# Helpers
# -----------------------------

def run(cmd, capture=False):
    return subprocess.run(
        cmd,
        shell=True,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
    )


def logprint(msg, logfile):
    print(msg)
    with logfile.open("a") as f:
        f.write(msg + "\n")


def logerror(msg, logfile):
    logprint(f"ERROR: {msg}", logfile)


# -----------------------------
# Load configuration
# -----------------------------

if "MUSICA_BASE_DIR" not in os.environ:
    for candidate in [
        Path("config/musica.conf"),
        Path("../config/musica.conf"),
    ]:
        if candidate.exists():
            cmd = f"set -a && . '{candidate}' && env"
            res = run(cmd, capture=True)
            for line in res.stdout.splitlines():
                if "=" in line:
                    k, v = line.split("=", 1)
                    os.environ[k] = v
            break
    else:
        print("ERROR: musica.conf not found. Run: source config/musica.conf")
        sys.exit(1)

MUSICA_BASE_DIR = os.environ["MUSICA_BASE_DIR"]
MUSICA_DB_TYPE = os.environ["MUSICA_DB_TYPE"]
MUSICA_DB_NAME = os.environ["MUSICA_DB_NAME"]
MUSICA_DB_USER = os.environ.get("MUSICA_DB_USER", "")
MUSICA_DB_PASS = os.environ.get("MUSICA_DB_PASS")
MUSICA_SQL_DIR = os.environ["MUSICA_SQL_DIR"]

# -----------------------------
# Parse CLI arguments (-db)
# -----------------------------

args = sys.argv[1:]
i = 0
while i < len(args):
    if args[i] == "-db":
        i += 1
        if i < len(args):
            MUSICA_DB_NAME = args[i]
            os.environ["MUSICA_DB_NAME"] = MUSICA_DB_NAME
        else:
            print("ERROR: -db requires a database name")
            sys.exit(1)
    i += 1

# -----------------------------
# Logging
# -----------------------------

log_dir = Path(MUSICA_BASE_DIR) / "logs"
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / "db_creation.log"

print("===== Phase 3B: MariaDB Create Database =====")
with log_file.open("w") as f:
    f.write("===== Phase 3B: MariaDB Create Database =====\n")

logprint("Musica Database Creation Utility", log_file)
logprint("----------------------------------------", log_file)
logprint(f"Database type:     {MUSICA_DB_TYPE}", log_file)
logprint(f"Database name:     {MUSICA_DB_NAME}", log_file)
logprint(f"Schema file:       {MUSICA_SQL_DIR}/Create_Schema.sql", log_file)
print("")

# -----------------------------
# Validate schema file
# -----------------------------

schema_file = Path(MUSICA_SQL_DIR) / "Create_Schema.sql"
if not schema_file.exists():
    logerror(f"Schema file not found: {schema_file}", log_file)
    sys.exit(1)
else:
    logprint(f"Schema file found: {schema_file}", log_file)

# -----------------------------
# STEP 1A — Verify / create DB
# -----------------------------

logprint(f"Checking if database '{MUSICA_DB_NAME}' exists...", log_file)

res = run(
    "sudo mariadb -N -B -e "
    f"\"SELECT SCHEMA_NAME FROM information_schema.SCHEMATA "
    f"WHERE SCHEMA_NAME='{MUSICA_DB_NAME}';\"",
    capture=True,
)

if res.returncode != 0:
    logerror("Failed to query database catalog.", log_file)
    logprint(res.stdout or "", log_file)
    sys.exit(1)

if res.stdout.strip() == MUSICA_DB_NAME:
    logprint(f"Database '{MUSICA_DB_NAME}' already exists.", log_file)
else:
    logprint(f"Database '{MUSICA_DB_NAME}' does not exist. Creating...", log_file)
    res = run(
        "sudo mariadb -e "
        f"\"CREATE DATABASE {MUSICA_DB_NAME} "
        f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;\""
    )
    if res.returncode != 0:
        logerror(f"Failed to create database '{MUSICA_DB_NAME}'.", log_file)
        sys.exit(1)
    logprint(f"Database '{MUSICA_DB_NAME}' created.", log_file)

# -----------------------------
# STEP 2 — Load schema
# -----------------------------

if MUSICA_DB_TYPE in ("mariadb", "mysql"):
    logprint(f"Loading schema into database '{MUSICA_DB_NAME}'...", log_file)

    if MUSICA_DB_PASS is None:
        cmd = (
            f"sudo mariadb --batch --silent {MUSICA_DB_NAME} "
            f"< '{schema_file}'"
        )
    else:
        cmd = (
            f"mariadb -u {MUSICA_DB_USER} "
            f"-p{MUSICA_DB_PASS} {MUSICA_DB_NAME} "
            f"< '{schema_file}'"
        )

    res = run(cmd)
    if res.returncode != 0:
        logerror("Schema creation failed.", log_file)
        sys.exit(1)

# -----------------------------
# STEP 3 — Verify schema
# -----------------------------

logprint(f"Verifying schema load in database '{MUSICA_DB_NAME}'...", log_file)

res = run(
    f"sudo mariadb -N -B {MUSICA_DB_NAME} "
    f"-e \"SHOW TABLES LIKE 'recordings';\"",
    capture=True,
)

if res.returncode != 0:
    logerror(
        f"Failed to query tables in database '{MUSICA_DB_NAME}'.",
        log_file,
    )
    logprint(res.stdout or "", log_file)
    sys.exit(1)

if res.stdout.strip() != "recordings":
    logerror("Schema verification failed: table 'recordings' not found.", log_file)
    sys.exit(1)

logprint("Schema verification successful.", log_file)
logprint(
    f"Database '{MUSICA_DB_NAME}' initialized and verified successfully.",
    log_file,
)

sys.exit(0)

