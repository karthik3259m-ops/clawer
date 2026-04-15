import os
import time
import random
import subprocess
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth

def commit_batch():
    print("\n--- Syncing with GitHub ---")
    subprocess.run(["git", "config", "user.name", "github-actions[bot]"])
    subprocess.run(["git", "config", "user.email", "github-actions[bot]@users.noreply.github.com"])
    subprocess.run(["git", "add", "downloads/*"], check=False)
    subprocess.run("git commit -m 'Auto-uploading new papers' || exit 0", shell=True)
    subprocess.run(["git", "push"])

def scrape():
    if not os.path.exists('downloads'):
        os.makedirs('downloads')

    with sync_playwright() as p:
        # Launching Chromium with specific flags to look less like a bot
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080}
        )
        page = context.new_page()
        
        # Apply Stealth
        stealth(page)

        base_url = "https://www.adda247.com/jobs/category/previous-year-question-paper/"

        for pg_num in range(1, 4):
            target = f"{base_url}page/{pg_num}/"
            print(f"🔎 Visiting Page {pg_num}...")
            
            try:
                page.goto(target, wait_until="networkidle", timeout=60000)
                # Wait a bit for Cloudflare to 'blink' and let us in
                time.sleep(random.uniform(5, 8))

                # Extract article links using browser logic
                articles = page.evaluate('''() => {
                    return Array.from(document.querySelectorAll('a'))
                        .map(a => a.href)
                        .filter(href => href.includes('/jobs/') && !href.includes('.pdf'));
                }''')

                for art_url in set(articles):
                    print(f"  Checking: {art_url}")
                    page.goto(art_url, wait_until="domcontentloaded")
                    time.sleep(2)

                    # Find PDF links inside the article
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
                            # Download via the browser to keep the session alive
                            response = page.goto(pdf_url)
                            if response.status == 200:
                                with open(path, 'wb') as f:
                                    f.write(response.body())
                            page.go_back()
                            time.sleep(1)

            except Exception as e:
                print(f"❌ Error on page {pg_num}: {e}")
                continue

        browser.close()
    
    commit_batch()

if __name__ == "__main__":
    scrape()
