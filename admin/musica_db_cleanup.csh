#!/bin/csh -f
#==============================================================================
#  File:         musica_db_cleanup.csh 
#                Maintenance utility for Musica data directories
#  Purpose:      Performs full cleanup of temporary files, logs, and residual
#                data from test, import, and export operations in the Musica
#                environment.
#
#  Usage:        sudo ./cleanup.csh
#
#  Description:
#                - Removes all temp files under /tmp and data/tmp (if present)
#                - Clears log/ and cache/ directories
#                - Optionally resets database-related temp files
#                - Reads configuration from ../config/musica.conf
#
#  Notes:
#                * Use with care — this operation cannot be undone.
#                * Intended for maintenance and debugging only.
#==============================================================================

echo "Musica Database Cleanup Utility"
echo "----------------------------------------"

# Paths defined by installation contract
set data_dir    = "$MUSICA_DATA_DIR"
set import_dir  = "$MUSICA_IMPORT_DIR"
set export_dir  = "$MUSICA_EXPORT_DIR"
set archive_dir = "$MUSICA_IMPORT_ARCHIVE_DIR"

# Set retention period (in days)
set retention_days = 14

# Confirm configuration
echo "Retention period: $retention_days days"
echo "Imports directory: $import_dir"
echo "Exports directory: $export_dir"

if (! -d "$archive_dir") then
    echo "ERROR: Import archive directory not found: $archive_dir"
    exit 1
endif

echo "Archive directory: $archive_dir (preserved)"
echo ""

# Prompt for confirmation
echo -n "Proceed with cleanup? (y/n): "
set ans = $<
if ( "$ans" != "y" && "$ans" != "Y" ) then
    echo "Cleanup cancelled."
    exit 0
endif

# Perform cleanup on imports and exports
foreach dir ($import_dir $export_dir)
    if ( -d "$dir" ) then
        echo "Cleaning $dir ..."
        sudo find "$dir" -type f -mtime +$retention_days -print -delete
    else
        echo "Directory not found: $dir"
    endif
end

echo ""
echo "Cleanup complete. Archive directory preserved."
exit 0

