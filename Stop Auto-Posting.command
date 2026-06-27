#!/bin/bash
# Double-click to turn OFF automatic daily posting.
cd "$(dirname "$0")"
DEST="$HOME/Library/LaunchAgents/com.agosto.socialposter.plist"
launchctl unload "$DEST" 2>/dev/null
rm -f "$DEST"
echo "Auto-posting is OFF. You can still post manually with 'Post 2 to Social.command'."
echo ""
read -p "Press Enter to close..."
