#!/usr/bin/env python3

import mariadb
import getpass
import os
import sys
import time

def die(msg):
    print(f"ERROR: {msg}")
    sys.exit(1)

# -----------------------------
# Prompt for connection info
# -----------------------------
db_user = input("DB user: ").strip()
db_name = input("Database name: ").strip()
db_pass = getpass.getpass("DB password: ")

csv_path = input("Path to CSV file: ").strip()
if not os.path.isfile(csv_path):
    die("CSV file does not exist")

source_file = os.path.basename(csv_path)
load_batch_id = int(time.time())

# -----------------------------
# Connect
# -----------------------------
try:
    conn = mariadb.connect(
        user=db_user,
        password=db_pass,
        database=db_name,
        local_infile=True
    )
except mariadb.Error as e:
    die(e)

cur = conn.cursor()

# -----------------------------
# Step 1: Load into staging
# -----------------------------
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

# -----------------------------
# Step 2: Promote into recordings
# -----------------------------
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

# -----------------------------
# Summary
# -----------------------------
cur.execute(
    "SELECT COUNT(*) FROM stg_recordings WHERE load_batch_id = %s",
    (load_batch_id,)
)
staged = cur.fetchone()[0]

cur.execute(
    "SELECT COUNT(*) FROM recordings"
)
total = cur.fetchone()[0]

print(f"Batch ID: {load_batch_id}")
print(f"Staged rows: {staged}")
print(f"Total recordings: {total}")

cur.close()
conn.close()

