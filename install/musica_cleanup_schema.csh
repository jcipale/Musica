#!/bin/csh -f
# ==============================================================
#  Musica Database Cleanup Utility
#  Compatible with: CSH / TCSH
# ==============================================================
#  Purpose:
#     Detect installed DB engine (MariaDB / MySQL / SQLite)
#     and clean up / drop the Musica schema.
# ==============================================================

echo ""
echo "🧹 Musica Database Cleanup Utility"
echo "----------------------------------"

# --------------------------------------------------------------
# Detect available database engine
# --------------------------------------------------------------
which mariadb >& /dev/null
set mariadb_status = $status

which mysql >& /dev/null
set mysql_status = $status

which sqlite3 >& /dev/null
set sqlite_status = $status

if ($mariadb_status == 0) then
    set db_type = "mariadb"
else if ($mysql_status == 0) then
    set db_type = "mysql"
else if ($sqlite_status == 0) then
    set db_type = "sqlite3"
else
    set db_type = ""
endif

if ("$db_type" == "") then
    echo "❌ No supported database found."
    exit 1
endif

# --------------------------------------------------------------
# Confirm user intent
# --------------------------------------------------------------
echo "Detected database engine: $db_type"
echo -n "⚠️  This will permanently remove the Musica database. Continue? (y/N): "
set answer = $<
if ("$answer" != "y" && "$answer" != "Y") then
    echo "Cleanup aborted by user."
    exit 0
endif

# --------------------------------------------------------------
# Perform cleanup depending on DB engine
# --------------------------------------------------------------
switch ($db_type)
    case "mariadb":
    case "mysql":
        echo "🧨 Dropping Musica schema from $db_type..."
        $db_type -u root -p -e "DROP DATABASE IF EXISTS Musica;"
        if ($status != 0) then
            echo "❌ Failed to drop schema in $db_type."
            exit 1
        endif
        breaksw

    case "sqlite3":
        if (-e musica.db) then
            echo "🧨 Removing musica.db..."
            rm -f musica.db
            if ($status != 0) then
                echo "❌ Failed to remove musica.db."
                exit 1
            endif
        else
            echo "ℹ️  No musica.db file found to remove."
        endif
        breaksw
endsw

echo ""
echo "✅ Musica database cleanup complete."
echo "--------------------------------------------------------------"
exit 0

