#!/bin/bash
# Double-click ONCE to turn on automatic daily posting (2 posts/platform at 10am).
# Double-click "Stop Auto-Posting.command" to turn it off.
cd "$(dirname "$0")"
PLIST="com.agosto.socialposter.plist"
DEST="$HOME/Library/LaunchAgents/$PLIST"
mkdir -p "$HOME/Library/LaunchAgents"
cp "$PLIST" "$DEST"
launchctl unload "$DEST" 2>/dev/null
launchctl load "$DEST"
echo "Auto-posting is ON: 2 posts per platform every day at 10:00am."
echo "It posts the next items from content_queue.json. Logs: posting.log"
echo ""
read -p "Press Enter to close..."
