#!/bin/sh

# Define the log file for the ClamAV scan report (use /tmp to avoid permission issues)
SCAN_REPORT="/tmp/clamav_scan_report.txt"

# Remove old log file if it exists to avoid locking issues
rm -f "$SCAN_REPORT"

# Perform a ClamAV scan on the entire container's filesystem
echo "Starting ClamAV scan..."
clamscan -r --bell -i / --exclude-dir="^/proc" --exclude-dir="^/sys" --exclude-dir="^/dev" --exclude-dir="^/tmp" --log="$SCAN_REPORT"

# Check the scan result and print it
echo "ClamAV scan completed. Report saved to $SCAN_REPORT."
cat $SCAN_REPORT

# Start the application
echo "Starting the application..."
exec python3 -m metadefender_menlo
