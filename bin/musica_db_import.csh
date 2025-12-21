#!/bin/csh -f
# musica_db_import.csh
# Import CSV into recordings table. Appends only.

set script_dir = `dirname $0`
set base_dir = `cd $script_dir/..; pwd`

if (! -f "$base_dir/config/musica.conf") then
    echo "Error: config missing: $base_dir/config/musica.conf"
    exit 1
endif
source "$base_dir/config/musica.conf"

# verify environment
$base_dir/bin/musica_verify_env.csh
if ($status != 0) then
    echo "Environment verification failed."
    exit 1
endif

# input CSV
if ("$1" != "") then
    set csv_path = "$1"
else
    set csv_path = "$MUSICA_IMPORT_DIR/$MUSICA_DEFAULT_IMPORT"
endif

if (! -f "$csv_path") then
    echo "Import file not found: $csv_path"
    exit 1
endif

echo "Importing: $csv_path"

# prompt for header presence
echo -n "Does the file contain a header row? (y/N): "
set has_hdr = $<
if ("$has_hdr" == "y" || "$has_hdr" == "Y") then
    set ignore_clause = "IGNORE 1 LINES"
else
    set ignore_clause = ""
endif

# build and execute LOAD DATA
if ("$MUSICA_DB_PASS" == "") then
    set DBCLIENT = "sudo $MUSICA_DB_TYPE -D $MUSICA_DB_NAME --local-infile=1"
else
    set DBCLIENT = "$MUSICA_DB_TYPE -u $MUSICA_DB_USER -p$MUSICA_DB_PASS -D $MUSICA_DB_NAME --local-infile=1"
endif

echo "Executing LOAD DATA ..."
echo "LOAD DATA LOCAL INFILE '$csv_path' INTO TABLE recordings FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '\"' LINES TERMINATED BY '\n' $ignore_clause (artist,title,orchestra,conductor,year,genre,format,label,catalog_number,reissue,mode,dbx);" | eval $DBCLIENT

if ($status != 0) then
    echo "Import failed."
    exit 1
endif

# ensure import archive directory exists
if (! -d "$MUSICA_IMPORT_ARCHIVE_DIR") then
    mkdir -p "$MUSICA_IMPORT_ARCHIVE_DIR"
endif

# archive imported file
set ts = `date +"%Y%m%d_%H%M%S"`
set fname = `basename "$csv_path"`
set base = "$MUSICA_IMPORT_ARCHIVE_DIR/${fname:r}_$ts.csv"

mv "$csv_path" "$base"

echo "Import complete. Source archived as:"
echo "  $base"
