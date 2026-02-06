echo ""
echo "To confirm, type exactly:  uninstall musica"
echo -n "Confirmation: "
set ans = $<

if ( "$ans" != "uninstall musica" ) then
    echo "Incorrect confirmation. Uninstall aborted." | tee -a "$log_file"
    exit 0
endif

echo "Confirmation accepted." | tee -a "$log_file"

# ---------- Perform uninstall ----------
echo "Removing $app_root..." | tee -a "$log_file"
rm -rf "$app_root"

if ( -d "$app_root" ) then
    echo "ERROR: Failed to remove $app_root" | tee -a "$log_file"
    exit 1
endif

echo "Musica successfully uninstalled." | tee -a "$log_file"
echo "Uninstall completed at `date`" | tee -a "$log_file"

echo ""
echo "Musica has been uninstalled."
echo "Log saved to: $log_file"
echo ""

exit 0

