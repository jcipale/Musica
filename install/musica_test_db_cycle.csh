#!/bin/csh -f
# ======================================================================
# Musica DB Test Cycle Utility
# Version: 1.1
# Description:
#   End-to-end database lifecycle validation:
#     1) Create schema
#     2) Verify schema
#     3) Drop schema
#     4) Verify removal
# ======================================================================

echo
echo "Musica DB Test Cycle Utility"
echo "----------------------------------------"

# --- Set paths to wrapper scripts ---
set create_script = "./Run_Create_Schema.csh"
set drop_script   = "./Run_Drop_Schema.csh"

# --- Check for scripts ---
if (! -e "$create_script") then
    echo "Error: Missing schema creation script: $create_script"
    exit 1
endif
if (! -e "$drop_script") then
    echo "Error: Missing schema drop script: $drop_script"
    exit 1
endif

# --- Step 1: Create schema ---
echo
echo "Step 1: Creating schema..."
$create_script
if ($status != 0) then
    echo "Schema creation failed. Exiting test."
    exit 1
endif

# --- Step 2: Verify schema exists ---
echo
echo "Step 2: Verifying schema existence..."
if (`which mariadb >& /dev/null; echo $status` == 0) then
    sudo mariadb -e "SHOW DATABASES LIKE 'musica';" | grep -q musica
    if ($status == 0) then
        echo "Schema 'musica' verified in MariaDB."
    else
        echo "Schema 'musica' not found in MariaDB."
        exit 1
    endif
else if (`which mysql >& /dev/null; echo $status` == 0) then
    sudo mysql -e "SHOW DATABASES LIKE 'musica';" | grep -q musica
    if ($status == 0) then
        echo "Schema 'musica' verified in MySQL."
    else
        echo "Schema 'musica' not found in MySQL."
        exit 1
    endif
else if (`which sqlite3 >& /dev/null; echo $status` == 0) then
    if (-e "./../data/musica.db") then
        echo "SQLite database file verified."
    else
        echo "SQLite database file missing."
        exit 1
    endif
else
    echo "No supported database found for verification."
    exit 1
endif

# --- Step 3: Drop schema ---
echo
echo "Step 3: Dropping schema..."
$drop_script
if ($status != 0) then
    echo "Schema drop failed. Exiting test."
    exit 1
endif

# --- Step 4: Verify removal ---
echo
echo "Step 4: Verifying schema removal..."
if (`which mariadb >& /dev/null; echo $status` == 0) then
    sudo mariadb -e "SHOW DATABASES LIKE 'musica';" | grep -q musica
    if ($status == 0) then
        echo "Schema 'musica' still present — cleanup failed."
        exit 1
    else
        echo "Schema successfully removed from MariaDB."
    endif
else if (`which mysql >& /dev/null; echo $status` == 0) then
    sudo mysql -e "SHOW DATABASES LIKE 'musica';" | grep -q musica
    if ($status == 0) then
        echo "Schema 'musica' still present — cleanup failed."
        exit 1
    else
        echo "Schema successfully removed from MySQL."
    endif
else if (`which sqlite3 >& /dev/null; echo $status` == 0) then
    if (-e "./../data/musica.db") then
        echo "SQLite DB file still exists — cleanup failed."
        exit 1
    else
        echo "SQLite database file successfully removed."
    endif
else
    echo "No supported database found for verification."
    exit 1
endif

echo
echo "----------------------------------------"
echo "Database lifecycle test completed successfully."
exit 0

