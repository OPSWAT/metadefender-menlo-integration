#!/bin/sh

SCAN_REPORT="/var/log/clamav_scan_report.txt"
clamscan -r --bell -i /usr/src/app --log="$SCAN_REPORT"

echo "ClamAV Scan Report:"
cat "$SCAN_REPORT"

exit 0