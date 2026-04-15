import os
import requests
from bs4 import BeautifulSoup
import subprocess
import time

BASE_URL = "https://www.adda247.com/jobs/category/previous-year-question-paper/"
EXTENSIONS = ('.pdf', '.doc', '.docx')
BATCH_SIZE = 50
# Refined headers to look like a high-end Chrome browser
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Referer": "https://www.google.com/"
}

def commit_batch(count):
    print(f"--- Reached {count} files. Committing... ---")
    subprocess.run(["git", "config", "user.name", "GitHub Action"])
    subprocess.run(["git", "config", "user.email", "action@github.com"])
    subprocess.run(["git", "add", "downloads/*"])
    subprocess.run("git commit -m 'Batch upload' || echo 'Nothing new'", shell=True)
    subprocess.run(["git", "push"])

def get_pdfs_from_page(url, current_count):
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        s = BeautifulSoup(r.text, 'html.parser')
        new_files = 0
        for a in s.find_all('a', href=True):
            link = a['href']
            if any(link.lower().endswith(ext) for ext in EXTENSIONS):
                filename = os.path.join('downloads', link.split('/')[-1].split('?')[0])
                if not os.path.exists(filename):
                    print(f"Downloading File: {link}")
                    file_data = requests.get(link, headers=HEADERS, timeout=15).content
                    with open(filename, 'wb') as f:
                        f.write(file_data)
                    new_files += 1
                    if (current_count + new_files) % BATCH_SIZE == 0:
                        commit_batch(current_count + new_files)
        return new_files
    except:
        return 0

def start_crawl():
    if not os.path.exists('downloads'): os.makedirs('downloads')
    total_count = 0
    
    for i in range(1, 6): # Scanning first 5 pages of categories
        p_url = f"{BASE_URL}page/{i}/"
        print(f"Scanning Category Page: {p_url}")
        res = requests.get(p_url, headers=HEADERS, timeout=15)
        if res.status_code != 200: break
        
        soup = BeautifulSoup(res.text, 'html.parser')
        # Find all article links on the page
        articles = [a['href'] for a in soup.find_all('a', href=True) if '/jobs/' in a['href'] and not a['href'].endswith(EXTENSIONS)]
        
        for article_url in list(set(articles)): # Use set to avoid duplicates
            print(f"  --> Entering Article: {article_url}")
            total_count += get_pdfs_from_page(article_url, total_count)
            time.sleep(1) # Small delay to avoid triggering firewall

    commit_batch(total_count)

if __name__ == "__main__":
    start_crawl()
