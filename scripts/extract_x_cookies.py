#!/usr/bin/env python3
"""
Extract fresh Firefox session cookies for X/Twitter.
Run this before any X automation to get current auth tokens.
"""
import sqlite3
import shutil
import os
import json

def get_x_cookies():
    """Extract X auth cookies from Firefox."""
    firefox_db = "/home/kali/.mozilla/firefox/teveem2z.default-esr/cookies.sqlite"
    temp_db = "/tmp/cookies_extract.sqlite"
    
    try:
        shutil.copy2(firefox_db, temp_db)
    except Exception as e:
        print(f"ERROR: Cannot copy Firefox cookies: {e}")
        return None
    
    try:
        conn = sqlite3.connect(temp_db)
        c = conn.cursor()
        c.execute("SELECT name, value FROM moz_cookies WHERE host LIKE '%x.com%' AND name IN ('auth_token','ct0','gt','twid')")
        cookies = {row[0]: row[1] for row in c.fetchall()}
        conn.close()
        
        if 'auth_token' not in cookies:
            print("ERROR: No auth_token found. User needs to log in to X in Firefox.")
            return None
            
        return cookies
    except Exception as e:
        print(f"ERROR: Failed to query cookies: {e}")
        return None

if __name__ == "__main__":
    cookies = get_x_cookies()
    if cookies:
        print(json.dumps(cookies, indent=2))
    else:
        exit(1)
