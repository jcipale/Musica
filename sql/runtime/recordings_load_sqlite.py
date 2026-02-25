#!/usr/bin/env python3
"""
recordings_load.py — Load a CSV file into stg_recordings (SQLite)

Replaces MariaDB LOAD DATA LOCAL INFILE.

Behavior:
- Reads CSV (comma-separated, optional quotes)
- Skips header row
- Inserts into stg_recordings
- Sets:
  - load_batch_id (required, from arg)
  - source_file (basename of csv path)
  - is_valid = 1
  - validation_errors = NULL
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
import sqlite3


DB_FILE = Path.home() / "Musica" / "musica.db"


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_FILE))
    conn.execute("PRAGMA foreign_keys=ON;")
    conn.execute("PRAGMA busy_timeout=5000;")
    return conn


def main() -> None:
    ap = argparse.ArgumentParser(description="Load recordings CSV into stg_recordings (SQLite)")
    ap.add_argument("csv_file", help="Path to recordings CSV")
    ap.add_argument("--batch-id", type=int, required=True, help="load_batch_id to stamp on rows")
    args = ap.parse_args()

    csv_path = Path(args.csv_file).expanduser()
    if not csv_path.is_file():
        raise SystemExit(f"ERROR: CSV file not found: {csv_path}")

    source_file = csv_path.name

    insert_sql = """
    INSERT INTO stg_recordings (
        load_batch_id,
        source_file,
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
        dbx_encoded,
        is_valid,
        validation_errors
    ) VALUES (
        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, NULL
    )
    """

    rows = []
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f, delimiter=",", quotechar='"')
        # IGNORE 1 LINES
        next(reader, None)

        for line_num, cols in enumerate(reader, start=2):
            if not cols:
                continue
            # Expecting 13 columns per your LOAD DATA list
            if len(cols) != 13:
                raise SystemExit(
                    f"ERROR: {csv_path}:{line_num}: expected 13 columns, got {len(cols)} -> {cols}"
                )

            (
                artist,
                title,
                year,
                orchestra,
                conductor,
                genre,
                fmt,
                label,
                catalog_number,
                reissue,
                recording_mode,
                dbx_encoded,
                # NOTE: your list includes these 12 after year? actually list is 12 after year total 13
            ) = cols

            # SQLite will store year as INTEGER if we pass int; validate lightly here
            try:
                year_i = int(year)
            except ValueError:
                # keep raw, let validation step mark invalid later if you prefer
                raise SystemExit(f"ERROR: {csv_path}:{line_num}: year is not an integer: {year!r}")

            rows.append((
                args.batch_id,
                source_file,
                artist,
                title,
                year_i,
                orchestra,
                conductor,
                genre,
                fmt,
                label,
                catalog_number,
                reissue,
                recording_mode,
                dbx_encoded,
            ))

    if not rows:
        print("No data rows found (after header). Nothing to load.")
        return

    conn = connect()
    try:
        with conn:  # transaction
            conn.executemany(insert_sql, rows)
        print(f"OK: Loaded {len(rows)} rows into stg_recordings (batch_id={args.batch_id})")
    finally:
        conn.close()


if __name__ == "__main__":
    main()

