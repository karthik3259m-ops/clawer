import os
import requests
from bs4 import BeautifulSoup
import subprocess

# Settings
BASE_URL = "https://www.adda247.com/jobs/category/previous-year-question-paper/"
EXTENSIONS = ('.pdf', '.doc', '.docx')
BATCH_SIZE = 50
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

def commit_batch(count):
    print(f"--- Reached {count} files. Committing batch to GitHub... ---")
    subprocess.run(["git", "config", "user.name", "GitHub Action"])
    subprocess.run(["git", "config", "user.email", "action@github.com"])
    subprocess.run(["git", "add", "downloads/*"])
    subprocess.run(["git", "commit", "-m", f"Uploaded batch of {count} files"])
    subprocess.run(["git", "push"])

def download_files():
    if not os.path.exists('downloads'):
        os.makedirs('downloads')
    
    found_files = []
    current_page = BASE_URL
    file_count = 0

    while current_page:
        print(f"Scanning page: {current_page}")
        res = requests.get(current_page, headers=HEADERS)
        soup = BeautifulSoup(res.text, 'html.parser')

        # Find all resource links on the current page
        for a in soup.find_all('a', href=True):
            link = a['href']
            if link.lower().endswith(EXTENSIONS) and link not in found_files:
                try:
                    filename = os.path.join('downloads', link.split('/')[-1])
                    print(f"Downloading: {link}")
                    file_data = requests.get(link, headers=HEADERS).content
                    with open(filename, 'wb') as f:
                        f.write(file_data)
                    
                    found_files.append(link)
                    file_count += 1

                    # Batch Check
                    if file_count % BATCH_SIZE == 0:
                        commit_batch(file_count)
                except Exception as e:
                    print(f"Error downloading {link}: {e}")

        # Find "Next" page link
        next_page = soup.find('a', class_='next') # Adjust class name if Adda247 changes it
        current_page = next_page['href'] if next_page else None

    # Final commit for remaining files
    if file_count % BATCH_SIZE != 0:
        commit_batch(file_count)

if __name__ == "__main__":
    download_files()
