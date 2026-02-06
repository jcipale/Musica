#!/usr/bin/env python3
"""
Musica – Installation / Upgrade Script (Python)
Ported from install.csh
"""

import os
import sys
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------
APP_ROOT = Path("/opt/Musica")
PKG_ROOT = Path("/opt")
SRC_ROOT = Path.cwd()
TARBALL_NAME = "musica.tar"

PROJECT_DIRS = [
    "admin", "archive", "bin", "config", "data", "db", "docs",
    "install", "RELEASES", "sql", "tests", "web", "logs"
]

SUBDIRS = [
    "data/archive", "data/exports", "data/imports",
    "web/api", "web/css", "web/html", "web/js"
]

# ------------------------------------------------------------
# Utility functions
# ------------------------------------------------------------
def die(msg, code=1):
    print(f"ERROR: {msg}")
    sys.exit(code)

def run(cmd):
    return subprocess.run(cmd, shell=True, check=False)

def ensure_root():
    if os.geteuid() != 0:
        die(f"Root access required. Use: sudo {sys.argv[0]}")

def read_version(path):
    try:
        return path.read_text().strip()
    except FileNotFoundError:
        return ""

def mkdir(path):
    path.mkdir(parents=True, exist_ok=True)

def log(msg):
    print(msg)
    with LOG_FILE.open("a") as f:
        f.write(msg + "\n")

# ------------------------------------------------------------
# Start installer
# ------------------------------------------------------------
print("-------------------------------------------------------------")
print("           Musica – Installation / Upgrade Script")
print("-------------------------------------------------------------\n")

ensure_root()

# ---------- Verify VERSION ----------
src_version_file = SRC_ROOT / "VERSION"
if not src_version_file.exists():
    die("VERSION file missing in source directory.")

NEW_VERSION = read_version(src_version_file)
print(f"Source VERSION: {NEW_VERSION}")

# ---------- Logging setup ----------
mkdir(APP_ROOT)
mkdir(APP_ROOT / "logs")

TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_DIR = APP_ROOT / "logs"
LOG_FILE = LOG_DIR / f"install_{TIMESTAMP}.log"

log(f"Installer started at {TIMESTAMP}")
log(f"Source: {SRC_ROOT}")
log(f"Target: {APP_ROOT}")
log(f"Source VERSION: {NEW_VERSION}")

# ---------- Detect installed version ----------
INSTALL_STATE = "new"
OLD_VERSION = ""

if APP_ROOT.exists():
    log(f"Existing directory detected at {APP_ROOT}")
    old_version_file = APP_ROOT / "VERSION"
    if old_version_file.exists():
        OLD_VERSION = read_version(old_version_file)
        log(f"Installed VERSION: {OLD_VERSION}")
        INSTALL_STATE = "upgrade"
    else:
        log("No VERSION file found in existing install. Treating as new install.")

# ---------- Identical version handling ----------
if INSTALL_STATE == "upgrade" and OLD_VERSION == NEW_VERSION and OLD_VERSION:
    log(f"Versions match ({NEW_VERSION}). User must confirm overwrite.")
    ans = input("Overwrite existing installation? (y/n): ").strip().lower()
    if ans != "y":
        log("User aborted due to identical version.")
        sys.exit(0)
    log("User approved overwrite.")

# ---------- Installed version newer ----------
if INSTALL_STATE == "upgrade" and OLD_VERSION and OLD_VERSION > NEW_VERSION:
    die(f"Installed version ({OLD_VERSION}) is newer than release ({NEW_VERSION}). Aborting.")

# ---------- Create directory tree ----------
for d in PROJECT_DIRS:
    target = APP_ROOT / d
    if not target.exists():
        mkdir(target)
        log(f"Created: {target}")

for sd in SUBDIRS:
    target = APP_ROOT / sd
    if not target.exists():
        mkdir(target)
        log(f"Created: {target}")

# ---------- Copy project directories + delete source ----------
log("Copying project directories...")

for d in PROJECT_DIRS:
    src = SRC_ROOT / d
    dst = APP_ROOT / d
    if src.exists() and src.is_dir():
        log(f"Copying: {d}")
        for item in src.iterdir():
            if item.is_dir():
                shutil.copytree(item, dst / item.name, dirs_exist_ok=True)
            else:
                shutil.copy2(item, dst)
        log(f"Removing source: {src}")
        shutil.rmtree(src)

# ---------- Install uninstall.csh ----------
uninstall_src = SRC_ROOT / "uninstall.csh"
if uninstall_src.exists():
    uninstall_dst = APP_ROOT / "bin" / "uninstall.csh"
    log("Installing uninstall.csh...")
    shutil.copy2(uninstall_src, uninstall_dst)
    uninstall_dst.chmod(0o755)
    uninstall_src.unlink()
else:
    log("uninstall.csh not found in source.")

# ---------- Move install script into place ----------
install_src = SRC_ROOT / "install.csh"
if install_src.exists():
    install_dst = APP_ROOT / "install" / "install.csh"
    shutil.move(str(install_src), str(install_dst))
    install_dst.chmod(0o755)
    log(f"Copied install.csh to {install_dst}")

# ---------- Copy VERSION ----------
shutil.copy2(src_version_file, APP_ROOT / "VERSION")
src_version_file.unlink()
log("VERSION copied into target")

# ---------- Delete tarball ----------
tarball = PKG_ROOT / TARBALL_NAME
if tarball.exists():
    tarball.unlink()
    log(f"Deleted tarball: {TARBALL_NAME}")

# ---------- Completion ----------
if INSTALL_STATE == "new":
    log(f"Musica installed successfully. Version: {NEW_VERSION}")
else:
    log(f"Musica upgraded successfully. Version: {NEW_VERSION}")

log(f"Installation complete at {datetime.now()}")
log(f"Install log saved to: {LOG_FILE}")

sys.exit(0)

