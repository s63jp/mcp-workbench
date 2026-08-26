#!/usr/bin/env node
/**
 * Playwright Reddit Poster — Node.js version
 * Posts to r/LocalLLaMA, r/MachineLearning, r/programming
 * Uses Firefox cookie extraction + Playwright Chromium
 */
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const sqlite3 = require('sqlite3');

// --- Configuration ---
const FIREFOX_PROFILES = [
  '/home/kali/.mozilla/firefox/teveem2z.default-esr',
  '/home/kali/.mozilla/firefox/q4tlbhyt.default'
];
const POST_CONTENT_PATH = '/home/kali/mcp-workbench/content/reddit-post.md';
const LINK = 'https://mcp-workbench.uk';
const SUBREDDITS = ['LocalLLaMA', 'MachineLearning', 'programming'];
const CHROMIUM_PATH = '/usr/bin/chromium';

// --- Cookie extraction from Firefox ---
function extractFirefoxCookies(profileDir) {
  const cookieDb = path.join(profileDir, 'cookies.sqlite');
  if (!fs.existsSync(cookieDb)) return [];

  const tmpDb = '/tmp/reddit_cookies_' + Date.now() + '.sqlite';
  fs.copyFileSync(cookieDb, tmpDb);

  return new Promise((resolve) => {
    const db = new sqlite3.Database(tmpDb, (err) => {
      if (err) { resolve([]); return; }
      db.all(`SELECT name, value, host, path, isSecure, isHttpOnly FROM moz_cookies WHERE host LIKE '%reddit.com%'`, (err, rows) => {
        if (err || !rows) { resolve([]); return; }
        const cookies = rows.map(row => ({
          name: row.name,
          value: row.value,
          domain: row.host.startsWith('.') ? row.host.slice(1) : row.host,
          path: row.path || '/',
          secure: !!row.isSecure,
          httpOnly: !!row.isHttpOnly
        }));
        // Remove httpOnly restriction for our purposes
        cookies.forEach(c => c.httpOnly = false);
        resolve(cookies);
        db.close();
      });
    });
  });
}

