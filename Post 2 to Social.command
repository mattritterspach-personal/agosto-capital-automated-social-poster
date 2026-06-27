#!/bin/bash
# Double-click to post the next 2 queued Agosto Studio posts to IG, FB, and TikTok.
cd "$(dirname "$0")"
python3 agosto_run.py "$@"
echo ""
echo "If the queue is getting low, ask Claude to generate more posts."
read -p "Press Enter to close this window..."
