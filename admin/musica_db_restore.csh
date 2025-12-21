#!/bin/csh -f
# musica_db_restore.csh
# Restore Musica DB from a .sql.gz backup (admin operation).

if ($#argv != 1) then
    echo "Usage: $0 <backup-file.sql.gz>"
    exit 1
endif

set backup_file = $argv[1]
set script_dir = `dirname $0`
set base_dir = `cd $script_dir/..; pwd`

if (! -f "$base_dir/config/musica.conf") then
    echo "Error: config missing: $base_dir/config/musica.conf"
    exit 1
endif
source "$base_dir/config/musica.conf"

if (! -f "$backup_file") then
    echo "Error: backup file not found: $backup_file"
    exit 1
endif

if (! -d "$MUSICA_LOG_DIR") then
    mkdir -p "$MUSICA_LOG_DIR"
endif

echo "Restoring database $MUSICA_DB_NAME from $backup_file"
# drop db
if ("$MUSICA_DB_PASS" == "") then
    sudo mariadb -e "DROP DATABASE IF EXISTS $MUSICA_DB_NAME;"
    sudo mariadb -e "CREATE DATABASE $MUSICA_DB_NAME;"
else
    mysql -u "$MUSICA_DB_USER" -p"$MUSICA_DB_PASS" -e "DROP DATABASE IF EXISTS $MUSICA_DB_NAME;"
    mysql -u "$MUSICA_DB_USER" -p"$MUSICA_DB_PASS" -e "CREATE DATABASE $MUSICA_DB_NAME;"
endif

if ($status != 0) then
    echo "Error: failed to drop/create database."
    exit 1
endif

# restore
gzip -dc "$backup_file" | ( if ("$MUSICA_DB_PASS" == "") then sudo mariadb $MUSICA_DB_NAME; else mysql -u "$MUSICA_DB_USER" -p"$MUSICA_DB_PASS" $MUSICA_DB_NAME; endif )

if ($status != 0) then
    echo "Restore failed."
    exit 1
endif

echo "Restore complete."
exit 0

