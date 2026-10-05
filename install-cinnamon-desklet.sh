#!/bin/sh
set -eu

PROJECT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
DESKLET_ID="tasktracker@local"
DESKLET_DIR="$HOME/.local/share/cinnamon/desklets/$DESKLET_ID"
OLD_APPLET_DIR="$HOME/.local/share/cinnamon/applets/$DESKLET_ID"

install -d "$DESKLET_DIR"
install -m 644 "$PROJECT_DIR/desklets/$DESKLET_ID/desklet.js" "$DESKLET_DIR/desklet.js"
install -m 644 "$PROJECT_DIR/desklets/$DESKLET_ID/metadata.json" "$DESKLET_DIR/metadata.json"
install -m 644 "$PROJECT_DIR/desklets/$DESKLET_ID/settings-schema.json" "$DESKLET_DIR/settings-schema.json"
install -m 644 "$PROJECT_DIR/tasktracker.py" "$DESKLET_DIR/tasktracker.py"
install -m 644 "$PROJECT_DIR/tasktracker_ui.py" "$DESKLET_DIR/tasktracker_ui.py"
install -m 644 "$PROJECT_DIR/tasktracker_desklet_bridge.py" "$DESKLET_DIR/tasktracker_desklet_bridge.py"

if [ -d "$OLD_APPLET_DIR" ]; then
    rm -f "$OLD_APPLET_DIR/applet.js" "$OLD_APPLET_DIR/metadata.json"
    rm -f "$OLD_APPLET_DIR/tasktracker.py" "$OLD_APPLET_DIR/tasktracker_ui.py"
    rm -f "$OLD_APPLET_DIR/tasktracker_applet_bridge.py"
    rmdir "$OLD_APPLET_DIR" 2>/dev/null || true
fi

printf 'Installed TaskTracker desklet to %s\n' "$DESKLET_DIR"
printf 'Add it from System Settings > Desklets > Installed, then use Add to desktop.\n'
printf 'If the desklet does not appear, restart Cinnamon with Alt+F2, type r, and press Enter.\n'
