#!/opt/Musica/venv/bin/python


import mariadb
import getpass
import argparse
import sys
import os
import time
from pathlib import Path

# --------------------------------------------------
# Utilities
# --------------------------------------------------

def die(msg):
    print(f"ERROR: {msg}")
    sys.exit(1)

def connect_db(user, password, database, host="localhost"):
    try:
        return mariadb.connect(
            user=user,
            password=password,
            host=host,
            database=database,
            local_infile=True
        )
    except mariadb.Error as e:
        die(e)

# --------------------------------------------------
# Mode: Run SQL file
# --------------------------------------------------

def run_sql_file(conn, sql_path):
    if not sql_path.is_file():
        die(f"SQL file not found: {sql_path}")

    cur = conn.cursor()
    with open(sql_path, "r") as f:
        sql = f.read()

    for stmt in sql.split(";"):
        stmt = stmt.strip()
        if stmt:
            cur.execute(stmt)

    conn.commit()
    cur.close()
    print("SQL execution completed.")

# --------------------------------------------------
# Mode: Load CSV batch
# --------------------------------------------------

def load_csv_batch(conn, csv_path):
    if not os.path.isfile(csv_path):
        die("CSV file does not exist")

    cur = conn.cursor()

    source_file = os.path.basename(csv_path)
    load_batch_id = int(time.time())

    print("Loading CSV into staging...")

    load_sql = f"""
    LOAD DATA LOCAL INFILE '{csv_path}'
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
    )
    SET
        load_batch_id = {load_batch_id},
        source_file   = '{source_file}';
    """

    try:
        cur.execute(load_sql)
        conn.commit()
    except mariadb.Error as e:
        die(e)

    print("Promoting valid rows into recordings...")

    promote_sql = """
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
        NULLIF(TRIM(composer), ''),
        NULLIF(TRIM(orchestra), ''),
        NULLIF(TRIM(conductor), ''),
        genre,
        format,
        label,
        catalog_number,
        UPPER(NULLIF(TRIM(recording_mode), '')),
        UPPER(NULLIF(TRIM(reissue), '')),
        UPPER(NULLIF(TRIM(dbx_encoded), ''))
    FROM stg_recordings
    WHERE load_batch_id = %s
      AND is_valid = 1;
    """

    try:
        cur.execute(promote_sql, (load_batch_id,))
        conn.commit()
    except mariadb.Error as e:
        die(e)

    cur.execute(
        "SELECT COUNT(*) FROM stg_recordings WHERE load_batch_id = %s",
        (load_batch_id,)
    )
    staged = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM recordings")
    total = cur.fetchone()[0]

    print(f"Batch ID: {load_batch_id}")
    print(f"Staged rows: {staged}")
    print(f"Total recordings: {total}")

    cur.close()

# --------------------------------------------------
# Main
# --------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Musica DB Batch Utility")
    parser.add_argument("--run-sql", help="Execute SQL file", type=Path)
    parser.add_argument("--load-csv", help="Load CSV into Musica", type=str)
    parser.add_argument("--host", default="localhost")

    args = parser.parse_args()

    if not args.run_sql and not args.load_csv:
        die("Must specify --run-sql or --load-csv")

    user = input("DB user: ").strip()
    db   = input("Database: ").strip()
    pwd  = getpass.getpass("Password: ")

    conn = connect_db(user, pwd, db, args.host)

    if args.run_sql:
        run_sql_file(conn, args.run_sql)

    if args.load_csv:
        load_csv_batch(conn, args.load_csv)

    conn.close()

if __name__ == "__main__":
    main()

