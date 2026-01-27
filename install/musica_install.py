#!/usr/bin/env python3
"""
Musica – Installation / Upgrade Script
Phase 2 Requirements:
  * Create /opt/Musica if missing
  * Copy project directories into /opt/Musica
  * Compare VERSION file with existing installation
  * Skip or upgrade based on version
"""

import os
import shutil
import sys
from pathlib import Path

# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------
APP_ROOT = Path("/opt/Musica")
SRC_ROOT = Path.cwd()

print("-------------------------------------------------------------")
print("        Musica – Installation / Upgrade Script")
print("                 (Python, Phase 2)")
print("-------------------------------------------------------------")
print("")

# ------------------------------------------------------------
# Root permission check
# ------------------------------------------------------------
if os.geteuid() != 0:
    print("ERROR: Root access is required to install into /opt.")
    print("Run again using:")
    print(f"    sudo {sys.argv[0]}")
    sys.exit(1)

# ------------------------------------------------------------
# Validate source VERSION
# ------------------------------------------------------------
src_version_file = SRC_ROOT / "VERSION"
if not src_version_file.is_file():
    print("ERROR: VERSION file missing in the source directory:")
    print(f"       {SRC_ROOT}")
    print("Aborting installation.")
    sys.exit(1)

new_version = src_version_file.read_text().strip()
print(f"Source VERSION: {new_version}")

# ------------------------------------------------------------
# Determine installation state
# ------------------------------------------------------------
install_state = "new"
old_version = None

if APP_ROOT.is_dir():
    print(f"Existing installation detected in {APP_ROOT}")

    installed_version_file = APP_ROOT / "VERSION"
    if installed_version_file.is_file():
        old_version = installed_version_file.read_text().strip()
        print(f"Installed VERSION: {old_version}")
        install_state = "upgrade"
    else:
        print("WARNING: No VERSION file found in existing installation.")
        install_state = "upgrade"
else:
    print("No installation found. Creating new installation.")

# ------------------------------------------------------------
# Version comparison (simple string compare)
# ------------------------------------------------------------
if install_state == "upgrade":
    if old_version == new_version:
        print("-------------------------------------------------------------")
        print(f"Musica {old_version} is already installed.")
        print("Same version detected. Installation skipped.")
        print("-------------------------------------------------------------")
        sys.exit(0)

    if old_version and old_version > new_version:
        print("-------------------------------------------------------------")
        print(
            f"WARNING: Installed version ({old_version}) "
            f"is NEWER than release ({new_version})."
        )
        print("Upgrade not performed.")
        print("-------------------------------------------------------------")
        sys.exit(1)

    if old_version:
        print(f"Upgrade allowed: {old_version} -> {new_version}")

# ------------------------------------------------------------
# Create directory tree
# ------------------------------------------------------------
def makedir(path: Path):
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        print(f"Created: {path}")

makedir(APP_ROOT)

dirs = [
    "admin", "archive", "bin", "config", "data", "db", "docs",
    "install", "RELEASES", "sql", "tests", "web",
    "data/archive", "data/exports", "data/imports",
    "web/api", "web/css", "web/html", "web/js",
    "Muscia_dev", "Muscia_dev/maint_scripts",
    "Muscia_dev/op_scripts", "Muscia_dev/UI_scripts",
    "logs",
]

for d in dirs:
    makedir(APP_ROOT / d)

# ------------------------------------------------------------
# Copy contents
# ------------------------------------------------------------
print("")
print("Copying project directories into installation target...")

copy_dirs = [
    "admin", "archive", "bin", "config", "data",
    "db", "docs", "install", "RELEASES", "sql",
    "tests", "web",
]

for d in copy_dirs:
    src_dir = SRC_ROOT / d
    dest_dir = APP_ROOT / d

    if src_dir.is_dir():
        print(f"Copying directory: {d}")
        for item in src_dir.iterdir():
            dest = dest_dir / item.name
            if item.is_dir():
                shutil.copytree(item, dest, dirs_exist_ok=True)
            else:
                shutil.copy2(item, dest)

# ------------------------------------------------------------
# Copy VERSION
# ------------------------------------------------------------
print("Copying VERSION file...")
shutil.copy2(src_version_file, APP_ROOT / "VERSION")

# ------------------------------------------------------------
# Completion
# ------------------------------------------------------------
print("")
print("-------------------------------------------------------------")
if install_state == "new":
    print(f"Musica successfully installed. Version: {new_version}")
else:
    print(f"Musica successfully upgraded to Version: {new_version}")
print("-------------------------------------------------------------")

sys.exit(0)

