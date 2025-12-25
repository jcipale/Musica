#!/bin/csh -f

echo "=================================================="
echo "\!\!\! DANGER: MUSICA DATABASE NUCLEAR RESET \!\!\!"
echo ""
echo "This will PERMANENTLY DESTROY:"
echo "  - Database: $MUSICA_DB_NAME"
echo "  - User:     $MUSICA_DB_USER@$MUSICA_DB_HOST"
echo ""
echo "This action CANNOT be undone."
echo "=================================================="
echo -n "Type NUKE to continue: "
set confirm = $<
if ("$confirm" != "NUKE") then
    echo "Aborted."
    exit 1
endif

echo "Dropping user '$MUSICA_DB_USER'@'$MUSICA_DB_HOST'..."
sudo mariadb -e "DROP USER IF EXISTS '$MUSICA_DB_USER'@'$MUSICA_DB_HOST';"

set user_count = `sudo mariadb -N -B -e "SELECT COUNT(*) FROM mysql.user WHERE User='${MUSICA_DB_USER}' AND Host='${MUSICA_DB_HOST}';"`

# Verify user is gone
set user_count = `sudo mariadb -N -B -e "SELECT COUNT(*) FROM mysql.user WHERE User='${MUSICA_DB_USER}' AND Host='${MUSICA_DB_HOST}';"`

if ("$user_count" != "0") then
    echo "ERROR: User '${MUSICA_DB_USER}@${MUSICA_DB_HOST}' still exists"
    exit 1
endif

echo "User successfully removed."

sudo mariadb -e "FLUSH PRIVILEGES;"

echo "Drop Database"

sudo mariadb -e "DROP DATABASE IF EXISTS ${MUSICA_DB_NAME};"

set db_count = `sudo mariadb -N -B -e "SELECT COUNT(*) FROM information_schema.SCHEMATA WHERE SCHEMA_NAME='${MUSICA_DB_NAME}';"`

if ("$db_count" != "0") then
    echo "ERROR: Database '${MUSICA_DB_NAME}' still exists"
    exit 1
endif

echo "Database successfully removed."
exit 0
