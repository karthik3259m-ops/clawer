import os
import requests
from bs4 import BeautifulSoup
import subprocess

# Settings
BASE_URL = "https://www.adda247.com/jobs/category/previous-year-question-paper/"
EXTENSIONS = ('.pdf', '.doc', '.docx')
BATCH_SIZE = 50
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}

def commit_batch(count):
    print(f"--- Reached {count} files. Committing batch to GitHub... ---")
    subprocess.run(["git", "config", "user.name", "GitHub Action"])
    subprocess.run(["git", "config", "user.email", "action@github.com"])
    subprocess.run(["git", "add", "downloads/*"])
    # If there are no changes, git commit will fail. The '|| true' prevents the script from crashing.
    subprocess.run("git commit -m 'Uploaded batch of files' || echo 'No changes to commit'", shell=True)
    subprocess.run(["git", "push"])

def download_files():
    if not os.path.exists('downloads'):
        os.makedirs('downloads')
    
    file_count = 0
    # Scan the first 10 pages of the category
    for page_num in range(1, 11):
        page_url = f"{BASE_URL}page/{page_num}/"
        print(f"Scanning: {page_url}")
        
        try:
            res = requests.get(page_url, headers=HEADERS, timeout=15)
            if res.status_code != 200:
                print(f"Reached end or blocked at page {page_num}")
                break
                
            soup = BeautifulSoup(res.text, 'html.parser')
            links = soup.find_all('a', href=True)
            
            for a in links:
                link = a['href']
                if any(link.lower().endswith(ext) for ext in EXTENSIONS):
                    filename = os.path.join('downloads', link.split('/')[-1])
                    
                    if not os.path.exists(filename):
                        print(f"Found: {link}")
                        f_res = requests.get(link, headers=HEADERS, timeout=10)
                        with open(filename, 'wb') as f:
                            f.write(f_res.content)
                        
                        file_count += 1
                        if file_count % BATCH_SIZE == 0:
                            commit_batch(file_count)
                            
        except Exception as e:
            print(f"Error on page {page_num}: {e}")

    # Final push
    commit_batch(file_count)

if __name__ == "__main__":
    download_files()
