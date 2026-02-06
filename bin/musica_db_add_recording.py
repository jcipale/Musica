#!/opt/Musica/venv/bin/python

# ------------------------------------------------------------
# musica_db_add_recording.py
#
# Interactive tool to add a recording to Musica
#
# Assumptions:
#   - Musica venv exists (PEP 668)
#   - Database already provisioned
#   - User has INSERT privileges
# ------------------------------------------------------------

import sys
import getpass
from datetime import datetime
from pathlib import Path

import MySQLdb

# ------------------------------------------------------------
# Safety
# ------------------------------------------------------------
def enforce_venv():
    expected = Path("/opt/Musica/venv/bin/python")
    if Path(sys.executable) != expected:
        print("ERROR: This script must be run using the Musica venv.")
        print(f"Expected: {expected}")
        print(f"Running : {sys.executable}")
        sys.exit(1)

# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------
def prompt(label, required=True):
    val = input(label).strip()
    if required and not val:
        print("Required field missing.")
        sys.exit(1)
    return val if val else None

def normalize_flag(val):
    """
    Normalize single-character flags.
    Empty input becomes NULL.
    """
    if not val or not val.strip():
        return None
    return val.strip().upper()[0]

def normalize_text(val):
    """
    Normalize optional text fields.
    Empty -> NULL
    """
    if not val or not val.strip():
        return None
    return val.strip()

# ------------------------------------------------------------
# Main
# ------------------------------------------------------------
def main():
    enforce_venv()

    print("\nAdd New Recording to Musica")
    print("---------------------------")

    # ---- DB Credentials ----
    db_user = prompt("DB User: ")
    db_name = prompt("Database: ")
    db_pass = getpass.getpass("Password: ")

    # ---- Connect ----
    try:
        conn = MySQLdb.connect(
            user=db_user,
            passwd=db_pass,
            db=db_name,
            host="localhost",
            charset="utf8mb4"
        )
    except MySQLdb.Error as e:
        print(f"\nConnection failed: {e}")
        sys.exit(1)

    # ---- Core fields ----
    artist = prompt("Artist: ")
    title  = prompt("Title: ")

    try:
        year = int(prompt("Year (>=1900, <= next year): "))
    except ValueError:
        print("Year must be numeric.")
        sys.exit(1)

    max_year = datetime.now().year + 1
    if year < 1900 or year > max_year:
        print("Year out of valid range.")
        sys.exit(1)

    genre = prompt(
        "Genre [Jazz | Rock | Country | Symphonic]: "
    ).strip().capitalize()

    fmt = prompt(
        "Format [LP | CD | Cass | RTR | 78 | 4T | 8T]: "
    ).strip().upper()

    # ---- Genre-aware classical fields ----
    composer = orchestra = conductor = None

    if genre == "Symphonic":
        composer  = normalize_text(prompt("Composer: "))
        orchestra = normalize_text(prompt("Orchestra: "))
        conductor = normalize_text(prompt("Conductor: "))

    # ---- Optional metadata ----
    label   = normalize_text(prompt("Label (optional): ", False))
    catalog = normalize_text(prompt("Catalog Number (optional): ", False))

    mode    = normalize_flag(prompt("Recording Mode [M/S] (optional): ", False))
    reissue = normalize_flag(prompt("Reissue? [Y/N] (optional): ", False))
    dbx     = normalize_flag(prompt("dbx Encoded? [Y = yes, Enter = no]: ", False))

    # ---- SQL ----
    sql = """
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
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    # ---- Execute ----
    try:
        cur = conn.cursor()
        cur.execute(sql, (
            artist,
            title,
            year,
            composer,
            orchestra,
            conductor,
            genre,
            fmt,
            label,
            catalog,
            mode,
            reissue,
            dbx
        ))
        conn.commit()
        print("\nRecord inserted successfully.")

    except MySQLdb.Error as e:
        conn.rollback()
        print(f"\nInsert failed: {e}")

    finally:
        cur.close()
        conn.close()

# ------------------------------------------------------------
if __name__ == "__main__":
    main()

