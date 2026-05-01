#!/bin/bash
#
# Download new power logs from the roboRIO to power_logs/.
# Only fetches files that are not already present locally.
#
# Usage:  ./cli/commands/download_power_logs.sh
#         (or via the Robot menu in ./team)
#

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
LOCAL_DIR="$PROJECT_DIR/power_logs"
REMOTE_HOST="admin@10.97.71.2"
REMOTE_DIR="/home/lvuser/power_logs"

# Colors (standalone-safe)
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m'

mkdir -p "$LOCAL_DIR"

echo ""
echo -e "${BOLD}Connecting to roboRIO at ${REMOTE_HOST}...${NC}"
echo ""

# List remote files (just filenames, one per line)
remote_files=$(ssh -o ConnectTimeout=5 -o BatchMode=yes "$REMOTE_HOST" \
    "ls $REMOTE_DIR/*.csv 2>/dev/null" 2>/dev/null)

if [ $? -ne 0 ]; then
    echo -e "${RED}Could not connect to the roboRIO.${NC}"
    echo ""
    echo "  Make sure you are on the robot network (USB or WiFi)"
    echo "  and the robot is powered on."
    exit 1
fi

if [ -z "$remote_files" ]; then
    echo -e "${YELLOW}No power log CSVs found on the roboRIO.${NC}"
    exit 0
fi

# Figure out which files we already have
new_count=0
to_download=()

for remote_path in $remote_files; do
    filename=$(basename "$remote_path")
    if [ ! -f "$LOCAL_DIR/$filename" ]; then
        to_download+=("$remote_path")
        new_count=$((new_count + 1))
    fi
done

if [ "$new_count" -eq 0 ]; then
    total=$(echo "$remote_files" | wc -l | xargs)
    echo -e "${GREEN}All $total log(s) already downloaded. Nothing new.${NC}"
    exit 0
fi

echo -e "Found ${BOLD}${new_count}${NC} new log(s) to download."
echo ""

# Download each new file
downloaded=0
for remote_path in "${to_download[@]}"; do
    filename=$(basename "$remote_path")
    echo -n "  $filename ... "
    if scp -o ConnectTimeout=5 -q "$REMOTE_HOST:$remote_path" "$LOCAL_DIR/$filename" 2>/dev/null; then
        echo -e "${GREEN}OK${NC}"
        downloaded=$((downloaded + 1))
    else
        echo -e "${RED}FAILED${NC}"
    fi
done

echo ""
echo -e "${GREEN}Downloaded $downloaded new log(s) to power_logs/${NC}"
