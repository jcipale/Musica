#!/opt/Musica/venv/bin/python

"""
musica_db_query.py
Execute an ad-hoc SQL query and print results.
"""

import sys
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
    if len(sys.argv) < 2:
        print(f'Usage: {sys.argv[0]} "SQL_QUERY"')
        sys.exit(1)

    query = " ".join(sys.argv[1:])

    base_dir = Path(__file__).resolve().parent.parent
    cfg_path = base_dir / "config" / "musica.conf"

    if not cfg_path.is_file():
        die(f"Missing config: {cfg_path}")

    cfg = load_config(cfg_path)
    conn = connect_db(cfg)
    cur = conn.cursor()

    try:
        cur.execute(query)
        if cur.description:
            cols = [d[0] for d in cur.description]
            print("\t".join(cols))
            for row in cur.fetchall():
                print("\t".join("" if v is None else str(v) for v in row))
        else:
            conn.commit()
            print(f"{cur.rowcount} rows affected.")
    except MySQLdb.Error as e:
        die(f"Query failed: {e}")
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()

