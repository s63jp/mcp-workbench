#!/usr/bin/env python3
"""
Autonomous Dev.to posting for MCP Workbench
Uses free Dev.to API to publish articles about MCP and AI development.
"""
import json
import requests
import sys
import os
from datetime import datetime

API_KEY = os.environ.get("DEVTO_API_KEY", "z7oC3Psnc5TeduTRZPET1t3U")
BASE_URL = "https://dev.to/api"

def post_article(title, body, tags, published=False):
    """Post or draft an article on Dev.to."""
    headers = {
        "Content-Type": "application/json",
        "api-key": API_KEY
    }
    
    payload = {
        "article": {
            "title": title,
            "body_markdown": body,
            "tags": tags,
            "published": published
        }
    }
    
    resp = requests.post(f"{BASE_URL}/articles", headers=headers, json=payload)
    return resp.json()

def update_article(article_id, title=None, body=None, tags=None, published=None):
    """Update an existing article."""
    headers = {
        "Content-Type": "application/json",
        "api-key": API_KEY
    }
    
    payload = {"article": {}}
    if title: payload["article"]["title"] = title
    if body: payload["article"]["body_markdown"] = body
    if tags: payload["article"]["tags"] = tags
    if published is not None: payload["article"]["published"] = published
    
    resp = requests.put(f"{BASE_URL}/articles/{article_id}", headers=headers, json=payload)
    return resp.json()

def get_my_articles():
    """List my articles."""
    headers = {"api-key": API_KEY}
    resp = requests.get(f"{BASE_URL}/articles/me/all", headers=headers)
    return resp.json()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--title", help="Article title")
    parser.add_argument("--body", help="Markdown body (or path to .md file)")
    parser.add_argument("--tags", default="mcp,ai,devtools", help="Comma-separated tags")
    parser.add_argument("--publish", action="store_true", help="Publish immediately")
    parser.add_argument("--update", type=int, help="Update article ID")
    parser.add_argument("--list", action="store_true", help="List my articles")
    args = parser.parse_args()
    
    if args.list:
        articles = get_my_articles()
        for a in articles[:5]:
            status = "PUBLISHED" if a.get("published") else "DRAFT"
            print(f"[{status}] {a['id']}: {a['title']}")
    elif args.update:
        body = open(args.body).read() if os.path.exists(args.body) else args.body
        result = update_article(args.update, args.title, body, args.tags.split(","), args.publish)
        print(json.dumps(result, indent=2))
    elif args.title and args.body:
        body = open(args.body).read() if os.path.exists(args.body) else args.body
        result = post_article(args.title, body, args.tags.split(","), args.publish)
        print(json.dumps(result, indent=2))
    else:
        print("Usage: python3 devto_post.py --title 'My Title' --body 'content.md' --tags 'mcp,ai'")
