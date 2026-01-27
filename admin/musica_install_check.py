#!/usr/bin/env python3
"""
Musica Environment Setup

Purpose:
  1) Select database backend (MariaDB, MySQL, SQLite)
  2) Check / install database client/server
  3) Scan mounted volumes and select install location
  4) Create initial Musica directory hierarchy
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

# -----------------------------
# Helpers
# -----------------------------

def run(cmd, check=False, capture=False):
    """Run a shell command."""
    if capture:
        return subprocess.run(cmd, shell=True, text=True,
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE)
    return subprocess.run(cmd, shell=True, check=check)


def which(cmd):
    """Return path if command exists in PATH."""
    return shutil.which(cmd)


def sudo_available():
    return which("sudo") is not None


# -----------------------------
# Step 1 — Database selection
# -----------------------------

print("\n----------------------------------------------")
print("        Musica Environment Setup")
print("----------------------------------------------\n")

print("Select database to use:")
print("  1) MariaDB")
print("  2) MySQL")
print("  3) SQLite")
choice = input("Enter choice (1-3): ").strip()
print("")

if choice == "1":
    db = "mariadb"
    pkg = "mariadb-server"
elif choice == "2":
    db = "mysql"
    pkg = "mysql-server"
elif choice == "3":
    db = "sqlite3"
    pkg = "sqlite3"
else:
    print("Invalid choice. Defaulting to MariaDB.")
    db = "mariadb"
    pkg = "mariadb-server"

print(f"Database selected: {db}\n")

# -----------------------------
# Step 2 — Check/install DB
# -----------------------------

print(f"Checking if {db} is installed...")

if which(db):
    print(f"{db} is already installed.")
else:
    print(f"{db} not found.")

    if not sudo_available():
        print("ERROR: sudo not available; cannot install packages.")
        sys.exit(1)

    print("Installing via apt...")
    run("sudo apt-get update", check=True)
    run(f"sudo apt-get install -y {pkg}", check=True)

print("\nDatabase setup check complete.\n")

# -------------------------------------------------------------
# Step 3 — Scan mounted volumes (/mnt only)
# -------------------------------------------------------------

print("Scanning mounted volumes (excluding local system partitions)...")

mountfile = Path("/tmp/musica_mounts.txt")
if mountfile.exists():
    mountfile.unlink()

cmd = (
    "df -h --output=target,size,used,avail "
    "| grep '^/mnt/' | sort"
)
result = run(cmd, capture=True)

mountfile.write_text(result.stdout)

if not result.stdout.strip():
    print("ERROR: No /mnt volumes found.")
    sys.exit(1)

print("--------------------------------------------------------------")
print("No.  Mount Point                    Size       Used       Avail")
print("--------------------------------------------------------------")

lines = mountfile.read_text().splitlines()
for idx, line in enumerate(lines, start=1):
    print(f"{idx:<3}  {line}")

print("--------------------------------------------------------------")

choice = input("Enter number of mount to use for Musica: ").strip()

try:
    idx = int(choice)
    target = lines[idx - 1].split()[0]
except (ValueError, IndexError):
    print("Invalid selection.")
    sys.exit(1)

print(f"Selected: {target}")

# -----------------------------
# Step 4 — Create directories
# -----------------------------

musica_root = Path(target) / "Musica"
print(f"\nCreating Musica directory structure on {target} ...")

subdirs = ["bin", "etc", "log", "data", "docs"]

if sudo_available():
    run(f"sudo mkdir -p {musica_root}", check=True)
    for sd in subdirs:
        run(f"sudo mkdir -p {musica_root / sd}", check=True)

    user = os.environ.get("USER", "")
    run(f"sudo chown -R {user}:{user} {musica_root}", check=True)
else:
    musica_root.mkdir(parents=True, exist_ok=True)
    for sd in subdirs:
        (musica_root / sd).mkdir(parents=True, exist_ok=True)

print(f"\nMusica directory structure created at: {musica_root}\n")
print("Structure:")
run(f"ls -l {musica_root}")

print("""
--------------------------------------------------------------
Musica base environment setup is complete.
Proceed with database schema initialization or CSV import.
--------------------------------------------------------------
""")

