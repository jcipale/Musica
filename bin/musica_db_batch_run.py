#!/opt/Musica/venv/bin/python3
"""
musica_db_batch_run.py
----------------------
Wrapper / orchestrator for Musica batch database pipeline.

Responsibilities:
- Validate ~/.my.cnf context
- Extract database from ~/.my.cnf
- Orchestrate batch steps (load → promote)
"""

from pathlib import Path
import argparse
import configparser
import getpass
import subprocess
import sys
import os

CSV_PATH = Path("/opt/Musica/data/imports/recordings_load.csv")


# ============================================================
# Validation helpers
# ============================================================

def validate_mysql_context():
    os_user = getpass.getuser()
    cnf_path = Path.home() / ".my.cnf"

    print(f"Running as OS user : {os_user}")
    print(f"Using MySQL config : {cnf_path}")

    # 1) ~/.my.cnf must exist
    if not cnf_path.exists():
        print("ERROR: ~/.my.cnf not found.")
        print("Run musica_db_provision.py before running batch jobs.")
        sys.exit(1)

    # 2) Enforce permissions
    mode = cnf_path.stat().st_mode & 0o777
    if mode != 0o600:
        print("ERROR: ~/.my.cnf must have permissions 600.")
        print(f"Current permissions: {oct(mode)}")
        sys.exit(1)

    # 3) Parse config
    config = configparser.ConfigParser()
    config.read(cnf_path)

    if "client" not in config or "database" not in config["client"]:
        print("ERROR: ~/.my.cnf missing [client] database entry.")
        sys.exit(1)

    db_name = config["client"]["database"]

    print("MySQL context validated\n")
    return db_name


# ============================================================
# CLI / main
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Run Musica batch load pipeline"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show pipeline steps without executing"
    )

    args = parser.parse_args()

    print("=" * 50)
    print("Musica Batch Pipeline")
    print("=" * 50)

    # Extract DB from ~/.my.cnf
    target_db = validate_mysql_context()

    print(f"Target DB : {target_db}")
    print(f"CSV File  : {CSV_PATH}")
    print(f"Dry Run   : {args.dry_run}")
    print("=" * 50)
    print()

    if args.dry_run:
        print("[DRY RUN] No database operations will be performed.\n")

    # ========================================================
    # Pipeline steps (reference only)
    # ========================================================

    print("[STEP 0] Clear staging table")

    if not args.dry_run:
        try:
            subprocess.run(
                ["mysql", "-e", "DELETE FROM stg_recordings;"],
                check=True
            )
            print("Staging table cleared.\n")
        except subprocess.CalledProcessError:
            print("ERROR: Failed to clear staging table.")
            sys.exit(1)
    else:
        print("Would execute: TRUNCATE TABLE stg_recordings;\n")

    print("[STEP 1] Stage CSV into stg_recordings")
    print("Calling musica_db_load.py")

    if not args.dry_run:
        try:

            subprocess.run(
                [
                    "/opt/Musica/bin/musica_db_load.py",
                    "--csv",
                    str(CSV_PATH)
                ],
                check=True
            )

            print("Load step completed.\n")
        except subprocess.CalledProcessError:
            print("ERROR: Load step failed.")
            sys.exit(1)
    else:
        print("Would call: musica_db_load.py\n")

    # print("[STEP 2] Promote staging into recordings")
    # print("Calling musica_db_promote.py")
    # print("NOTE: Execution disabled in this wrapper version\n")

    print("[STEP 2] Promote staging into recordings")
    print("Calling musica_db_promote.py")

    if not args.dry_run:
        try:
            subprocess.run(
                ["/opt/Musica/bin/musica_db_promote.py"],
                check=True
            )
            print("Promote step completed.\n")
        except subprocess.CalledProcessError:
            print("ERROR: Promote step failed.")
            sys.exit(1)
    else:
        print("Would call: musica_db_promote.py\n")


    print("Pipeline completed successfully.")


if __name__ == "__main__":
    main()
