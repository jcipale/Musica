#!/bin/csh -f
#
# ==========================================================
#  Musica Target Selection Utility
#  --------------------------------
#  Description:
#    This script allows the user to select or create
#    a target installation path for the Musica project.
#
#  Compatible shells: csh / tcsh
#  Author: J. Cipale & ChatGPT (GPT-5)
#  Version: 1.2
# ==========================================================

echo ""
echo "🎵 Musica Target Selection Utility"
echo "----------------------------------"

# --- Default Target Root ---
set default_target = "/mnt"
set musica_root = ""

# --- Step 1: List available mount points ---
echo ""
echo "Available mount points under $default_target:"
if ( -d $default_target ) then
    ls -1 $default_target
else
    echo "⚠️  Warning: $default_target not found."
endif

# --- Step 2: Ask for desired mount point ---
echo ""
echo -n "Enter desired target mount point (default: /mnt/sda1): "
set user_target = $<
if ("$user_target" == "") then
    set user_target = "/mnt/sda1"
endif

# --- Step 3: Confirm path and prepare Musica directory ---
set musica_root = "$user_target/Musica"

echo ""
echo "Creating Musica directory structure on $user_target ..."

# ✅ Create directory structure safely
sudo mkdir -p $musica_root/bin
sudo mkdir -p $musica_root/etc
sudo mkdir -p $musica_root/log
sudo mkdir -p $musica_root/data
sudo mkdir -p $musica_root/docs

# ✅ Fix ownership so current user owns the files
sudo chown -R "`whoami`:`whoami`" "$musica_root"

if ($status != 0) then
    echo "❌ Error: Failed to set ownership on $musica_root"
    exit 1
endif

# --- Step 4: Confirm success ---
echo ""
echo "✅ Musica target directory created successfully!"
echo "📂 Root path: $musica_root"
echo ""
echo "Directory structure:"
ls -l $musica_root
echo ""
echo "🎶 Target selection complete."

