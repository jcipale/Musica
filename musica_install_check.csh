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
        set db = "mariadb-server"
        breaksw
    case 2:
        set db = "mysql-server"
        breaksw
    case 3:
        set db = "sqlite3"
        breaksw
    default:
        echo "Invalid choice. Defaulting to MariaDB."
        set db = "mariadb"
endsw

echo "Database selected: $db"
echo ""

# --- Step 2: Check if installed ---
echo "Checking if $db is installed..."

set installed = `which $db 2>/dev/null`
if ("$installed" == "") then
    echo "$db not found. Installing via apt..."
    sudo apt update
    sudo apt install -y $db || echo "Error: Unable to install $db"
else
    echo "$db is already installed: $installed"
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

#if (! -s $mountfile) then
#    echo "No mounts found under /mnt."
#    exit 1
#endif

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

# ===========================================================
#  Step 4: (Future)
#  - Create Musica directory hierarchy
#  - Copy/untar scripts
#  - Configure database and environment
# ===========================================================
echo "Creating Musica directory structure on $target ..."
sudo mkdir -p $target/Musica/{bin,etc,log,data,docs}
sudo chown -R $USER:$USER $target/Musica

echo "Musica directory tree created successfully."
echo ""
echo "--------------------------------------------------------------"
echo "Musica base environment setup is complete."
echo "Proceed with database schema initialization or CSV import."
echo "--------------------------------------------------------------"

unset noglob
