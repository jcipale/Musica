#!/opt/Musica/venv/bin/python

import mariadb
import getpass
import sys

def prompt(label, required=True):
    val = input(label).strip()
    if required and not val:
        print("Required field missing.")
        sys.exit(1)
    return val or None

def normalize(val):
    if not val:
        return None
    return val.strip().upper()[0]

def main():
    print("\nAdd New Recording to Musica")
    print("---------------------------")

    db_user = prompt("DB User: ")
    db_name = prompt("Database: ")
    db_pass = getpass.getpass("Password: ")

    try:
        conn = mariadb.connect(
            user=db_user,
            password=db_pass,
            database=db_name,
            host="localhost"
        )
    except mariadb.Error as e:
        print(f"Connection failed: {e}")
        sys.exit(1)

    artist  = prompt("Artist: ")
    title   = prompt("Title: ")
    year    = int(prompt("Year (>=1900, <= next year): "))
    genre   = prompt("Genre [Jazz | Rock | Country | Symphonic]: ")
    fmt     = prompt("Format [LP | CD | Cass | RtR]: ")

    label   = prompt("Label (optional): ", False)
    catalog = prompt("Catalog Number (optional): ", False)
    mode    = normalize(prompt("Recording Mode [M/S] (optional): ", False))
    reissue = normalize(prompt("Reissue? [Y/N] (optional): ", False))
    dbx     = normalize(prompt("dbx Encoded? [Y = yes, Enter = no]: ", False))

    sql = """
        INSERT INTO recordings (
            artist, title, year, genre, format,
            label, catalog_number, recording_mode,
            reissue, dbx_encoded
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    try:
        cur = conn.cursor()
        cur.execute(sql, (
            artist, title, year, genre, fmt,
            label, catalog, mode, reissue, dbx
        ))
        conn.commit()
        print("\nRecord inserted successfully.")
    except mariadb.Error as e:
        print(f"\nInsert failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()

