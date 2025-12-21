#!/bin/csh -f
#
# Phase 3A — MariaDB Environment Check & Optional Installation
# Supports OS argument, auto-detection, or interactive menu.
#

######### N E W ##################
# ------------------------------------------------------------
# Load configuration (must be first)
# ------------------------------------------------------------
if (! $?MUSICA_BASE_DIR) then
    if (-f "$0:h/../config/musica.conf") then
        source "$0:h/../config/musica.conf"
    else
        echo "ERROR: musica.conf not found"
        exit 1
    endif
endif

# NOTE:
# Phase 3A validates system prerequisites only.
# Database creation and authentication occur in Phase 3B.

# Runtime MUSICA operations do NOT use the root account.

set db_exists = 0

# ----------------------------------------------
# Correct csh-safe script path & base_dir setup
# ----------------------------------------------
if ($#argv >= 1) then
    set script_name = "$argv[0]"
else
    set script_name = "musica_db_check_env.csh"
endif

set script_path = "`pwd`/$script_name"
set script_dir  = `dirname "$script_path"`
set base_dir    = `cd "$script_dir/.."; pwd`

set log_dir  = "$MUSICA_BASE_DIR/logs"
set log_file = "$log_dir/db_env_check.log"

if (! -d "$log_dir") then
    mkdir -p "$log_dir"
endif

alias logprint 'echo "\!*" |& tee "$log_file"'
alias logerror 'echo "ERROR: \!*" |& tee "$log_file"' ## <---

echo "===== Phase 3A: MariaDB Environment Check =====" |& tee "$log_file"
echo "Started: `date`" |& tee "$log_file"

# ----------------------------
# STEP 1 — OS argument check
# ----------------------------
set os_arg = ""
if ($#argv >= 2) then
    set os_arg = "$argv[1]"
    logprint "OS argument supplied: $os_arg"
endif

# ----------------------------
# STEP 2 — Auto-detect OS
# ----------------------------
set os_detect = ""

if ("$os_arg" == "") then
    if (-f /etc/os-release) then
        set idline = `grep "^ID=" /etc/os-release | sed 's/ID=//' | tr -d '"'`
        if ("$idline" != "") then
            set os_detect = "$idline"
            logprint "Auto-detected OS: $os_detect"
        endif
    endif
endif

# ----------------------------------------
# STEP 3 — User menu if detection fails
# ----------------------------------------
if ("$os_arg" == "" && "$os_detect" == "") then
    logprint "OS auto-detect failed — prompting user."
    echo ""
    echo "Select your operating system:"
    echo "1) Debian / Ubuntu"
    echo "2) RHEL / CentOS"
    echo "3) Fedora"
    echo "4) openSUSE"
    echo "5) Arch"
    echo "6) macOS"
    echo "7) Cancel"
    echo -n "Enter choice [1-7]: "
    set choice = $<

    switch ($choice)
        case 1:
            set os_detect = "debian"
            breaksw
        case 2:
            set os_detect = "rhel"
            breaksw
        case 3:
            set os_detect = "fedora"
            breaksw
        case 4:
            set os_detect = "opensuse"
            breaksw
        case 5:
            set os_detect = "arch"
            breaksw
        case 6:
            set os_detect = "macos"
            breaksw
        default:
            logprint "User cancelled. Exiting."
            exit 1
    endsw
endif

# final OS choice
if ("$os_arg" != "") then
    set os = "$os_arg"
else
    set os = "$os_detect"
endif

logprint "Using OS setting: $os"
echo ""

# ----------------------------------------
# STEP 4 — Check MariaDB client presence
# ----------------------------------------
logprint "Checking MariaDB client tools..."

set mariadb_cmd = `which mariadb`

if ("$mariadb_cmd" == "") then
    set client_ok = 0
else
    set client_ok = 1
endif

if ($client_ok == 1) then
    logprint "MariaDB client found: $mariadb_cmd"
else
    logprint "MariaDB client NOT found."

    echo -n "Install MariaDB now? (y/n): "
    set install_ans = $<
    if ("$install_ans" != "y" && "$install_ans" != "Y") then
        logprint "User declined MariaDB install. Aborting."
        exit 1
    endif

    logprint "User approved MariaDB installation."

    switch ($os)
        case debian:
        case ubuntu:
            sudo apt update |& tee "$log_file"
            sudo apt install -y mariadb-server mariadb-client |& tee "$log_file"
            breaksw

        case rhel:
        case centos:
            sudo yum install -y mariadb-server mariadb |& tee "$log_file"
            breaksw

        case fedora:
            sudo dnf install -y mariadb-server mariadb |& tee "$log_file"
            breaksw

        case opensuse:
            sudo zypper install -y mariadb |& tee "$log_file"
            breaksw

        case arch:
            sudo pacman -Sy --noconfirm mariadb |& tee file"
            breaksw

        case macos:
            brew install mariadb |& tee "$log_file"
            breaksw

        default:
            logprint "ERROR: Unsupported OS: $os"
            exit 1
    endsw
endif

# ----------------------------------------
# STEP 5 — Ensure MariaDB server is running
# ----------------------------------------
logprint "Checking MariaDB service status..."

#set svc_status = `systemctl is-active mariadb 2>/dev/null`
set svc_status = `systemctl is-active mariadb`

if ("$svc_status" != "active") then
    echo "MariaDB is not running."
    echo -n "Start MariaDB now? (y/n): "
    set start_ans = $<
    if ("$start_ans" == "y" || "$start_ans" == "Y") then
        sudo systemctl start mariadb |& tee "$log_file"
    else
        logprint "User declined to start MariaDB. Exiting."
        exit 1
    endif
else
    logprint "MariaDB service is active."
endif

# ----------------------------------------
# STEP 6 — Database checks deferred
# ----------------------------------------
logprint "Database checks deferred to Phase 3B."


# ----------------------------------------
# STEP 7 — Check if Musica DB exists
# Core environment validation
# ------------------------------------------------------------
set fail = 0

# validate base dirs

# ------------------------------------------------------------
# Import archive directory (admin-managed)
# ------------------------------------------------------------

# ------------------------------------------------------------
# Final gate
# ------------------------------------------------------------
if ($fail) then
    logerror "Environment verification failed"
    exit 1
endif

logprint "Phase 3A complete. Environment ready for Phase 3B."
exit 0

