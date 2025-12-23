#!/bin/csh -f
#
# Phase 3C — MariaDB User Creation & Verification
#

# --- Load configuration ---
if (! $?MUSICA_BASE_DIR) then
    if (-f "$0:h/../config/musica.conf") then
        source "$0:h/../config/musica.conf"
    else
        echo "ERROR: musica.conf not found"
        exit 1
    endif
endif

set log_dir  = "$MUSICA_BASE_DIR/logs"
set log_file = "$log_dir/db_user_create.log"

if (! -d "$log_dir") then
    mkdir -p "$log_dir"
endif

alias logprint 'echo "\!*" |& tee -a "$log_file"'
alias logerror 'echo "ERROR: \!*" |& tee -a "$log_file"'

echo "===== Phase 3C: MariaDB User Creation =====" |& tee "$log_file"
logprint "Database: $MUSICA_DB_NAME"
logprint "User:     $MUSICA_DB_USER"
echo ""

# ------------------------------------------------------------
# STEP 1 — Verify database exists
# ------------------------------------------------------------
sudo mariadb -N -B -e \
"SELECT SCHEMA_NAME FROM information_schema.SCHEMATA WHERE SCHEMA_NAME='$MUSICA_DB_NAME';" \
> /tmp/musica_db_exists.$$

if ($status != 0) then
    logerror "Failed to query database catalog"
    exit 1
endif

set db_check = `cat /tmp/musica_db_exists.$$`
rm -f /tmp/musica_db_exists.$$

if ("$db_check" != "$MUSICA_DB_NAME") then
    logerror "Database '$MUSICA_DB_NAME' does not exist. Run Phase 3B first."
    exit 1
endif

logprint "Database exists."

# ------------------------------------------------------------
# STEP 2 — Create user (idempotent)
# ------------------------------------------------------------
logprint "Ensuring database user exists..."

if ("$MUSICA_DB_PASS" == "") then
    sudo mariadb -e \
    "CREATE USER IF NOT EXISTS '$MUSICA_DB_USER'@'$MUSICA_DB_HOST' IDENTIFIED VIA unix_socket;"
else
    sudo mariadb -e \
    "CREATE USER IF NOT EXISTS '$MUSICA_DB_USER'@'$MUSICA_DB_HOST' IDENTIFIED BY '$MUSICA_DB_PASS';"
endif

if ($status != 0) then
    logerror "Failed to create or verify user '$MUSICA_DB_USER'"
    exit 1
endif

logprint "User exists."

# ------------------------------------------------------------
# STEP 3 — Apply grants
# ------------------------------------------------------------
logprint "Applying grants..."

sudo mariadb -e "
GRANT
    SELECT, INSERT, UPDATE, DELETE,
    CREATE, DROP, INDEX, ALTER
ON ${MUSICA_DB_NAME}.*
TO '$MUSICA_DB_USER'@'$MUSICA_DB_HOST';
FLUSH PRIVILEGES;
"

if ($status != 0) then
    logerror "Failed to apply grants"
    exit 1
endif

logprint "Grants applied."

# ------------------------------------------------------------
# STEP 4 — Verify login as runtime user
# ------------------------------------------------------------
logprint "Verifying login as '$MUSICA_DB_USER'..."

if ("$MUSICA_DB_PASS" == "") then
    mariadb -u "$MUSICA_DB_USER" "$MUSICA_DB_NAME" -e "SELECT 1;" >& /dev/null
else
    mariadb -u "$MUSICA_DB_USER" -p"$MUSICA_DB_PASS" "$MUSICA_DB_NAME" -e "SELECT 1;" >& /dev/null
endif

if ($status != 0) then
    logerror "Login test failed for user '$MUSICA_DB_USER'"
    exit 1
endif

logprint "User authentication verified."

logprint "Phase 3C complete. Database user ready."
exit 0

