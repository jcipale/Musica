#!/opt/Musica/venv/bin/python

# ------------------------------------------------------------
# musica_db_add_recording.py
#
# Interactive tool to add a recording to Musica
# Authentication and database selection via ~/.my.cnf
# ------------------------------------------------------------

import sys
import os
import stat
import configparser
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
        sys.exit(1)


def load_and_validate_my_cnf():
    cnf_path = Path.home() / ".my.cnf"

    if not cnf_path.is_file():
        print(f"ERROR: Missing .my.cnf at {cnf_path}")
        sys.exit(1)

    # Enforce 600 permissions
    st = os.stat(cnf_path)
    if st.st_mode & (stat.S_IRWXG | stat.S_IRWXO):
        print("ERROR: .my.cnf must have permissions 600.")
        sys.exit(1)

    config = configparser.ConfigParser()
    config.read(cnf_path)

    if "client" not in config:
        print("ERROR: .my.cnf missing [client] section.")
        sys.exit(1)

    required = ["user", "password", "host", "database"]
    for key in required:
        if key not in config["client"]:
            print(f"ERROR: .my.cnf missing required key: {key}")
            sys.exit(1)

    return cnf_path


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
    if not val or not val.strip():
        return None
    return val.strip().upper()[0]


def normalize_text(val):
    if not val or not val.strip():
        return None
    return val.strip()


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------
def main():
    enforce_venv()
    cnf_path = load_and_validate_my_cnf()

    # ---- Connect using ~/.my.cnf ----
    try:
        conn = MySQLdb.connect(
            read_default_file=str(cnf_path),
            charset="utf8mb4"
        )
    except MySQLdb.Error as e:
        print(f"\nConnection failed: {e}")
        sys.exit(1)

    print("\nAdd New Recording to Musica")
    print("---------------------------")

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

    composer = orchestra = conductor = None

    if genre == "Symphonic":
        composer  = normalize_text(prompt("Composer: "))
        orchestra = normalize_text(prompt("Orchestra: "))
        conductor = normalize_text(prompt("Conductor: "))

    label   = normalize_text(prompt("Label (optional): ", False))
    catalog = normalize_text(prompt("Catalog Number (optional): ", False))
    mode    = normalize_flag(prompt("Recording Mode [M/S] (optional): ", False))
    reissue = normalize_flag(prompt("Reissue? [Y/N] (optional): ", False))
    dbx     = normalize_flag(prompt("dbx Encoded? [Y = yes, Enter = no]: ", False))

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
        sys.exit(1)

    finally:
        cur.close()
        conn.close()


# ------------------------------------------------------------
if __name__ == "__main__":
    main()

