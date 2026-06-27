#!/bin/bash
# Double-click this file to post the next 2 queued posts to IG, FB, and TikTok.
cd "$(dirname "$0")"
python3 agosto_run.py "$@"
echo ""
read -p "Press Enter to close this window..."
