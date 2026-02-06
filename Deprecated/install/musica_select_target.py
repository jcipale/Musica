#!/opt/Musica/venv/bin/python

"""
Musica Target Selection Utility

Allows the user to select or create a target installation path
for the Musica project.
"""

import os
import subprocess
import sys
from pathlib import Path

# ------------------------------------------------------------
# Intro
# ------------------------------------------------------------
print("")
print("Musica Target Selection Utility")
print("----------------------------------")

# --- Default Target Root ---
default_target = Path("/mnt")
musica_root = None

# ------------------------------------------------------------
# Step 1: List available mount points
# ------------------------------------------------------------
print("")
print(f"Available mount points under {default_target}:")

if default_target.is_dir():
    try:
        for entry in sorted(default_target.iterdir()):
            if entry.is_dir():
                print(entry.name)
    except PermissionError:
        print("Warning: insufficient permissions to list mount points.")
else:
    print(f"Warning: {default_target} not found.")

# ------------------------------------------------------------
# Step 2: Ask for desired mount point
# ------------------------------------------------------------
print("")
user_target = input("Enter desired target mount point (default: /mnt/sda1): ").strip()

if not user_target:
    user_target = "/mnt/sda1"

user_target_path = Path(user_target)
musica_root = user_target_path / "Musica"

# ------------------------------------------------------------
# Step 3: Create Musica directory structure
# ------------------------------------------------------------
print("")
print(f"Creating Musica directory structure on {user_target_path} ...")

subdirs = ["bin", "etc", "log", "data", "docs"]

for subdir in subdirs:
    subprocess.run(
        ["sudo", "mkdir", "-p", str(musica_root / subdir)],
        check=False
    )

# Fix ownership to current user
user = os.getlogin()
result = subprocess.run(
    ["sudo", "chown", "-R", f"{user}:{user}", str(musica_root)],
    check=False
)

if result.returncode != 0:
    print(f"Error: Failed to set ownership on {musica_root}")
    sys.exit(1)

# ------------------------------------------------------------
# Step 4: Confirm success
# ------------------------------------------------------------
print("")
print("Musica target directory created successfully!")
print(f"Root path: {musica_root}")
print("")
print("Directory structure:")

subprocess.run(["ls", "-l", str(musica_root)], check=False)

print("")
print(" Target selection complete.")

