#!/bin/csh -f
# musica_verify_env.csh
# Verify Musica directory layout, config and DB client/service presence.

set script_dir = `dirname $0`
set base_dir = `cd $script_dir/..; pwd`

# load config
if (! -f "$base_dir/config/musica.conf") then
    echo "Error: configuration file not found: $base_dir/config/musica.conf"
    exit 1
endif
source "$base_dir/config/musica.conf"

# required directories
set required_dirs = ( "$MUSICA_DATA_DIR" "$MUSICA_IMPORT_DIR" "$MUSICA_EXPORT_DIR" \
                      "$MUSICA_ARCHIVE_DIR" "$MUSICA_BIN_DIR" "$MUSICA_SQL_DIR" "$MUSICA_LOG_DIR" )

foreach d ($required_dirs)
    if (! -d "$d") then
        echo "Missing directory: $d"
        exit 1
    endif
end

# check DB client presence
set has_client = 0
if (`which mariadb >& /dev/null; echo $status` == 0) then
    set has_client = 1
else if (`which mysql >& /dev/null; echo $status` == 0) then
    set has_client = 1
endif

if ($has_client == 0) then
    echo "Error: no mariadb/mysql client found in PATH."
    exit 1
endif

# check DB service if using mariadb/mysql
if ("$MUSICA_DB_TYPE" == "mariadb" || "$MUSICA_DB_TYPE" == "mysql") then
    set svc = `systemctl is-active $MUSICA_DB_TYPE | tr -d '[:space:]'`
    if ("$svc" != "active") then
        echo "Warning: $MUSICA_DB_TYPE service not active."
    endif
endif

echo "Environment verification: OK"
exit 0
