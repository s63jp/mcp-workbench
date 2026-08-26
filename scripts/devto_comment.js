#!/usr/bin/env node
/**
 * Post comments on Dev.to using Firefox cookies.
 * Extracts cookies from your Firefox profile and posts comments via Playwright.
 */
const { chromium } = require('playwright');
const sqlite3 = require('sqlite3').verbose();

const COOKIE_SQLITE = "/tmp/devto_cookies.sqlite";

async function extractCookies() {
    return new Promise((resolve, reject) => {
        const db = new sqlite3.Database(COOKIE_SQLITE);
        db.all("SELECT name, value, host, path, isSecure FROM moz_cookies WHERE host LIKE '%dev.to%'", [], (err, rows) => {
            db.close();
            if (err) reject(err);
            else resolve(rows);
        });
    });
}

async function postComments() {
    console.log("Extracting cookies from Firefox...");
    const cookies = await extractCookies();
    console.log(`Got ${cookies.length} cookies`);
    
    // Launch browser with extracted cookies
    const browser = await chromium.launch({ headless: true });
    const context = await browser.newContext();
    
    // Add cookies
    for (const cookie of cookies) {
        try {
            await context.addCookies([{
                name: cookie.name,
                value: cookie.value,
                domain: cookie.host.startsWith('.') ? cookie.host.slice(1) : cookie.host,
                path: cookie.path || '/',
                secure: cookie.isSecure === 1
            }]);
        } catch (e) {
            // Skip invalid cookies
        }
    }
    
    const page = await context.newPage();
    
    // Articles to comment on (found from earlier check - all have comments)
    const articles = [
        {
            slug: 'jaypee_2de6db397980219fcd/how-to-debug-mcp-server-connection-issues-in-60-seconds-18bd',
            comment: "Great points from both of you! Reid - you're right about the protocol state issue after the Jul 28 MCP draft. Bartek - the session id reuse problem is exactly what our compatibility reports aim to catch. MCP Workbench tests across multiple clients including forced reconnects to catch exactly these issues. We'd love to feature your servers in our directory at https://mcp-workbench.uk"
        }
    ];
    
    for (const article of articles) {
        try {
            console.log(`Posting on: ${article.slug}`);
            await page.goto(`https://dev.to/${article.slug}`, { waitUntil: 'networkidle', timeout: 30000 });
            
            // Wait for textarea
            await page.waitForSelector('textarea', { timeout: 10000 });
            
            // Fill comment
            await page.fill('textarea', article.comment);
            
            // Submit with Ctrl+Enter
            await page.keyboard.press('Control+Enter');
            await page.waitForTimeout(3000);
            
            console.log(`✅ Posted on ${article.slug}`);
        } catch (e) {
            console.error(`❌ Error on ${article.slug}: ${e.message}`);
        }
    }
    
    await browser.close();
    console.log("Done!");
}

postComments().catch(console.error);
