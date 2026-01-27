#!/usr/bin/env python3

import mariadb
import getpass
import sys
from pathlib import Path

# --- Prompt for connection info ---
user = input("DB user: ")
db   = input("Database: ")
host = input("Host [localhost]: ") or "localhost"
pwd  = getpass.getpass("Password: ")

sql_file = input("Load SQL file path: ").strip()
sql_path = Path(sql_file)

if not sql_path.is_file():
    print(f"ERROR: File not found: {sql_path}")
    sys.exit(1)

# --- Connect (LOCAL INFILE enabled) ---
conn = mariadb.connect(
    user=user,
    password=pwd,
    host=host,
    database=db,
    local_infile=True
)

cur = conn.cursor()

# --- Execute SQL script ---
with open(sql_path, "r") as f:
    sql = f.read()

for stmt in sql.split(";"):
    stmt = stmt.strip()
    if stmt:
        cur.execute(stmt)

conn.commit()
conn.close()

print("Batch load completed.")

