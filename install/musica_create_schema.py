#!/usr/bin/env python3
"""
Musica Schema Creation Utility
Compatible with MariaDB, MySQL, SQLite
"""

import os
import sys
import sqlite3
import subprocess
import shutil

# ------------------------------------------------------------
# Load configuration
# ------------------------------------------------------------
def load_config():
    candidates = [
        os.path.join(os.getcwd(), "config", "musica.conf"),
        os.path.join(os.path.dirname(__file__), "..", "config", "musica.conf"),
    ]

    for cfg in candidates:
        if os.path.isfile(cfg):
            with open(cfg) as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        k, v = line.split("=", 1)
                        os.environ[k.strip()] = v.strip().strip('"')
            return cfg

    print("ERROR: musica.conf not found")
    sys.exit(1)


load_config()

# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------
def cmd_exists(cmd):
    return shutil.which(cmd) is not None


def run(cmd, *, input_sql=None):
    p = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    out, err = p.communicate(input_sql)
    return p.returncode, out, err


# ------------------------------------------------------------
# Schema SQL (canonical)
# ------------------------------------------------------------
SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS ArtistCatalog (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    ArtistLast      VARCHAR(128) NOT NULL,
    ArtistFirst     VARCHAR(128),
    Title           VARCHAR(256) NOT NULL,
    Orchestra       VARCHAR(256),
    Conductor       VARCHAR(128),
    Year            INTEGER,
    Genre           VARCHAR(64),
    Format          VARCHAR(32),
    Label           VARCHAR(128),
    CatalogNumber   VARCHAR(64),
    Reissue         CHAR(1) DEFAULT 'N',
    Mode            CHAR(1) DEFAULT 'S',
    DBX             CHAR(1) DEFAULT 'N'
);

CREATE INDEX IF NOT EXISTS idx_year_artist
    ON ArtistCatalog (Year, ArtistLast);
"""

# ------------------------------------------------------------
# Detect DB backend
# ------------------------------------------------------------
db_type = os.environ.get("MUSICA_DB_TYPE", "").lower()
db_name = os.environ.get("MUSICA_DB_NAME", "Musica")

print("\n🎼 Musica Schema Creation")
print("------------------------")
print(f"Database type: {db_type}")
print(f"Database name: {db_name}\n")

# ------------------------------------------------------------
# MariaDB / MySQL
# ------------------------------------------------------------
if db_type in ("mariadb", "mysql"):
    client = "mariadb" if cmd_exists("mariadb") else "mysql"

    print(f"Using client: {client}")

    # Create database if needed
    rc, _, err = run(
        [client, "-u", "root", "-e", f"CREATE DATABASE IF NOT EXISTS {db_name};"]
    )
    if rc != 0:
        print("ERROR: Failed to create database")
        print(err)
        sys.exit(1)

    # Load schema
    rc, _, err = run(
        [client, "-u", "root", db_name],
        input_sql=SCHEMA_SQL
    )
    if rc != 0:
        print("ERROR: Failed to load schema")
        print(err)
        sys.exit(1)

# ------------------------------------------------------------
# SQLite
# ------------------------------------------------------------
elif db_type == "sqlite3":
    sqlite_path = os.environ.get("MUSICA_SQLITE_DB", "musica.db")
    print(f"Using SQLite file: {sqlite_path}")

    try:
        conn = sqlite3.connect(sqlite_path)
        conn.executescript(SCHEMA_SQL)
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        print(f"ERROR: SQLite schema creation failed: {e}")
        sys.exit(1)

else:
    print("ERROR: Unsupported or undefined MUSICA_DB_TYPE")
    sys.exit(1)

print("\nSchema created and verified successfully.")
sys.exit(0)

