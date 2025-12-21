#!/bin/csh -f
# ===============================================================
# Musica Database Cleanup Utility
# Compatible with: MariaDB, MySQL, SQLite
# ===============================================================

echo ""
echo "🧹 Musica Database Cleanup Utility"
echo "----------------------------------"

# Detect OS
set os_type = `uname -s`
echo "Detected OS: $os_type"

# -----------------------------------------------------------------
# Step 1: Detect which supported database is installed
# -----------------------------------------------------------------
set db_type = ""

if (`which mariadb-server >& /dev/null; echo $?` == 0) then
    set db_type = "mariadb"
else if (`which mysql-server >& /dev/null; echo $?` == 0) then
    set db_type = "mysql"
else if (`which sqlite3 >& /dev/null; echo $?` == 0) then
    set db_type = "sqlite"
endif

if ("$db_type" == "") then
    echo "❌ No supported database found (MariaDB/MySQL/SQLite)."
    exit 1
endif

# -----------------------------------------------------------------
# Step 2: Confirm user intent
# -----------------------------------------------------------------
echo -n "⚠️  Are you sure you want to DESTROY the Musica database? (y/N): "
set confirm = $<
if ("$confirm" != "y" && "$confirm" != "Y") then
    echo "Aborted by user."
    exit 0
endif

# -----------------------------------------------------------------
# Step 3: Execute cleanup
# -----------------------------------------------------------------
if ("$db_type" == "mariadb" || "$db_type" == "mysql") then
    echo "🧹 Dropping Musica schema from $db_type..."
    sudo $db_type -u root -e "DROP DATABASE IF EXISTS Musica;"
else if ("$db_type" == "sqlite") then
    echo "🧹 Removing SQLite database file..."
    if (-e Musica.db) then
        rm -f Musica.db
        echo "✅ Musica.db deleted."
    else
        echo "ℹ️  Musica.db not found. Nothing to delete."
    endif
endif

# -----------------------------------------------------------------
# Step 4: Wrap up
# -----------------------------------------------------------------
if ($status == 0) then
    echo "✅ Cleanup completed successfully."
else
    echo "⚠️  Cleanup encountered an error (exit code $status)."
endif

exit 0

