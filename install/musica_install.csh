#!/bin/csh

# ------------------------------------------------------------
# Musica – Installation / Upgrade Script (C-Shell)
# Phase 2 Requirements:
#   * Create /opt/Musica if missing
#   * Copy project directories into /opt/Musica
#   * Compare VERSION file with existing installation
#   * Skip or upgrade based on version
# ------------------------------------------------------------

set app_root = "/opt/Musica"
set src_root = `pwd`

echo "-------------------------------------------------------------"
echo "        Musica – Installation / Upgrade Script"
echo "                 (C-Shell, Phase 2)"
echo "-------------------------------------------------------------"
echo ""

# ----------------- Root Permission Check ---------------------
set uid = `id -u`
if ( $uid != 0 ) then
    echo "ERROR: Root access is required to install into /opt."
    echo "Run again using:"
    echo "    sudo $0"
    exit 1
endif

# ----------------- Validate Source VERSION -------------------
if ( ! -f "$src_root/VERSION" ) then
    echo "ERROR: VERSION file missing in the source directory:"
    echo "       $src_root"
    echo "Aborting installation."
    exit 1
endif

set new_version = `cat $src_root/VERSION`

echo "Source VERSION: $new_version"

# ----------------- Determine Installation State --------------
set install_state = "new"

if ( -d "$app_root" ) then
    echo "Existing installation detected in $app_root"

    if ( -f "$app_root/VERSION" ) then
        set old_version = `cat $app_root/VERSION`
        echo "Installed VERSION: $old_version"
        set install_state = "upgrade"
    else
        echo "WARNING: No VERSION file found in existing installation."
        set install_state = "upgrade"
    endif
else
    echo "No installation found. Creating new installation."
endif

# ----------------- Version Comparison -------------------------
# NOTE: simple string compare; future versions can include semantic parsing

if ( "$install_state" == "upgrade" ) then
    if ( "$old_version" == "$new_version" ) then
        echo "-------------------------------------------------------------"
        echo "Musica $old_version is already installed."
        echo "Same version detected. Installation skipped."
        echo "-------------------------------------------------------------"
        exit 0
    endif

    if ( "$old_version" > "$new_version" ) then
        echo "-------------------------------------------------------------"
        echo "WARNING: Installed version ($old_version) is NEWER than release ($new_version)."
        echo "Upgrade not performed."
        echo "-------------------------------------------------------------"
        exit 1
    endif

    echo "Upgrade allowed: $old_version → $new_version"
endif

# ----------------- Create Directory Tree ----------------------
alias makedir 'if ( ! -d \!:1 ) mkdir -p \!:1 ; echo "Created: \!:1"'

makedir $app_root

# The full directory tree you provided
set dirs = ( \
    admin archive bin config data db docs install RELEASES sql tests web \
    data/archive data/exports data/imports \
    web/api web/css web/html web/js \
    Muscia_dev Muscia_dev/maint_scripts Muscia_dev/op_scripts Muscia_dev/UI_scripts \
    logs \
)

foreach d ( $dirs )
    makedir "$app_root/$d"
end

# ----------------- Copy Contents ------------------------------
echo ""
echo "Copying project directories into installation target..."

foreach d ( admin archive bin config data db docs install RELEASES sql tests web )
    if ( -d "$src_root/$d" ) then
        echo "Copying directory: $d"
        cp -R $src_root/$d/* $app_root/$d/ >& /dev/null
    endif
end

# ----------------- Copy VERSION -------------------------------
echo "Copying VERSION file..."
cp $src_root/VERSION $app_root/VERSION

echo ""
echo "-------------------------------------------------------------"
if ( "$install_state" == "new" ) then
    echo "Musica successfully installed. Version: $new_version"
else
    echo "Musica successfully upgraded to Version: $new_version"
endif
echo "-------------------------------------------------------------"

exit 0

