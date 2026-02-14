#!/opt/Musica/venv/bin/python3
"""
musica_db_load.py
-----------------
Loads a CSV file into stg_recordings using MySQL LOCAL INFILE.

Relies entirely on ~/.my.cnf for credentials.
"""

from pathlib import Path
import argparse
import subprocess
import sys

def main():
    parser = argparse.ArgumentParser(
        description="Load CSV into stg_recordings"
    )
    parser.add_argument(
        "--csv",
        required=True,
        help="CSV file to load"
    )

    args = parser.parse_args()

    csv_file = Path(args.csv)
    if not csv_file.is_file():
        print(f"ERROR: CSV file not found: {csv_file}")
        sys.exit(1)

    print(f"Loading CSV → staging table")
    print(f"CSV : {csv_file}")

    sql = f"""
LOAD DATA LOCAL INFILE '{csv_file}'
INTO TABLE stg_recordings
FIELDS TERMINATED BY ';'
OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\\n'
IGNORE 1 LINES
(
    artist,
    title,
    year,
    orchestra,
    conductor,
    genre,
    format,
    label,
    catalog_number,
    reissue,
    recording_mode,
    dbx_encoded
);
"""

    cmd = ["mysql"]

    try:
        subprocess.run(
            cmd,
            input=sql,
            text=True,
            check=True
        )
    except subprocess.CalledProcessError as e:
        print("ERROR: CSV load failed")
        sys.exit(1)

    print("CSV loaded successfully.")


if __name__ == "__main__":
    main()

