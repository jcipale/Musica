#!/opt/Musica/venv/bin/python3
# musica_db_promote.py — Promote valid staging rows to recordings

import subprocess
import sys

DB_NAME = "QA_Musica"


def require_root():
    import os
    if os.geteuid() != 0:
        print("ERROR: Must run as root (sudo).")
        sys.exit(1)


def promote_staging(db_name: str):
    sql = """
    INSERT IGNORE INTO recordings (
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
    cmd = ["mysql", "-u", "root", db_name]

    try:
        subprocess.run(cmd, input=sql, text=True, check=True)
    except subprocess.CalledProcessError as e:
        print("ERROR: Failed to promote staging rows")
        print(e)
        sys.exit(1)

    print("Staging rows promoted successfully.")


if __name__ == "__main__":
    require_root()
    promote_staging(DB_NAME)

