#!/opt/Musica/venv/bin/python

"""
Phase 3C — MariaDB User Creation & Verification
"""

import os
import subprocess
import sys
from pathlib import Path

# -----------------------------
# Helpers
# -----------------------------

def run(cmd, check=False, capture=False):
    return subprocess.run(
        cmd,
        shell=True,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
    )


def logprint(msg, logfile):
    line = msg.rstrip()
    print(line)
    with logfile.open("a") as f:
        f.write(line + "\n")


def logerror(msg, logfile):
    logprint(f"ERROR: {msg}", logfile)


# -----------------------------
# Load configuration
# -----------------------------

if "MUSICA_BASE_DIR" not in os.environ:
    conf = Path(__file__).resolve().parent.parent / "config" / "musica.conf"
    if conf.exists():
        # source musica.conf into environment
        cmd = f"set -a && . '{conf}' && env"
        result = run(cmd, capture=True)
        for line in result.stdout.splitlines():
            if "=" in line:
                k, v = line.split("=", 1)
                os.environ[k] = v
    else:
        print("ERROR: musica.conf not found")
        sys.exit(1)

MUSICA_BASE_DIR = os.environ["MUSICA_BASE_DIR"]
MUSICA_DB_NAME = os.environ["MUSICA_DB_NAME"]
MUSICA_DB_USER = os.environ["MUSICA_DB_USER"]
MUSICA_DB_HOST = os.environ.get("MUSICA_DB_HOST", "localhost")
MUSICA_DB_PASS = os.environ.get("MUSICA_DB_PASS", "")

log_dir = Path(MUSICA_BASE_DIR) / "logs"
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / "db_user_create.log"

print("===== Phase 3C: MariaDB User Creation =====")
with log_file.open("w") as f:
    f.write("===== Phase 3C: MariaDB User Creation =====\n")

logprint(f"Database: {MUSICA_DB_NAME}", log_file)
logprint(f"User:     {MUSICA_DB_USER}", log_file)
print("")

# ------------------------------------------------------------
# STEP 1 — Verify database exists
# ------------------------------------------------------------

logprint("Checking database existence...", log_file)

cmd = (
    "sudo mariadb -N -B -e "
    f"\"SELECT SCHEMA_NAME FROM information_schema.SCHEMATA "
    f"WHERE SCHEMA_NAME='{MUSICA_DB_NAME}';\""
)

res = run(cmd, capture=True)

if res.returncode != 0:
    logerror("Failed to query database catalog", log_file)
    sys.exit(1)

db_check = res.stdout.strip()

if db_check != MUSICA_DB_NAME:
    logerror(
        f"Database '{MUSICA_DB_NAME}' does not exist. Run Phase 3B first.",
        log_file,
    )
    sys.exit(1)

logprint("Database exists.", log_file)

# ------------------------------------------------------------
# STEP 2 — Create user (idempotent)
# ------------------------------------------------------------

logprint("Ensuring database user exists...", log_file)

if MUSICA_DB_PASS == "":
    create_user_sql = (
        f"CREATE USER IF NOT EXISTS "
        f"'{MUSICA_DB_USER}'@'{MUSICA_DB_HOST}' "
        f"IDENTIFIED VIA unix_socket;"
    )
else:
    create_user_sql = (
        f"CREATE USER IF NOT EXISTS "
        f"'{MUSICA_DB_USER}'@'{MUSICA_DB_HOST}' "
        f"IDENTIFIED BY '{MUSICA_DB_PASS}';"
    )

res = run(f"sudo mariadb -e \"{create_user_sql}\"")

if res.returncode != 0:
    logerror(f"Failed to create or verify user '{MUSICA_DB_USER}'", log_file)
    sys.exit(1)

logprint("User exists.", log_file)

# ------------------------------------------------------------
# STEP 3 — Apply grants
# ------------------------------------------------------------

logprint("Applying grants...", log_file)

grant_sql = (
    f"GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, INDEX, ALTER "
    f"ON {MUSICA_DB_NAME}.* "
    f"TO '{MUSICA_DB_USER}'@'{MUSICA_DB_HOST}';"
)

res = run(f"sudo mariadb -e \"{grant_sql}\"")
res2 = run("sudo mariadb -e \"FLUSH PRIVILEGES;\"")

if res.returncode != 0 or res2.returncode != 0:
    logerror("Failed to apply grants", log_file)
    sys.exit(1)

logprint("Grants applied.", log_file)

# ------------------------------------------------------------
# STEP 4 — Verify login as runtime user
# ------------------------------------------------------------

logprint(f"Verifying login as '{MUSICA_DB_USER}'...", log_file)

if MUSICA_DB_PASS == "":
    test_cmd = (
        f"mariadb -u '{MUSICA_DB_USER}' '{MUSICA_DB_NAME}' "
        f"-e \"SELECT 1;\""
    )
else:
    test_cmd = (
        f"mariadb -u '{MUSICA_DB_USER}' "
        f"-p'{MUSICA_DB_PASS}' "
        f"'{MUSICA_DB_NAME}' "
        f"-e \"SELECT 1;\""
    )

res = run(test_cmd)

if res.returncode != 0:
    logerror(f"Login test failed for user '{MUSICA_DB_USER}'", log_file)
    sys.exit(1)

logprint("User authentication verified.", log_file)
logprint("Phase 3C complete. Database user ready.", log_file)

sys.exit(0)

