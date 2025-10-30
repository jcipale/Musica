#!/bin/csh
# ===========================================================
#  Musica Setup Script
#  Purpose:
#    1) Check/install database backend (MariaDB, MySQL, SQLite)
#    2) Confirm environment setup
#    3) Let user select install location (/mnt/…)
# ===========================================================
set noglob

echo ""
echo "----------------------------------------------"
echo "        Musica Environment Setup"
echo "----------------------------------------------"
echo ""

# --- Step 1: Select database ---
echo "Select database to use:"
echo "  1) MariaDB"
echo "  2) MySQL"
echo "  3) SQLite"
echo -n "Enter choice (1-3): "
set choice = $<
echo ""

switch ($choice)
    case 1:
        set db = "mariadb"
        set pkg = "mariadb-server"
        breaksw
    case 2:
        set db = "mysql"
        set pkg = "mysql-server"
        breaksw
    case 3:
        set db = "sqlite3"
        set pkg = "sqlite3"
        breaksw
    default:
        echo "Invalid choice. Defaulting to MariaDB."
        set db = "mariadb"
        set pkg = "mariadb-server"
endsw

echo "Database selected: $db"
echo ""

# --- Step 2: Check if installed ---
echo "Checking if $db is installed..."

# Check if the binary exists in PATH
which $db >& /dev/null
if ($status == 0) then
    echo "$db is already installed."
else
    echo "$db not found. Installing via apt..."

    sudo apt-get update
    sudo apt-get install -y $pkg

endif
echo ""
echo "Database setup check complete."
echo ""

# -------------------------------------------------------------
# Step 3: Scan mounted volumes (excluding local system partitions)
# -------------------------------------------------------------
echo ""
echo "Scanning mounted volumes (excluding local system partitions)..."

# ---------- build mountfile (safe: run under sh to avoid csh parsing issues) ----------
set mountfile = "/tmp/musica_mounts.txt"
rm -f $mountfile
/bin/sh -c 'df -h --output=target,size,used,avail | grep "^/mnt/" | sort' >! $mountfile

# ---------- show numbered list (print full line, do not re-parse fields) ----------

set idx = 1

echo "--------------------------------------------------------------"
echo "No.  Mount Point                    Size       Used       Avail"
echo "--------------------------------------------------------------"
#awk '{ printf("%-3d  %s\n", NR, $0) }' $mountfile

/bin/awk '{ printf("%-3d  %s\n", NR, $0) }' /tmp/musica_mounts.txt

echo "--------------------------------------------------------------"

# ---------- prompt and extract the chosen mount (first field) ----------
echo -n "Enter number of mount to use for Musica: "
set choice = $<
set target = `awk -v n="$choice" 'NR==n {print $1}' $mountfile`

if ("$target" == "") then
    echo "Invalid selection."
    exit 1
endif

echo "Selected: $target"
# (now use $target for creating directories etc.)

echo "Creating Musica directory structure on $target ..."

# ===========================================================
#  Step 4: (Future)
#  - Create Musica directory hierarchy
#  - Copy/untar scripts
#  - Configure database and environment
# ===========================================================
# Define the Musica root directory
set musica_root = "$target/Musica"

# Create subdirectories explicitly (no brace expansion)
sudo mkdir -p $musica_root
foreach subdir (bin etc log data docs)
    sudo mkdir -p "$musica_root/$subdir"
end

# Assign ownership to the current user
sudo chown -R "${USER}:${USER}" "$musica_root"

echo "Musica directory structure created successfully at: $musica_root"
echo ""
echo "Structure:"
ls -l "$musica_root"

echo "Musica directory tree created successfully."
echo ""
echo "--------------------------------------------------------------"
echo "Musica base environment setup is complete."
echo "Proceed with database schema initialization or CSV import."
echo "--------------------------------------------------------------"

unset noglob
