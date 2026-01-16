#!/bin/tcsh
#
# musica_db_create.csh
# Creates the Musica database using the schema SQL file.

# --- Load configuration ----------------------------------------------------
if (! $?MUSICA_BASE_DIR) then
    if (-f ./config/musica.conf) then
        source ./config/musica.conf
    else if (-f ../config/musica.conf) then
        source ../config/musica.conf
    else
        echo "ERROR: musica.conf not found. Run: source config/musica.conf"
        exit 1
    endif
endif

# NOTE:
# Phase 3B Implements database creation and authentication.
# Runtime MUSICA operations do NOT use the root account.

set db_exists = 0

# ----------------------------------------------
# Correct csh-safe script path & base_dir setup
# ----------------------------------------------
if ($#argv >= 1) then
    set script_name = "$argv[0]"
else
    set script_name = "musica_db_create.csh"
endif

set log_dir  = "$MUSICA_BASE_DIR/logs"
set log_file = "$log_dir/db_creation.log"

if (! -d "$log_dir") then
    mkdir -p "$log_dir"
endif

alias logprint 'echo "\!*" |& tee -a "$log_file"'
alias logerror 'echo "ERROR: \!*" |& tee -a "$log_file"'

# ----------------------------
# Parse CLI arguments
# ----------------------------
set i = 1
while ($i <= $#argv)
    switch ($argv[$i])
        case -db:
            @ i++
            if ($i <= $#argv) then
                setenv MUSICA_DB_NAME "$argv[$i]"
            else
                logerror "-db requires a database name"
                exit 1
            endif
            breaksw
        default:
            # ignore unknown options for now
            breaksw
    endsw
    @ i++
end

# ----------------------------
# STEP 1 — Database setup check
# ----------------------------

echo "===== Phase 3B: MariaDB Create Database =====" |& tee "$log_file"
echo "Musica Database Creation Utility"
echo "----------------------------------------"
echo "Database type:     $MUSICA_DB_TYPE"
echo "Database name:     $MUSICA_DB_NAME"
echo "Schema file:       $MUSICA_SQL_DIR/Create_Schema.sql"
echo ""

# --- Validate SQL file ----------------------------------------------------
if (! -f $MUSICA_SQL_DIR/Create_Schema.sql) then
    logerror "ERROR: Schema file not found: $MUSICA_SQL_DIR/Create_Schema.sql"
    exit 1
else
    logprint "Schema file found: $MUSICA_SQL_DIR/Create_Schema.sql"
endif

# ----------------------------
# STEP 1A — Verify / create database
# ----------------------------
logprint "Checking if database '$MUSICA_DB_NAME' exists..."

# Check database existence using admin (socket) access
sudo mariadb -N -B -e "SELECT SCHEMA_NAME FROM information_schema.SCHEMATA WHERE SCHEMA_NAME='$MUSICA_DB_NAME';" > /tmp/musica_db_check.$$

if ($status != 0) then
    logerror "Failed to query database catalog."
    cat /tmp/musica_db_check.$$ | tee -a "$log_file"
    rm -f /tmp/musica_db_check.$$
    exit 1
endif

set db_check = `cat /tmp/musica_db_check.$$`
rm -f /tmp/musica_db_check.$$

if ("$db_check" == "$MUSICA_DB_NAME") then
    set db_exists = 1
    logprint "Database '$MUSICA_DB_NAME' already exists."
else
    logprint "Database '$MUSICA_DB_NAME' does not exist. Creating..."
    sudo mariadb -e "CREATE DATABASE $MUSICA_DB_NAME CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
    if ($status != 0) then
        logerror "Failed to create database '$MUSICA_DB_NAME'."
        exit 1
    endif
    logprint "Database '$MUSICA_DB_NAME' created."
endif


# ----------------------------
# STEP 2 — Execute schema 
# ----------------------------

#if ($MUSICA_DB_TYPE == "mariadb" || $MUSICA_DB_TYPE == "mysql") then
#    logprint "Loading schema into database '$MUSICA_DB_NAME'..."
#
#    if ("$MUSICA_DB_PASS" == "") then
#        # unix_socket authentication (admin context)
#        sudo mariadb --batch --silent $MUSICA_DB_NAME < $MUSICA_SQL_DIR/Create_Schema.sql
#    else
#        mariadb -u $MUSICA_DB_USER -p$MUSICA_DB_PASS $MUSICA_DB_NAME < $MUSICA_SQL_DIR/Create_Schema.sql
#    endif
#
#    if ($status != 0) then
#        logerror "ERROR: Schema creation failed."
#        exit 1
#    endif
#endif

# ----------------------------
# STEP 2 — Execute schema
# ----------------------------

if ($MUSICA_DB_TYPE == "mariadb" || $MUSICA_DB_TYPE == "mysql") then
    logprint "Loading schema into database '$MUSICA_DB_NAME'..."

    if (! $?MUSICA_DB_PASS) then
        # unix_socket authentication (admin context)
        sudo mariadb --batch --silent $MUSICA_DB_NAME < $MUSICA_SQL_DIR/Create_Schema.sql
    else
        mariadb -u $MUSICA_DB_USER -p$MUSICA_DB_PASS $MUSICA_DB_NAME < $MUSICA_SQL_DIR/Create_Schema.sql
    endif

    if ($status != 0) then
        logerror "ERROR: Schema creation failed."
        exit 1
    endif
endif

# ----------------------------
# STEP 3 — Verify schema load
# ----------------------------
logprint "Verifying schema load in database '$MUSICA_DB_NAME'..."

sudo mariadb -N -B $MUSICA_DB_NAME -e "SHOW TABLES LIKE 'recordings';" >& /tmp/musica_schema_check.$$

if ($status != 0) then
    logerror "Failed to query tables in database '$MUSICA_DB_NAME'."
    cat /tmp/musica_schema_check.$$ | tee -a "$log_file"
    rm -f /tmp/musica_schema_check.$$
    exit 1
endif

set table_check = `cat /tmp/musica_schema_check.$$`
rm -f /tmp/musica_schema_check.$$

if ("$table_check" != "recordings") then
    logerror "Schema verification failed: table 'recordings' not found."
    exit 1
endif

logprint "Schema verification successful."

logprint "Database '$MUSICA_DB_NAME' initialized and verified successfully."

exit 0
