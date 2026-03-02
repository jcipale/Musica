#!/usr/bin/env python3
"""
musica_db_batch_load_sqlite.py

Musica-native SQLite batch loader.

Hard rules:
- DB file:        ~/Musica/musica.db
- Import folder:  ~/Musica/data/imports/
- User supplies:  filename only (no paths)
- CSV delimiter:  ';' (required; enforced)
- Single transaction
- No schema logic changes
"""

from __future__ import annotations

import argparse
import csv
import os
import sqlite3
import sys
import time
from typing import Dict, List, Tuple


# Canonical paths (per-user)
MUSICA_HOME = os.path.expanduser("~/Musica")
DB_FILE = os.path.join(MUSICA_HOME, "musica.db")
IMPORT_DIR = os.path.join(MUSICA_HOME, "data", "imports")

DEFAULT_TABLE = "recordings"

# Deterministic CSV header -> DB column mapping
# (also accepts headers that already match DB column names)
CSV_TO_DB_COL = {
    "Artist": "artist",
    "Title": "title",
    "Year": "year",
    "Composer": "composer",
    "Orchestra": "orchestra",
    "Conductor": "conductor",
    "Genre": "genre",
    "Format": "format",
    "Label": "label",
    "Catalog Number": "catalog_number",
    "CatalogNumber": "catalog_number",
    "Catalog_Number": "catalog_number",
    "Catalog#": "catalog_number",
    "Recording Mode": "recording_mode",
    "Mode": "recording_mode",
    "Reissue": "reissue",
    "DBX": "dbx_encoded",
    "DBX Encoded": "dbx_encoded",
    "DBX_encoded": "dbx_encoded",
}


def die(msg: str, code: int = 1) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    raise SystemExit(code)


def resolve_import_file(filename: str) -> str:
    if os.path.sep in filename or (os.path.altsep and os.path.altsep in filename):
        die(f"Provide filename only (no path): {filename}")
    return os.path.abspath(os.path.join(IMPORT_DIR, filename))


def table_exists(conn: sqlite3.Connection, table: str) -> bool:
    cur = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=? LIMIT 1",
        (table,),
    )
    return cur.fetchone() is not None


def fetch_table_columns(conn: sqlite3.Connection, table: str) -> List[str]:
    cur = conn.execute(f"PRAGMA table_info({table})")
    return [r[1] for r in cur.fetchall()]


def count_rows(conn: sqlite3.Connection, table: str) -> int:
    cur = conn.execute(f"SELECT COUNT(*) FROM {table}")
    row = cur.fetchone()
    return int(row[0]) if row else 0


def build_insert_sql(table: str, cols: List[str]) -> str:
    col_list = ", ".join(cols)
    placeholders = ", ".join(["?"] * len(cols))
    return f"INSERT INTO {table} ({col_list}) VALUES ({placeholders})"


def map_headers_to_db(raw_headers: List[str], table_cols: List[str]) -> Tuple[List[str], Dict[str, str]]:
    """
    Returns:
      - insert_cols: list of DB columns to insert (in CSV order)
      - db_to_csv: mapping DB column -> original CSV header key
    Rules:
      - If a CSV header matches a DB column exactly, use it.
      - Else, try CSV_TO_DB_COL mapping.
      - Ignore unknown headers.
      - Result columns are restricted to columns present in the DB table.
    """
    insert_cols: List[str] = []
    db_to_csv: Dict[str, str] = {}

    for h in raw_headers:
        if h is None:
            continue
        h2 = h.strip()
        if not h2:
            continue

        # direct match first
        if h2 in table_cols:
            db_col = h2
        else:
            db_col = CSV_TO_DB_COL.get(h2)

        if db_col and db_col in table_cols:
            # preserve CSV order; do not duplicate
            if db_col not in db_to_csv:
                insert_cols.append(db_col)
                db_to_csv[db_col] = h2

    return insert_cols, db_to_csv


