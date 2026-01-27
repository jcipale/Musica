#!/usr/bin/env python3
"""
musica_db_cleanup.py
Maintenance utility for Musica data directories.
Translated from musica_db_cleanup.csh
"""

import sys
import os
import subprocess
from pathlib import Path
from datetime import datetime, timedelta


def main():
    print("Musica Database Cleanup Utility")
    print("----------------------------------------")

    # ------------------------------------------------------------------
    # Required environment variables (set via musica.conf by caller)
    # ------------------------------------------------------------------
    required_env = [
        "MUSICA_DATA_DIR",
        "MUSICA_IMPORT_DIR",
        "MUSICA_EXPORT_DIR",
        "MUSICA_IMPORT_ARCHIVE_DIR",
    ]

    missing = [v for v in required_env if v not in os.environ]
    if missing:
        print(f"ERROR: Missing required environment variables: {', '.join(missing)}")
        sys.exit(1)

    data_dir = Path(os.environ["MUSICA_DATA_DIR"])
    import_dir = Path(os.environ["MUSICA_IMPORT_DIR"])
    export_dir = Path(os.environ["MUSICA_EXPORT_DIR"])
    archive_dir = Path(os.environ["MUSICA_IMPORT_ARCHIVE_DIR"])

    # Retention period (days)
    retention_days = 14

    print(f"Retention period: {retention_days} days")
    print(f"Imports directory: {import_dir}")
    print(f"Exports directory: {export_dir}")

    if not archive_dir.is_dir():
        print(f"ERROR: Import archive directory not found: {archive_dir}")
        sys.exit(1)

    print(f"Archive directory: {archive_dir} (preserved)")
    print("")

    # ------------------------------------------------------------------
    # Confirmation
    # ------------------------------------------------------------------
    ans = input("Proceed with cleanup? (y/n): ").strip()
    if ans.lower() != "y":
        print("Cleanup cancelled.")
        sys.exit(0)

    # ------------------------------------------------------------------
    # Cleanup logic (mtime-based deletion)
    # Matches: find -type f -mtime +N -delete
    # ------------------------------------------------------------------
    cutoff = datetime.now() - timedelta(days=retention_days)

    for directory in (import_dir, export_dir):
        if directory.is_dir():
            print(f"Cleaning {directory} ...")
            for root, _, files in os.walk(directory):
                for name in files:
                    path = Path(root) / name
                    try:
                        mtime = datetime.fromtimestamp(path.stat().st_mtime)
                        if mtime < cutoff:
                            print(path)
                            path.unlink()
                    except Exception as e:
                        print(f"WARNING: Failed to remove {path}: {e}")
        else:
            print(f"Directory not found: {directory}")

    print("")
    print("Cleanup complete. Archive directory preserved.")
    sys.exit(0)


if __name__ == "__main__":
    main()

