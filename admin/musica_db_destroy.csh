#!/bin/csh -f
#
# musica_db_destroy.csh
# Completely destroy the Musica database for QA/dev reset.
#

# ----------------------------------------------
# Correct csh-safe script path & base_dir setup
# ----------------------------------------------
if ($#argv >= 1) then
    set script_name = "$argv[0]"
else
    set script_name = "musica_db_destroy.csh"
endif

set script_path = "`pwd`/$script_name"
set script_dir  = `dirname "$script_path"`
set base_dir    = `cd "$script_dir/.."; pwd`

set log_dir  = "$base_dir/logs"
set log_file = "$log_dir/db_destroy.log"

if (! -d "$log_dir") then
    mkdir -p "$log_dir"
endif

echo "===== Musica DB Destroy =====" |& tee "$log_file"
echo "Started: `date`" |& tee -a "$log_file"

alias logprint 'echo "\!*" |& tee -a "$log_file"'

# ----------------------------------------
# Safety Confirmation
# ----------------------------------------
echo ""
echo "WARNING: This will permanently delete the Musica database."
echo "Type 'DESTROY' to continue: "
echo -n "> "
set confirm = $<

if ("$confirm" != "DESTROY") then
    logprint "Invalid confirmation. Aborting."
    exit 1
endif

logprint "User confirmed destruction."

# ----------------------------------------
# Check MariaDB root access
# ----------------------------------------
logprint "Testing MariaDB root login..."

echo "SELECT 1;" | mariadb -u root >& /dev/null
if ($status != 0) then
    logprint "ERROR: Cannot authenticate to MariaDB as root."
    exit 1
endif

# ----------------------------------------
# Check if DB exists
# ----------------------------------------
logprint "Checking if Musica DB exists..."

set db_exists = `echo "SHOW DATABASES LIKE 'Musica';" | mariadb -u root | grep -c Musica`

if ($db_exists == 0) then
    logprint "Musica database does not exist. Nothing to destroy."
    exit 0
endif

# ----------------------------------------
# Drop DB
# ----------------------------------------
logprint "Dropping Musica database..."

echo "DROP DATABASE Musica;" | mariadb -u root |& tee -a "$log_file"

if ($status != 0) then
    logprint "ERROR: Failed to drop Musica DB."
    exit 1
endif

logprint "Musica DB successfully removed."
logprint "Completed: `date`"

exit 0

