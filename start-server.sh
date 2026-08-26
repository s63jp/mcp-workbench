#!/bin/bash
# MCP Workbench Server Launcher
# Usage: ./start-server.sh
# Keeps running even after SSH/session disconnect

cd /home/kali/mcp-workbench

# Check if already running
if ss -tlnp | grep -q ':3460 '; then
    echo "Server already running on port 3460"
    echo "PID: $(pgrep -f 'server.py 3460')"
    exit 0
fi

# Kill any stale processes
pkill -f 'server.py 3460' 2>/dev/null
sleep 1

# Node/npx live under the Hermes node install; make sure the server can find them
export PATH="/home/kali/.hermes/node/bin:$PATH"

# Start with nohup so it survives disconnect
nohup python3 server.py 3460 >> /home/kali/mcp-workbench/logs/server.log 2>> /home/kali/mcp-workbench/logs/server_error.log &

echo "MCP Workbench server started on port 3460"
echo "Logs: logs/server.log"
echo "PID: $(pgrep -f 'server.py 3460')"