def row_to_values(row: Dict[str, str], insert_cols: List[str], db_to_csv: Dict[str, str]) -> Tuple[object, ...]:
    vals: List[object] = []
    for db_col in insert_cols:
        csv_key = db_to_csv[db_col]
        v = row.get(csv_key, "")
        v = v.strip() if v is not None else ""
        vals.append(None if v == "" else v)
    return tuple(vals)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("filename", help="CSV filename located in ~/Musica/data/imports/")
    ap.add_argument("--table", default=DEFAULT_TABLE, help=f"Target table (default: {DEFAULT_TABLE})")
    ap.add_argument("--chunk", type=int, default=1000, help="Insert chunk size (default: 1000)")
    ap.add_argument("--dry-run", action="store_true", help="Parse/validate only; no inserts")
    ap.add_argument("--fast", action="store_true", help="Session-only speed pragmas (WAL + synchronous=NORMAL)")
    ap.add_argument(
        "--strict-columns",
        action="store_true",
        help="Fail if CSV contains any header that cannot be mapped to a DB column",
    )
    args = ap.parse_args()

    csv_path = resolve_import_file(args.filename)
    table = args.table

    if not os.path.isfile(DB_FILE):
        die(f"DB file not found: {DB_FILE}")
    if not os.path.isdir(IMPORT_DIR):
        die(f"Import directory missing: {IMPORT_DIR}")
    if not os.path.isfile(csv_path):
        die(f"CSV file not found: {csv_path}")

    print("Musica SQLite Batch Load")
    print("-----------------------")
    print(f"DB file   : {DB_FILE}")
    print(f"Import dir: {IMPORT_DIR}")
    print(f"CSV file  : {csv_path}")
    print(f"Table     : {table}")
    print(f"Chunk     : {args.chunk}")
    if args.dry_run:
        print("Mode      : DRY RUN (no inserts)")
    if args.fast:
        print("Pragmas   : FAST (session-only)")

    conn = sqlite3.connect(DB_FILE)
    try:
        conn.execute("PRAGMA foreign_keys = ON;")

        if args.fast:
            conn.execute("PRAGMA journal_mode = WAL;")
            conn.execute("PRAGMA synchronous = NORMAL;")
            conn.execute("PRAGMA temp_store = MEMORY;")

        if not table_exists(conn, table):
            die(f"Target table does not exist: {table}")

        table_cols = fetch_table_columns(conn, table)
        if not table_cols:
            die(f"Could not read columns for table: {table}")

        before_rows = count_rows(conn, table)

        with open(csv_path, "r", newline="", encoding="utf-8") as f:
            # Enforce ';' delimiter (fail fast)
            header_line = f.readline()
            if ";" not in header_line:
                die("CSV delimiter check failed: expected ';' in header row")
            f.seek(0)

            reader = csv.DictReader(f, delimiter=";")
            if reader.fieldnames is None:
                die("CSV missing header row")

            raw_headers = [h.strip() if h is not None else "" for h in reader.fieldnames]
            insert_cols, db_to_csv = map_headers_to_db(raw_headers, table_cols)

            if args.strict_columns:
                unknown = []
                for h in raw_headers:
                    if not h:
                        continue
                    if h in table_cols:
                        continue
                    if h not in CSV_TO_DB_COL:
                        unknown.append(h)
                if unknown:
                    die(f"Unmapped CSV headers (strict): {unknown}")

            if not insert_cols:
                die("No matching columns between CSV and table")

            insert_sql = build_insert_sql(table, insert_cols)

            total_read = 0
            total_attempted = 0
            buf: List[Tuple[object, ...]] = []

            t0 = time.perf_counter()

            if not args.dry_run:
                conn.execute("BEGIN;")

            for row in reader:
                total_read += 1
                buf.append(row_to_values(row, insert_cols, db_to_csv))

                if len(buf) >= args.chunk:
                    if not args.dry_run:
                        conn.executemany(insert_sql, buf)
                        total_attempted += len(buf)
                    buf.clear()

            if buf:
                if not args.dry_run:
                    conn.executemany(insert_sql, buf)
                    total_attempted += len(buf)
                buf.clear()

            if not args.dry_run:
                conn.execute("COMMIT;")

            elapsed = time.perf_counter() - t0

        after_rows = count_rows(conn, table) if not args.dry_run else before_rows
        inserted_effective = after_rows - before_rows if not args.dry_run else 0

        print()
        print("Results")
        print("-------")
        print(f"Rows before : {before_rows}")
        print(f"Rows after  : {after_rows}" if not args.dry_run else "Rows after  : (dry-run)")
        print(f"CSV rows    : {total_read}")
        if not args.dry_run:
            print(f"Inserted    : {inserted_effective}")
            print(f"Elapsed sec : {elapsed:.6f}")
            print(f"Rows/sec    : {(inserted_effective / elapsed):.2f}" if elapsed > 0 else "Rows/sec    : n/a")

    except sqlite3.IntegrityError as e:
        try:
            conn.execute("ROLLBACK;")
        except Exception:
            pass
        die(f"insert failed (integrity): {e}")
    except sqlite3.OperationalError as e:
        try:
            conn.execute("ROLLBACK;")
        except Exception:
            pass
        die(f"insert failed (operational): {e}")
    finally:
        conn.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
