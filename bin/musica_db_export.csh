#!/bin/csh -f
# musica_db_export.csh
# Export recordings to CSV or plain text.

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

# output path
if ("$1" != "") then
    set outpath = "$1"
else
    set outpath = "$MUSICA_EXPORT_DIR/$MUSICA_DEFAULT_EXPORT"
endif

# format selection: CSV if second arg == csv else plain text
set fmt = "csv"
if ("$2" != "") then
    set fmt = "$2"
endif

if ("$MUSICA_DB_PASS" == "") then
    set DBCLIENT = "sudo $MUSICA_DB_TYPE -D $MUSICA_DB_NAME -e"
else
    set DBCLIENT = "$MUSICA_DB_TYPE -u $MUSICA_DB_USER -p$MUSICA_DB_PASS -D $MUSICA_DB_NAME -e"
endif

if ("$fmt" == "csv") then
    # produce CSV via SQL client (tab-separated -> convert)
    $DBCLIENT "SELECT artist,title,orchestra,conductor,year,genre,format,label,catalog_number,reissue,mode,dbx FROM recordings ORDER BY year,artist;" | sed 's/\t/,/g' >! "$outpath"
else
    $DBCLIENT "SELECT * FROM recordings ORDER BY year,artist;" >! "$outpath"
endif

if ($status != 0) then
    echo "Export failed."
    exit 1
endif

echo "Export saved to: $outpath"
exit 0

