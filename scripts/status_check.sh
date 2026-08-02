#!/bin/bash
# MCP Workbench Status Check Script
# Usage: bash /home/kali/mcp-workbench/scripts/status_check.sh

echo "=== MCP Workbench Status Check ==="
echo "Timestamp: $(date)"
echo ""

# Server Health
echo "1. Server Health:"
curl -s http://localhost:3460/api/health 2>/dev/null || echo "   ❌ Server not responding"
echo ""

# Beta Signups
echo "2. Beta Signups:"
if [ -d /home/kali/mcp-workbench/beta-signups ]; then
    COUNT=$(ls /home/kali/mcp-workbench/beta-signups/ | wc -l)
    echo "   Total signups: $COUNT"
    if [ $COUNT -gt 0 ]; then
        echo "   Recent signups:"
        ls -t /home/kali/mcp-workbench/beta-signups/ | head -3 | while read f; do
            cat "/home/kali/mcp-workbench/beta-signups/$f" | grep '"email"' | head -1
        done
    fi
else
    echo "   No signups yet"
fi
echo ""

# Process Status
echo "3. Processes:"
ps aux | grep -E "python3.*server|cloudflared" | grep -v grep
echo ""

# Disk Space
echo "4. Disk Space:"
df -h /home | tail -1
echo ""

# Memory
echo "5. Memory:"
free -h | grep Mem
echo ""

echo "=== End Status Check ==="
