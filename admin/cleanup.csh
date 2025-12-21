#!/bin/csh
# cleanup.csh — remove backup and temporary files safely

echo "Cleaning up temporary files..."
find . \( -name "*~" -o -name "*.bak" -o -name "#*#" -o -name "*.tmp" \) -exec rm -f {} \;
echo "Cleanup complete."

