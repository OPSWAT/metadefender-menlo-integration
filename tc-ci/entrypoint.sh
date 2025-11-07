#!/bin/sh

SCAN_REPORT="/var/log/clamav_scan_report.txt"
mkdir -p /var/log
rm -f "$SCAN_REPORT"

echo "Starting ClamAV scan..."
clamscan -r --bell -i /usr/src/app --log="$SCAN_REPORT"

SCAN_EXIT_CODE=$?
echo "ClamAV scan completed with exit code: $SCAN_EXIT_CODE"
cat "$SCAN_REPORT"

exit $SCAN_EXIT_CODE

