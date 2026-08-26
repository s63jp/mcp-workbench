#!/bin/bash
# Install the user-level systemd service for MCP Workbench.
set -e
export XDG_RUNTIME_DIR=/run/user/1000
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus
mkdir -p ~/.config/systemd/user
cp /home/kali/mcp-workbench/mcp-workbench.user.service ~/.config/systemd/user/mcp-workbench.service
systemctl --user daemon-reload
systemctl --user enable mcp-workbench.service
echo "SERVICE ENABLED"
systemctl --user status mcp-workbench.service --no-pager 2>&1 | head -5 || true
