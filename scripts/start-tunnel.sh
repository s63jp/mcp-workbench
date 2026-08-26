#!/bin/bash
# Start Cloudflare tunnel for MCP Workbench
cd /home/kali/.cloudflared
cloudflared tunnel run --credentials-file 747f9c89-3c1c-4867-9156-c01a15404efc.json 747f9c89-3c1c-4867-9156-c01a15404efc
