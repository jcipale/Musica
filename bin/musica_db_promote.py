#!/opt/Musica/venv/bin/python3
"""
musica_db_promote.py
--------------------
Promotes valid rows from stg_recordings into recordings.
"""

from pathlib import Path
import argparse
import subprocess
import sys

SQL_DIR = Path("/opt/Musica/sql/runtime")
PROMOTE_SQL = SQL_DIR / "promote_staging.sql"

def main():
    parser = argparse.ArgumentParser(
        description="Promote staging data into recordings"
    )

    args = parser.parse_args()

    if not PROMOTE_SQL.is_file():
        print(f"ERROR: SQL file not found: {PROMOTE_SQL}")
        sys.exit(1)

    print(f"Promoting staging data")

    cmd = ["mysql"]

    try:
        with PROMOTE_SQL.open() as f:
            subprocess.run(
                cmd,
                stdin=f,
                check=True
            )
    except subprocess.CalledProcessError:
        print("ERROR: Promotion failed")
        sys.exit(1)

    print("Promotion completed successfully.")


if __name__ == "__main__":
    main()