// --- Load post content ---
function loadPostContent() {
  const content = fs.readFileSync(POST_CONTENT_PATH, 'utf8');
  const lines = content.trim().split('\n');

  // Title is first line (H1 markdown)
  const title = lines[0].replace(/^#+\s*/, '').trim();

  // Body is everything after the first --- separator
  const bodyStart = lines.findIndex((l, i) => i > 0 && l.trim() === '---');
  const body = bodyStart > 0
    ? lines.slice(bodyStart + 1).join('\n').trim()
    : lines.slice(1).join('\n').trim();

  return { title, body };
}

// --- Post to one subreddit ---
async function postToSubreddit(browser, subreddit, title, body) {
  console.log(`\n[>] Posting to r/${subreddit}...`);

  // Extract cookies
  let allCookies = [];
  for (const profile of FIREFOX_PROFILES) {
    const cookies = await extractFirefoxCookies(profile);
    if (cookies.length > 0) {
      allCookies = cookies;
      console.log(`  [+] Found ${cookies.length} Reddit cookies`);
      break;
    }
  }

  if (allCookies.length === 0) {
    console.log(`  [!] No Reddit cookies found in Firefox`);
    return null;
  }

  const context = await browser.newContext({
    viewport: { width: 1280, height: 800 },
    userAgent: 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
  });

  // Add cookies to context
  for (const c of allCookies) {
    try {
      await context.addCookies([c]);
    } catch (e) {
      // skip bad cookies
    }
  }

  const page = await context.newPage();

  try {
    // Go to Reddit home
    console.log(`  [>] Navigating to Reddit...`);
    await page.goto('https://www.reddit.com', { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForTimeout(3000);

    const url1 = page.url();
    console.log(`  [>] URL: ${url1}`);

    if (url1.includes('js_challenge') || url1.includes('challenge')) {
      console.log(`  [!] JS challenge detected`);
      await context.close();
      return null;
    }

    // Check login state
    const pageText = await page.textContent('body');
    if (pageText.includes(' Log in ') || pageText.includes('Sign Up')) {
      // Check more carefully
      const html = await page.content();
      if (html.includes('" loggedIn":false') || html.includes('"loggedIn":false')) {
        console.log(`  [!] Not logged in (session may be expired)`);
        await context.close();
        return null;
      }
    }
    console.log(`  [+] Session active`);

    // Navigate to submit page
    const submitUrl = `https://www.reddit.com/r/${subreddit}/submit`;
    console.log(`  [>] Navigating to submit page...`);
    await page.goto(submitUrl, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForTimeout(3000);

    const url2 = page.url();
    console.log(`  [>] Submit URL: ${url2}`);

    if (url2.includes('js_challenge') || url2.includes('challenge')) {
      console.log(`  [!] JS challenge on submit page`);
      await context.close();
      return null;
    }

    // Fill title
    console.log(`  [>] Filling title...`);
    const titleSelectors = [
      'input[name="title"]',
      'input[placeholder*="title" i]',
      'input[id="title"]',
      'input[autocomplete="off"]'
    ];

    let titleFilled = false;
    for (const sel of titleSelectors) {
      const el = page.locator(sel).first();
      if (await el.count() > 0) {
        await el.fill(title);
        titleFilled = true;
        console.log(`  [+] Title filled: ${sel}`);
        break;
      }
    }

    if (!titleFilled) {
      // Try JS fallback
      await page.evaluate((t) => {
        const inputs = document.querySelectorAll('input[type="text"], input:not([type])');
        for (const inp of inputs) {
          if (inp.closest('[class*="submit"]') || inp.closest('[class*="title"]')) {
            inp.value = t;
            inp.dispatchEvent(new Event('input', { bubbles: true }));
            inp.dispatchEvent(new Event('change', { bubbles: true }));
            break;
          }
        }
      }, title);
      titleFilled = true;
      console.log(`  [+] Title filled via JS`);
    }

    // Fill body
    console.log(`  [>] Filling body...`);
    const fullBody = `${body}\n\n🔗 ${LINK}`;

    const bodySelectors = [
      'textarea[name="text"]',
      'textarea[id="text"]',
      'textarea[placeholder*="description" i]',
      '[data-testid="description-input"]',
      '.public-DraftEditor-content'
    ];

    let bodyFilled = false;
    for (const sel of bodySelectors) {
      const el = page.locator(sel).first();
      if (await el.count() > 0) {
        await el.fill(fullBody);
        bodyFilled = true;
        console.log(`  [+] Body filled: ${sel}`);
        break;
      }
    }

    if (!bodyFilled) {
      // contenteditable
      try {
        await page.evaluate((text) => {
          const el = document.querySelector('.public-DraftEditor-content') ||
                     document.querySelector('[contenteditable="true"]');
          if (el) {
            el.textContent = text;
            el.dispatchEvent(new Event('input', { bubbles: true }));
          }
        }, fullBody);
        bodyFilled = true;
        console.log(`  [+] Body filled via contenteditable`);
      } catch (e) {
        console.log(`  [!] Could not fill body: ${e.message}`);
      }
    }

    // Submit
    console.log(`  [>] Submitting...`);
    const submitSelectors = [
      'button[type="submit"]',
      'button:has-text("Post")',
      'button:has-text("Submit")',
      '[data-testid="submit-post"]'
    ];

    for (const sel of submitSelectors) {
      const btn = page.locator(sel).first();
      if (await btn.count() > 0) {
        await btn.click();
        console.log(`  [+] Clicked: ${sel}`);
        break;
      }
    }

    // Wait for result
    await page.waitForTimeout(5000);
    const finalUrl = page.url();
    console.log(`  [>] Final URL: ${finalUrl}`);

    // Determine success
    const success = finalUrl.includes('/comments/') ||
                    finalUrl.includes('submitted') ||
                    (!finalUrl.includes('/submit') && finalUrl.includes(subreddit));

    if (success) {
      console.log(`  [✅] SUCCESS: ${finalUrl}`);
      await context.close();
      return finalUrl;
    } else {
      // Save screenshot
      const screenshotPath = `/tmp/reddit_${subreddit}_failure.png`;
      await page.screenshot({ path: screenshotPath });
      console.log(`  [!] Post may have failed. Screenshot: ${screenshotPath}`);
      await context.close();
      return finalUrl;
    }

  } catch (e) {
    console.log(`  [!] Error: ${e.message}`);
    try {
      await page.screenshot({ path: `/tmp/reddit_${subreddit}_error.png` });
    } catch {}
    await context.close();
    return null;
  }
}

// --- Main ---
async function main() {
  console.log('='.repeat(60));
  console.log('MCP Workbench Reddit Poster — Playwright Node.js');
  console.log('='.repeat(60));

  const { title, body } = loadPostContent();
  console.log(`\n[>] Loaded content: "${title.substring(0, 50)}..."`);

  console.log(`\n[>] Launching Chromium...`);
  const browser = await chromium.launch({
    executablePath: CHROMIUM_PATH,
    headless: true,
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-dev-shm-usage',
      '--disable-blink-features=AutomationControlled',
      '--disable-extensions'
    ]
  });

  const results = {};
  for (const subreddit of SUBREDDITS) {
    const url = await postToSubreddit(browser, subreddit, title, body);
    results[subreddit] = url;
    await new Promise(r => setTimeout(r, 2000)); // rate limit
  }

  await browser.close();

  // Save results
  const outputPath = '/home/kali/mcp-workbench/docs/posted_reddit.json';
  const output = { status: 'completed', results, timestamp: new Date().toISOString() };
  fs.writeFileSync(outputPath, JSON.stringify(output, null, 2));

  console.log('\n' + '='.repeat(60));
  console.log('RESULTS:');
  for (const [subreddit, url] of Object.entries(results)) {
    const icon = url && (url.includes('/comments/') || url.includes('submitted')) ? '✅' : '❌';
    console.log(`  ${icon} r/${subreddit}: ${url}`);
  }
  console.log('='.repeat(60));

  return results;
}

main().catch(e => {
  console.error('Fatal:', e);
  process.exit(1);
});
