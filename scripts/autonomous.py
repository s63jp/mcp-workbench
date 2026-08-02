#!/usr/bin/env python3
"""
Autonomous MCP Workbench Development Script
Runs autonomously to continue project work while user is away.
"""
import json
import os
import subprocess
import time
import sys

PROJECT_DIR = "/home/kali/mcp-workbench"
LOG_FILE = f"{PROJECT_DIR}/logs/autonomous.log"

def log(msg):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] {msg}"
    print(entry)
    os.makedirs(f"{PROJECT_DIR}/logs", exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(entry + "\n")

def run_cmd(cmd, timeout=30):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Timeout"

def check_server_health():
    log("=== Checking Server Health ===")
    rc, out, err = run_cmd("curl -s http://localhost:3460/api/health")
    if rc == 0:
        log(f"✅ Server healthy: {out.strip()}")
        return True
    else:
        log("❌ Server not responding")
        return False

def check_beta_signups():
    log("=== Checking Beta Signups ===")
    signup_dir = f"{PROJECT_DIR}/beta-signups"
    if os.path.isdir(signup_dir):
        files = os.listdir(signup_dir)
        log(f"✅ Total beta signups: {len(files)}")
        if files:
            # Show recent ones
            recent = sorted(files, reverse=True)[:3]
            for f in recent:
                try:
                    with open(f"{signup_dir}/{f}") as fh:
                        data = json.load(fh)
                        log(f"   - {data.get('email', 'unknown')} | Tools: {data.get('tools', 'N/A')}")
                except:
                    pass
    else:
        log("No signups directory yet")

def check_twitter_notifications():
    log("=== Checking X/Twitter ===")
    # This would need browser automation - skip for now
    log("⏭️  Skipping X check (requires browser session)")

def development_tasks():
    log("=== Running Development Tasks ===")
    
    # Task 1: Check if landing page exists and is accessible
    beta_page = f"{PROJECT_DIR}/public/beta.html"
    if os.path.exists(beta_page):
        log("✅ Beta landing page exists")
    else:
        log("❌ Beta landing page missing!")
    
    # Task 2: Check server.py syntax
    rc, out, err = run_cmd(f"python3 -m py_compile {PROJECT_DIR}/server.py")
    if rc == 0:
        log("✅ Server.py syntax OK")
    else:
        log(f"❌ Server.py syntax error: {err}")
    
    # Task 3: Check for any error logs
    log_dir = f"{PROJECT_DIR}/logs"
    if os.path.isdir(log_dir):
        for fname in os.listdir(log_dir):
            if fname.endswith('.jsonl'):
                fpath = f"{log_dir}/{fname}"
                # Count error lines
                rc, out, _ = run_cmd(f"grep -c 'error' {fpath} 2>/dev/null || echo 0")
                try:
                    count = int(out.strip())
                    if count > 0:
                        log(f"⚠️  {fname} has {count} error entries")
                except:
                    pass

def main():
    log("🚀 Starting autonomous MCP Workbench session")
    
    health_ok = check_server_health()
    check_beta_signups()
    check_twitter_notifications()
    development_tasks()
    
    log("✅ Autonomous session complete")
    log("")

if __name__ == "__main__":
    main()
