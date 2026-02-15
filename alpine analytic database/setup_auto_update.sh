#!/bin/bash

# FIS Alpine Analytics - Auto Update Setup
# This script sets up weekly automatic database updates

set -e

echo "🏔️ FIS Alpine Analytics - Auto Update Setup"
echo "=============================================="
echo ""

# Get the absolute path to this directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
VENV_PYTHON="$PROJECT_ROOT/fis-api/venv/bin/python3"

echo "📂 Project root: $PROJECT_ROOT"
echo "🐍 Python: $VENV_PYTHON"
echo ""

# Check if virtual environment exists
if [ ! -f "$VENV_PYTHON" ]; then
    echo "❌ Error: Virtual environment not found at $VENV_PYTHON"
    echo "   Please create it first:"
    echo "   cd $PROJECT_ROOT/fis-api"
    echo "   python3 -m venv venv"
    echo "   source venv/bin/activate"
    echo "   pip install -r requirements.txt"
    exit 1
fi

echo "✅ Virtual environment found"
echo ""

# Create launchd plist
PLIST_DIR="$HOME/Library/LaunchAgents"
PLIST_FILE="$PLIST_DIR/com.fis.alpine.update.plist"

mkdir -p "$PLIST_DIR"

cat > "$PLIST_FILE" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.fis.alpine.update</string>

    <key>ProgramArguments</key>
    <array>
        <string>$VENV_PYTHON</string>
        <string>$SCRIPT_DIR/run_daily_update.py</string>
    </array>

    <key>WorkingDirectory</key>
    <string>$SCRIPT_DIR</string>

    <key>StartCalendarInterval</key>
    <dict>
        <key>Weekday</key>
        <integer>0</integer>
        <key>Hour</key>
        <integer>2</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>

    <key>StandardOutPath</key>
    <string>/tmp/fis-alpine-update.log</string>

    <key>StandardErrorPath</key>
    <string>/tmp/fis-alpine-update-error.log</string>

    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin</string>
    </dict>
</dict>
</plist>
EOF

echo "✅ Created launchd configuration at:"
echo "   $PLIST_FILE"
echo ""

# Load the launchd job
echo "⏰ Loading automatic update schedule..."
launchctl unload "$PLIST_FILE" 2>/dev/null || true
launchctl load "$PLIST_FILE"

if [ $? -eq 0 ]; then
    echo "✅ Automatic updates configured!"
    echo ""
    echo "📅 Update Schedule:"
    echo "   - Every Sunday at 2:00 AM"
    echo "   - Checks for new race data"
    echo "   - Updates database automatically"
    echo ""
    echo "📝 Logs:"
    echo "   - Output: /tmp/fis-alpine-update.log"
    echo "   - Errors: /tmp/fis-alpine-update-error.log"
    echo ""
    echo "🔍 Check status:"
    echo "   launchctl list | grep fis.alpine"
    echo ""
    echo "🛑 To stop automatic updates:"
    echo "   launchctl unload $PLIST_FILE"
    echo ""
    echo "✅ Setup complete!"
else
    echo "❌ Error: Failed to load launchd job"
    exit 1
fi
