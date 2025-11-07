#!/bin/sh

set -e

echo "Building ClamAV scan image..."
docker build -f Dockerfile-AV -t menlo-clamav .

echo "Starting container for ClamAV scan..."
CONTAINER_ID=$(docker run -d menlo-clamav)

echo "Container started: $CONTAINER_ID"
echo "Waiting for scan to complete..."
sleep 120

echo "Copying scan report..."
docker cp "$CONTAINER_ID:/var/log/clamav_scan_report.txt" ./clamav_scan_report.txt

echo ""
echo "=== ClamAV Scan Report ==="
cat ./clamav_scan_report.txt
echo "=========================="

echo "Stopping and removing container..."
docker stop "$CONTAINER_ID"
docker rm "$CONTAINER_ID"

echo "ClamAV scan completed. Container $CONTAINER_ID stopped and removed."
