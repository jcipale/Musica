#!/bin/csh -f
# musica_db_backup.csh
# Create a timestamped compressed SQL backup into MUSICA_ARCHIVE_DIR.

set script_dir = `dirname $0`
set base_dir = `cd $script_dir/..; pwd`

if (! -f "$base_dir/config/musica.conf") then
    echo "Error: config missing: $base_dir/config/musica.conf"
    exit 1
endif
source "$base_dir/config/musica.conf"

if (! -d "$MUSICA_LOG_DIR") then
    mkdir -p "$MUSICA_LOG_DIR"
endif

set timestamp = `date +"%Y%m%d_%H%M%S"`
set backup_file = "$MUSICA_LOG_DIR/musica_backup_$timestamp.sql.gz"
set log_file = "$MUSICA_LOG_DIR/musica_backup_$timestamp.log"

# choose dump command
set dump_cmd = ""
if (`which mysqldump >& /dev/null; echo $status` == 0) then
    set dump_cmd = "mysqldump"
else if (`which mariadb-dump >& /dev/null; echo $status` == 0) then
    set dump_cmd = "mariadb-dump"
endif

if ("$dump_cmd" == "") then
    echo "Error: mysqldump/mariadb-dump not found."
    exit 1
endif

echo "Backing up database $MUSICA_DB_NAME to $backup_file"
if ("$MUSICA_DB_PASS" == "") then
    $dump_cmd --databases $MUSICA_DB_NAME > /tmp/musica_dump.sql 2> "$log_file"
else
    $dump_cmd --user="$MUSICA_DB_USER" --password="$MUSICA_DB_PASS" --databases $MUSICA_DB_NAME > /tmp/musica_dump.sql 2> "$log_file"
endif

if ($status != 0) then
    echo "Error during dump. See $log_file"
    rm -f /tmp/musica_dump.sql
    exit 1
endif

gzip -c /tmp/musica_dump.sql > "$backup_file"
set rc = $status
rm -f /tmp/musica_dump.sql

if ($rc != 0) then
    echo "Error compressing backup."
    exit 1
endif

echo "Backup complete: $backup_file"
echo "Log: $log_file"
exit 0
