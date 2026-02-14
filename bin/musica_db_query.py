#!/opt/Musica/venv/bin/python
# musica_db_promote.py — Promote valid staging rows to recordings

import subprocess
import sys
from pathlib import Path


PROMOTE_SQL = """
INSERT INTO recordings (
    artist,
    title,
    year,
    composer,
    orchestra,
    conductor,
    genre,
    format,
    label,
    catalog_number,
    recording_mode,
    reissue,
    dbx_encoded
)
SELECT
    artist,
    title,
    year,
    COALESCE(NULLIF(TRIM(composer), ''), '---'),
    COALESCE(NULLIF(TRIM(orchestra), ''), '---'),
    COALESCE(NULLIF(TRIM(conductor), ''), '---'),
    genre,
    format,
    COALESCE(NULLIF(TRIM(label), ''), '---'),
    COALESCE(NULLIF(TRIM(catalog_number), ''), '---'),
    UPPER(NULLIF(TRIM(recording_mode), '')),
    UPPER(NULLIF(TRIM(reissue), '')),
    UPPER(NULLIF(TRIM(dbx_encoded), ''))
FROM stg_recordings
WHERE is_valid = 1;
"""


def die(msg):
    print(f"ERROR: {msg}")
    sys.exit(1)


def validate_my_cnf(expected_db: str):
    cnf_path = Path.home() / ".my.cnf"

    if not cnf_path.is_file():
        die(f"Missing .my.cnf at {cnf_path}")

    # Optional metadata check
    db_name = None
    with cnf_path.open() as f:
        for line in f:
            line = line.strip()
            if line.startswith("db="):
                db_name = line.split("=", 1)[1].strip()

    if expected_db and db_name and db_name != expected_db:
        die(f".my.cnf DB mismatch (expected {expected_db}, found {db_name})")


def promote():
    try:
        subprocess.run(
            ["mysql"],
            input=PROMOTE_SQL,
            text=True,
            check=True
        )
    except subprocess.CalledProcessError as e:
        die("Failed to promote staging rows")

    print("Staging rows promoted successfully.")


if __name__ == "__main__":
    db_arg = None
    if len(sys.argv) > 1:
        if sys.argv[1] == "--db" and len(sys.argv) == 3:
            db_arg = sys.argv[2]
        else:
            print("Usage: musica_db_promote.py [--db DATABASE]")
            sys.exit(1)

    validate_my_cnf(db_arg)
    promote()

