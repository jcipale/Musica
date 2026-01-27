#!/usr/bin/env python3
"""
Musica Environment Setup Script
Purpose:
  1) Check/install database backend (MariaDB, MySQL, SQLite)
  2) Confirm environment setup
  3) Let user select install location (/mnt/…)
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------
def run(cmd):
    return subprocess.run(cmd, text=True, check=False)


def cmd_exists(cmd):
    return shutil.which(cmd) is not None


def require_root():
    if os.geteuid() != 0:
        print("This operation requires sudo/root.")
        sys.exit(1)


# ------------------------------------------------------------
# Header
# ------------------------------------------------------------
print("\n----------------------------------------------")
print("        Musica Environment Setup")
print("----------------------------------------------\n")

# ------------------------------------------------------------
# Step 1 — Select database
# ------------------------------------------------------------
print("Select database to use:")
print("  1) MariaDB")
print("  2) MySQL")
print("  3) SQLite")

choice = input("Enter choice (1-3): ").strip()
print()

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

# ------------------------------------------------------------
# Step 2 — Check / install DB
# ------------------------------------------------------------
print(f"Checking if {db} is installed...")

if cmd_exists(db):
    print(f"{db} is already installed.")
else:
    print(f"{db} not found. Installing via apt...")
    require_root()
    run(["apt-get", "update"])
    run(["apt-get", "install", "-y", pkg])

print("\nDatabase setup check complete.\n")

# ------------------------------------------------------------
# Step 3 — Scan mounted volumes under /mnt
# ------------------------------------------------------------
print("Scanning mounted volumes (excluding local system partitions)...\n")

mountfile = Path("/tmp/musica_mounts.txt")
mountfile.unlink(missing_ok=True)

cmd = "df -h --output=target,size,used,avail | grep '^/mnt/' | sort"
with mountfile.open("w") as f:
    subprocess.run(cmd, shell=True, stdout=f, text=True)

lines = mountfile.read_text().strip().splitlines()

if not lines:
    print("No /mnt mounts found.")
    sys.exit(1)

print("--------------------------------------------------------------")
print("No.  Mount Point                    Size       Used       Avail")
print("--------------------------------------------------------------")

for idx, line in enumerate(lines, start=1):
    print(f"{idx:<3}  {line}")

print("--------------------------------------------------------------")

choice = input("Enter number of mount to use for Musica: ").strip()

try:
    idx = int(choice) - 1
    target = lines[idx].split()[0]
except (ValueError, IndexError):
    print("Invalid selection.")
    sys.exit(1)

print(f"\nSelected: {target}")

# ------------------------------------------------------------
# Step 4 — Create directory structure
# ------------------------------------------------------------
musica_root = Path(target) / "Musica"

print(f"\nCreating Musica directory structure on {target} ...")

require_root()

subdirs = ["bin", "etc", "log", "data", "docs"]
os.makedirs(musica_root, exist_ok=True)

for sub in subdirs:
    os.makedirs(musica_root / sub, exist_ok=True)

user = os.environ.get("SUDO_USER", os.environ.get("USER"))
run(["chown", "-R", f"{user}:{user}", str(musica_root)])

print(f"\nMusica directory structure created successfully at: {musica_root}\n")
print("Structure:")
run(["ls", "-l", str(musica_root)])

print("\n--------------------------------------------------------------")
print("Musica base environment setup is complete.")
print("Proceed with database schema initialization or CSV import.")
print("--------------------------------------------------------------")

