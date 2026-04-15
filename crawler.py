import os
import requests
from bs4 import BeautifulSoup
import subprocess
import time

# Very specific browser fingerprint to bypass basic bot filters
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Referer": "https://www.google.com/",
}

def commit_batch(count):
    """
    Commands to sync with GitHub. 
    Note: In Actions, the environment variables handle the token.
    """
    print(f"\n--- Batch Sync: {count} files found. ---")
    # These configs are needed for the runner to 'act' as a user
    subprocess.run(["git", "config", "user.name", "github-actions[bot]"])
    subprocess.run(["git", "config", "user.email", "github-actions[bot]@users.noreply.github.com"])
    
    # Add files inside the downloads folder
    subprocess.run(["git", "add", "downloads/*"], check=False)
    
    # Commit and push
    result = subprocess.run("git commit -m 'Auto-upload batch: " + str(count) + " files'", shell=True, capture_output=True)
    if b"nothing to commit" not in result.stdout:
        subprocess.run(["git", "push"])
        print("🚀 Pushed to GitHub.")
    else:
        print("Ø No new files to commit.")

def scrape():
    if not os.path.exists('downloads'):
        os.makedirs('downloads')
    
    file_count = 0
    base_url = "https://www.adda247.com/jobs/category/previous-year-question-paper/"

    # Scanning first 5 pages of the archive
    for page in range(1, 6):  
        target = f"{base_url}page/{page}/"
        print(f"\n🔎 Scanning Archive Page {page}...")
        
        try:
            response = requests.get(target, headers=HEADERS, timeout=20)
            if response.status_code != 200:
                print(f"⚠️ Access Denied (Status {response.status_code})")
                continue

            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find article links
            article_links = set()
            for l in soup.find_all('a', href=True):
                href = l['href']
                # Filter for job posts only
                if "/jobs/" in href and not href.endswith(('.pdf', '.png', '.jpg', '.zip')):
                    article_links.add(href)

            print(f"📄 Found {len(article_links)} articles. Checking for PDFs...")

            for art in article_links:
                try:
                    art_res = requests.get(art, headers=HEADERS, timeout=15)
                    art_soup = BeautifulSoup(art_res.text, 'html.parser')
                    
                    for a in art_soup.find_all('a', href=True):
                        file_url = a['href']
                        if file_url.lower().endswith(('.pdf', '.docx', '.doc')):
                            # Clean filename
                            fname = file_url.split('/')[-1].split('?')[0]
                            path = os.path.join('downloads', fname)
                            
                            if not os.path.exists(path):
                                print(f"  📥 Downloading: {fname}")
                                try:
                                    f_data = requests.get(file_url, headers=HEADERS, timeout=20).content
                                    with open(path, 'wb') as f:
                                        f.write(f_data)
                                    file_count += 1
                                    
                                    # Push to GitHub every 10 files to avoid timeout/large commits
                                    if file_count % 10 == 0:
                                        commit_batch(file_count)
                                except Exception as download_err:
                                    print(f"  ❌ Failed to download {fname}: {download_err}")
                except Exception as art_err:
                    print(f"  ❌ Failed to read article {art}: {art_err}")
                
                time.sleep(1) # Human-like delay

        except Exception as e:
            print(f"❌ Error on page {page}: {e}")

    # Final sync for any remaining files
    if file_count > 0:
        commit_batch(file_count)
    else:
        print("\n✅ All caught up. No new files found.")

if __name__ == "__main__":
    scrape()
