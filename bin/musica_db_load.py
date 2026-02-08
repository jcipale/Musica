#!/opt/Musica/venv/bin/python3
# musica_db_load.py — Load CSV into stg_recordings

import subprocess
from pathlib import Path
import sys

DB_NAME = "QA_Musica"  # Could also prompt interactively
CSV_DIR = Path("/opt/Musica/data/imports")


def require_root():
    import os
    if os.geteuid() != 0:
        print("ERROR: Must run as root (sudo).")
        sys.exit(1)


def load_csv(csv_file: Path, db_name: str):
    if not csv_file.is_file():
        print(f"ERROR: CSV file not found: {csv_file}")
        sys.exit(1)

    print(f"Loading CSV: {csv_file} → staging table")
    cmd = ["mysql", "-u", "root", "--local-infile=1", db_name]
    sql = f"""
    LOAD DATA LOCAL INFILE '{csv_file}'
    INTO TABLE stg_recordings
    FIELDS TERMINATED BY ','
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
    try:
        subprocess.run(cmd, input=sql, text=True, check=True)
    except subprocess.CalledProcessError as e:
        print("ERROR: Failed to load CSV")
        print(e)
        sys.exit(1)

    print("CSV loaded successfully.")


if __name__ == "__main__":
    require_root()
    csv_file = CSV_DIR / (sys.argv[1] if len(sys.argv) > 1 else "recordings_load.csv")
    load_csv(csv_file, DB_NAME)

