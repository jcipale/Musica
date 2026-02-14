#!/opt/Musica/venv/bin/python
# ------------------------------------------------------------
# musica_db_batch_tool.py
#
# Musica Batch Pipeline Wrapper
#
# Responsibilities:
#   - Validate execution environment
#   - Validate ~/.my.cnf
#   - Optionally perform dry-run
#   - Call loader and promoter scripts (stubbed)
#
# No DB flags.
# All credentials come from ~/.my.cnf
# ------------------------------------------------------------

import sys
import os
import argparse
import configparser
from pathlib import Path


# ------------------------------------------------------------
# Safety
# ------------------------------------------------------------
def enforce_venv():
    expected = Path("/opt/Musica/venv/bin/python")
    if Path(sys.executable) != expected:
        print("ERROR: Must run using Musica virtual environment.")
        print(f"Expected: {expected}")
        print(f"Running : {sys.executable}")
        sys.exit(1)


# ------------------------------------------------------------
# .my.cnf Validation
# ------------------------------------------------------------
def validate_mycnf():
    home = Path.home()
    cnf_path = home / ".my.cnf"

    if not cnf_path.is_file():
        print(f"ERROR: Missing MySQL config file: {cnf_path}")
        sys.exit(1)

    config = configparser.ConfigParser()
    config.read(cnf_path)

    if "client" not in config:
        print("ERROR: .my.cnf missing [client] section.")
        sys.exit(1)

    client = config["client"]

    required_keys = ["user", "password", "host", "database"]

    for key in required_keys:
        if key not in client or not client[key].strip():
            print(f"ERROR: .my.cnf missing required key: {key}")
            sys.exit(1)

    return client["database"]


# ------------------------------------------------------------
# File Checks
# ------------------------------------------------------------
def validate_csv():
    csv_path = Path("/opt/Musica/data/imports/recordings_load.csv")
    if not csv_path.is_file():
        print(f"ERROR: Missing CSV file: {csv_path}")
        sys.exit(1)
    return csv_path


def validate_script(path):
    if not path.is_file():
        print(f"ERROR: Missing script: {path}")
        sys.exit(1)


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------
def main():
    enforce_venv()

    parser = argparse.ArgumentParser(description="Musica Batch Pipeline")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate pipeline without executing load/promote"
    )
    args = parser.parse_args()

    print("==================================================")
    print("Musica Batch Pipeline")
    print("==================================================")

    db_name = validate_mycnf()
    csv_path = validate_csv()

    loader_script = Path("/opt/Musica/bin/musica_db_load.py")
    promoter_script = Path("/opt/Musica/bin/musica_db_promote.py")

    validate_script(loader_script)
    validate_script(promoter_script)

    print(f"OS User   : {os.getlogin()}")
    print(f"Database  : {db_name}")
    print(f"CSV File  : {csv_path}")
    print(f"Dry Run   : {args.dry_run}")
    print("==================================================")

    # ---- Dry Run ----
    if args.dry_run:
        print("\n[DRY RUN] No database operations will be performed.")
        print(f"Would call: {loader_script}")
        print(f"Would call: {promoter_script}")
        print("\nDry run validation successful.")
        sys.exit(0)

    # ---- Execution (Stub Mode) ----
    print("\n[STEP 1] Stage CSV into stg_recordings")
    print(f"Calling: {loader_script}")
    print("NOTE: Execution disabled in this wrapper version")

    print("\n[STEP 2] Promote staging into recordings")
    print(f"Calling: {promoter_script}")
    print("NOTE: Execution disabled in this wrapper version")

    print("\nPipeline completed successfully.")
    sys.exit(0)


# ------------------------------------------------------------
if __name__ == "__main__":
    main()

