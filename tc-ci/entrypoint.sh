#!/bin/sh

# Define the log file for the ClamAV scan report
SCAN_REPORT="/var/log/clamav_scan_report.txt"

# Create log directory if it doesn't exist
mkdir -p /var/log
rm -f "$SCAN_REPORT"

# Perform a ClamAV scan on the application directory
echo "Starting ClamAV scan..."
clamscan -r --bell -i /usr/src/app --log="$SCAN_REPORT"

# Capture the scan exit code
SCAN_EXIT_CODE=$?
echo "ClamAV scan completed with exit code: $SCAN_EXIT_CODE"

# Output the scan report if it exists
echo ""
echo "=== ClamAV Scan Report ==="
if [ -f "$SCAN_REPORT" ]; then
    cat "$SCAN_REPORT"
else
    echo "WARNING: Scan report file not found at $SCAN_REPORT"
fi
echo "=========================="

# Exit with scan result code (0 = no viruses, 1 = viruses found, 2 = error)
exit $SCAN_EXIT_CODE

