#!/bin/csh -f
# ------------------------------------------------------------
# Musica DB Destroy Utility (Dangerous)
# Removes entire Musica DB — use for testing only
# ------------------------------------------------------------

echo "⚠️  WARNING: This will permanently delete the Musica database."
echo -n "Type 'DESTROY' to continue: "
set confirm = $<

if ("$confirm" != "DESTROY") then
    echo "Aborting."
    exit 0
endif

set db_type = ""
if (`which mariadb >& /dev/null`) then
    set db_type = "mariadb"
else if (`which mysql >& /dev/null`) then
    set db_type = "mysql"
else if (`which sqlite3 >& /dev/null`) then
    set db_type = "sqlite"
endif

if ("$db_type" == "") then
    echo "❌ No supported database found."
    exit 1
endif

switch ($db_type)
    case "mariadb":
        sudo mariadb -e "DROP DATABASE IF EXISTS Musica;"
        breaksw
    case "mysql":
        sudo mysql -e "DROP DATABASE IF EXISTS Musica;"
        breaksw
    case "sqlite":
        rm -f ./Musica.sqlite3
        breaksw
endsw

echo ""
echo "💀 Database destroyed."

