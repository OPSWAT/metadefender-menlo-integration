#!/bin/sh

# Define the log file for the ClamAV scan report
SCAN_REPORT="/var/log/clamav_scan_report.txt"

mkdir -p /var/log
rm -f "$SCAN_REPORT"

# Perform a ClamAV scan on the entire container's filesystem
echo "Starting ClamAV scan..."
clamscan -r --bell -i / --exclude-dir="^/proc" --exclude-dir="^/sys" --exclude-dir="^/dev" --exclude-dir="^/var/log" --log=$SCAN_REPORT

# Check the scan result and print it
echo "ClamAV scan completed. Report saved to $SCAN_REPORT."
cat $SCAN_REPORT
# Exit the container
exit 0