import os
import requests
from bs4 import BeautifulSoup
import subprocess
import time

# Use a very specific browser fingerprint
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Cache-Control": "max-age=0"
}

def commit_batch(count):
    print(f"--- Processed {count} files. Syncing with GitHub... ---")
    subprocess.run(["git", "config", "user.name", "GitHub Action"])
    subprocess.run(["git", "config", "user.email", "action@github.com"])
    subprocess.run(["mkdir", "-p", "downloads"])
    subprocess.run(["git", "add", "downloads/*"])
    subprocess.run("git commit -m 'Auto-upload batch' || echo 'No new files'", shell=True)
    subprocess.run(["git", "push"])

def scrape():
    if not os.path.exists('downloads'):
        os.makedirs('downloads')
    
    file_count = 0
    # Adda247 uses a specific URL structure for job posts
    base_url = "https://www.adda247.com/jobs/category/previous-year-question-paper/"

    for page in range(1, 4):  # Start with 3 pages to test
        target = f"{base_url}page/{page}/"
        print(f"--- Accessing Page {page}: {target} ---")
        
        try:
            response = requests.get(target, headers=HEADERS, timeout=20)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code != 200:
                print("Access Denied or Page Not Found. Snippet:")
                print(response.text[:500]) # See if there's a Cloudflare message
                continue

            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 1. Find all article links
            links = soup.find_all('a', href=True)
            article_links = set()
            for l in links:
                href = l['href']
                if "/jobs/" in href and not href.endswith(('.pdf', '.png', '.jpg')):
                    article_links.add(href)

            print(f"Found {len(article_links)} potential articles.")

            # 2. Enter each article to find PDFs
            for art in article_links:
                print(f"  Checking article: {art}")
                art_res = requests.get(art, headers=HEADERS, timeout=15)
                art_soup = BeautifulSoup(art_res.text, 'html.parser')
                
                for a in art_soup.find_all('a', href=True):
                    file_url = a['href']
                    if file_url.lower().endswith(('.pdf', '.docx', '.doc')):
                        fname = file_url.split('/')[-1].split('?')[0]
                        path = os.path.join('downloads', fname)
                        
                        if not os.path.exists(path):
                            print(f"    -> Downloading: {fname}")
                            f_data = requests.get(file_url, headers=HEADERS, timeout=15).content
                            with open(path, 'wb') as f:
                                f.write(f_data)
                            file_count += 1
                            
                            if file_count % 50 == 0:
                                commit_batch(file_count)
                time.sleep(2) # Prevent rate limiting

        except Exception as e:
            print(f"Error on page {page}: {e}")

    commit_batch(file_count)

if __name__ == "__main__":
    scrape()
