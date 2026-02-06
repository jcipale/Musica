#!/opt/Musica/venv/bin/python

"""
musica_db_export.py
Export recordings to CSV or plain text.
Refactored to DB-API (MySQLdb).
"""

import csv
import sys
import os
import getpass
from pathlib import Path
import MySQLdb


def die(msg, code=1):
    print(f"ERROR: {msg}")
    sys.exit(code)


def load_config(path: Path):
    config = {}
    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            config[k.strip()] = v.strip().strip('"').strip("'")
    return config


def connect_db(cfg):
    user = cfg.get("MUSICA_DB_USER") or input("DB user: ").strip()
    db   = cfg.get("MUSICA_DB_NAME") or input("Database: ").strip()
    pwd  = cfg.get("MUSICA_DB_PASS") or getpass.getpass("Password: ")

    try:
        return MySQLdb.connect(
            user=user,
            passwd=pwd,
            db=db,
            host=cfg.get("MUSICA_DB_HOST", "localhost"),
            charset="utf8mb4"
        )
    except MySQLdb.Error as e:
        die(f"DB connection failed: {e}")


def main():
    base_dir = Path(__file__).resolve().parent.parent
    cfg_path = base_dir / "config" / "musica.conf"

    if not cfg_path.is_file():
        die(f"Missing config: {cfg_path}")

    cfg = load_config(cfg_path)

    # output path
    if len(sys.argv) >= 2:
        outpath = Path(sys.argv[1])
    else:
        outpath = Path(cfg["MUSICA_EXPORT_DIR"]) / cfg["MUSICA_DEFAULT_EXPORT"]

    fmt = sys.argv[2].lower() if len(sys.argv) >= 3 else "csv"

    conn = connect_db(cfg)
    cur = conn.cursor()

    sql = """
        SELECT
            artist,
            title,
            orchestra,
            conductor,
            year,
            genre,
            format,
            label,
            catalog_number,
            reissue,
            recording_mode,
            dbx_encoded
        FROM recordings
        ORDER BY year, artist
    """

    try:
        cur.execute(sql)
        rows = cur.fetchall()
    except MySQLdb.Error as e:
        die(f"Query failed: {e}")

    with outpath.open("w", newline="", encoding="utf-8") as f:
        if fmt == "csv":
            writer = csv.writer(f)
            writer.writerow([d[0] for d in cur.description])
            writer.writerows(rows)
        else:
            for row in rows:
                f.write("\t".join("" if v is None else str(v) for v in row) + "\n")

    cur.close()
    conn.close()

    print(f"Export written to: {outpath}")


if __name__ == "__main__":
    main()

