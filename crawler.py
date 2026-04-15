import os
import time
import random
import subprocess
from playwright.sync_api import sync_playwright
# FIX: Import the sync version of the stealth function
from playwright_stealth import stealth_sync

def commit_batch():
    print("\n--- Syncing with GitHub ---")
    subprocess.run(["git", "config", "user.name", "github-actions[bot]"])
    subprocess.run(["git", "config", "user.email", "github-actions[bot]@users.noreply.github.com"])
    subprocess.run(["git", "add", "downloads/*"], check=False)
    # The 'exit 0' ensures the action doesn't fail if there are no new files
    subprocess.run("git commit -m 'Auto-uploading new papers' || exit 0", shell=True)
    subprocess.run(["git", "push"])

def scrape():
    if not os.path.exists('downloads'):
        os.makedirs('downloads')

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Use a realistic desktop context
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080}
        )
        page = context.new_page()
        
        # FIX: Apply stealth correctly for sync_playwright
        stealth_sync(page)

        base_url = "https://www.adda247.com/jobs/category/previous-year-question-paper/"

        for pg_num in range(1, 4):
            target = f"{base_url}page/{pg_num}/"
            print(f"🔎 Visiting Page {pg_num}...")
            
            try:
                # Add a referer to look human
                page.goto(target, wait_until="domcontentloaded", timeout=60000)
                time.sleep(random.uniform(5, 10)) # Crucial for Cloudflare

                # Get article links
                articles = page.evaluate('''() => {
                    return Array.from(document.querySelectorAll('a'))
                        .map(a => a.href)
                        .filter(href => href.includes('/jobs/') && !href.includes('.pdf') && !href.includes('category'));
                }''')

                for art_url in set(articles):
                    print(f"  Checking article: {art_url}")
                    try:
                        page.goto(art_url, wait_until="domcontentloaded", timeout=30000)
                        time.sleep(2)

                        # Find PDFs
                        pdfs = page.evaluate('''() => {
                            return Array.from(document.querySelectorAll('a'))
                                .map(a => a.href)
                                .filter(href => href.toLowerCase().endsWith('.pdf'));
                        }''')

                        for pdf_url in set(pdfs):
                            fname = pdf_url.split('/')[-1].split('?')[0]
                            path = os.path.join('downloads', fname)

                            if not os.path.exists(path):
                                print(f"    📥 Downloading: {fname}")
                                # Download directly via requests using browser cookies for speed/reliability
                                cookies = {c['name']: c['value'] for c in context.cookies()}
                                headers = {"User-Agent": context.request.headers.get("user-agent", "")}
                                
                                pdf_data = context.request.get(pdf_url)
                                if pdf_data.status == 200:
                                    with open(path, 'wb') as f:
                                        f.write(pdf_data.body())
                                    time.sleep(1)
                    except Exception as e:
                        print(f"    ❌ Error in article: {e}")
                        continue

            except Exception as e:
                print(f"❌ Error on page {pg_num}: {e}")
                continue

        browser.close()
    
    commit_batch()

if __name__ == "__main__":
    scrape()
