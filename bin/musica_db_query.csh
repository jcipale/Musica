#!/bin/csh -f
# musica_db_query.csh
# Execute an ad-hoc SQL query and print results. For CSV/Text output see export script.

set script_dir = `dirname $0`
set base_dir = `cd $script_dir/..; pwd`

if (! -f "$base_dir/config/musica.conf") then
    echo "Error: config missing: $base_dir/config/musica.conf"
    exit 1
endif
source "$base_dir/config/musica.conf"

$base_dir/bin/musica_verify_env.csh
if ($status != 0) then
    echo "Environment verification failed."
    exit 1
endif

if ($#argv == 0) then
    echo "Usage: $0 \"SQL_QUERY\""
    exit 1
endif

# join all args into one query string
set query = "$argv[1]"
@ i = 2
while ($i <= $#argv)
    set query = "$query $argv[$i]"
    @ i++
end

if ("$MUSICA_DB_PASS" == "") then
    sudo $MUSICA_DB_TYPE -D $MUSICA_DB_NAME -e "$query"
else
    $MUSICA_DB_TYPE -u "$MUSICA_DB_USER" -p"$MUSICA_DB_PASS" -D $MUSICA_DB_NAME -e "$query"
endif

exit $status

