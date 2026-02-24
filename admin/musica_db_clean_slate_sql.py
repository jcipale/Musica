#!/usr/bin/env python3
"""
musica_db_clean_slate.py — Reset Musica single-user SQLite test state.

Default behavior:
- Backup ~/Musica/musica.db to ~/Musica/musica.db.bak.<timestamp>
- Delete ~/Musica/musica.db

Optional:
- --no-backup         : skip backup
- --touch             : recreate empty db file (0 bytes) after delete
- --wipe-logs         : delete ~/Musica/logs/* (non-recursive by default)
- --wipe-imports      : delete ~/Musica/data/imports/* (if present)
- --wipe-exports      : delete ~/Musica/data/exports/* (if present)

Safety:
- Refuses to run as root/sudo.
- Requires explicit --yes to actually perform destructive actions.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path
import shutil


MUSICA_BASE_DIR = Path.home() / "Musica"
DEFAULT_DB = MUSICA_BASE_DIR / "musica.db"


def refuse_root():
    if hasattr(os, "geteuid") and os.geteuid() == 0:
        print("ERROR: Do not run clean-slate as root/sudo.")
        sys.exit(1)


def _rm_contents(dir_path: Path, *, recursive: bool = False) -> tuple[int, int]:
    """
    Remove contents of a directory. Returns (files_deleted, dirs_deleted).
    """
    files_deleted = 0
    dirs_deleted = 0
    if not dir_path.exists():
        return (0, 0)
    if not dir_path.is_dir():
        raise SystemExit(f"ERROR: Not a directory: {dir_path}")

    for p in dir_path.iterdir():
        try:
            if p.is_file() or p.is_symlink():
                p.unlink()
                files_deleted += 1
            elif p.is_dir():
                if recursive:
                    shutil.rmtree(p)
                    dirs_deleted += 1
                else:
                    # non-recursive: refuse to delete subdirs
                    print(f"WARNING: Skipping subdir (use recursive if you ever want that): {p}")
        except PermissionError:
            raise SystemExit(f"ERROR: Permission denied deleting: {p}")
    return (files_deleted, dirs_deleted)


def main() -> None:
    refuse_root()

    ap = argparse.ArgumentParser(description="Reset Musica SQLite test state (clean slate).")
    ap.add_argument("--db-file", default=str(DEFAULT_DB), help="SQLite DB path (default: ~/Musica/musica.db)")
    ap.add_argument("--yes", action="store_true", help="Actually perform deletions (required).")
    ap.add_argument("--no-backup", action="store_true", help="Do not backup DB before deleting.")
    ap.add_argument("--touch", action="store_true", help="Recreate empty DB file after deleting (0 bytes).")

    ap.add_argument("--wipe-logs", action="store_true", help="Delete files in ~/Musica/logs/")
    ap.add_argument("--wipe-imports", action="store_true", help="Delete files in ~/Musica/data/imports/")
    ap.add_argument("--wipe-exports", action="store_true", help="Delete files in ~/Musica/data/exports/")

    args = ap.parse_args()

    db_file = Path(args.db_file).expanduser()

    print("Musica Clean Slate (SQLite)")
    print("---------------------------")
    print("DB file:", db_file)

    if not args.yes:
        print("\nDRY RUN (no changes made). Re-run with --yes to execute.")
        if db_file.exists():
            print("Would delete:", db_file)
            if not args.no_backup:
                ts = time.strftime("%Y%m%d-%H%M%S")
                print("Would backup to:", db_file.with_name(db_file.name + f".bak.{ts}"))
        else:
            print("DB file does not exist; nothing to delete.")
        if args.wipe_logs:
            print("Would wipe logs dir:", MUSICA_BASE_DIR / "logs")
        if args.wipe_imports:
            print("Would wipe imports dir:", MUSICA_BASE_DIR / "data" / "imports")
        if args.wipe_exports:
            print("Would wipe exports dir:", MUSICA_BASE_DIR / "data" / "exports")
        return

    # --- DB backup + delete ---
    if db_file.exists():
        if db_file.is_dir():
            raise SystemExit(f"ERROR: Expected DB file but found directory: {db_file}")

        if not args.no_backup:
            ts = time.strftime("%Y%m%d-%H%M%S")
            bak = db_file.with_name(db_file.name + f".bak.{ts}")
            shutil.copy2(db_file, bak)
            print("Backed up DB to:", bak)

        db_file.unlink()
        print("Deleted DB:", db_file)
    else:
        print("DB file not present; skipping delete.")

    if args.touch:
        db_file.touch(exist_ok=True)
        # enforce owner-only perms on Unix (Windows ignores)
        try:
            os.chmod(db_file, 0o600)
        except Exception:
            pass
        print("Recreated empty DB:", db_file, f"(size={db_file.stat().st_size} bytes)")

    # --- Optional wipes ---
    if args.wipe_logs:
        logs_dir = MUSICA_BASE_DIR / "logs"
        f, d = _rm_contents(logs_dir, recursive=False)
        print(f"Wiped logs: {logs_dir} (files={f}, dirs={d})")

    if args.wipe_imports:
        imp_dir = MUSICA_BASE_DIR / "data" / "imports"
        f, d = _rm_contents(imp_dir, recursive=False)
        print(f"Wiped imports: {imp_dir} (files={f}, dirs={d})")

    if args.wipe_exports:
        exp_dir = MUSICA_BASE_DIR / "data" / "exports"
        f, d = _rm_contents(exp_dir, recursive=False)
        print(f"Wiped exports: {exp_dir} (files={f}, dirs={d})")

    print("OK: Clean slate complete.")


if __name__ == "__main__":
    main()

