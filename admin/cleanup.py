#!/usr/bin/env python3
"""
cleanup.py — remove backup and temporary files safely
"""

from pathlib import Path

patterns = ["*~", "*.bak", "#*#", "*.tmp"]

print("Cleaning up temporary files...")

for pattern in patterns:
    for path in Path(".").rglob(pattern):
        try:
            path.unlink()
        except Exception:
            # match csh behavior: ignore failures silently
            pass

print("Cleanup complete.")

