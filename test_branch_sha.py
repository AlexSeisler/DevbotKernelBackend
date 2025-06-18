import os
from dotenv import load_dotenv
import requests

load_dotenv()

GITHUB_TOKEN = os.getenv("FEDERATION_GITHUB_TOKEN")
OWNER = os.getenv("GITHUB_OWNER")
REPO = os.getenv("GITHUB_REPO")
BRANCH = "main"

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

url = f"https://api.github.com/repos/{OWNER}/{REPO}/git/refs/heads/{BRANCH}"

print(f"[TEST] Requesting SHA from: {url}")
response = requests.get(url, headers=HEADERS)

if response.status_code != 200:
    print(f"[ERROR] Status Code: {response.status_code}")
    print(f"[RESPONSE] {response.text}")
    exit()

data = response.json()
sha = data.get("object", {}).get("sha")
print(f"[✅] Base SHA for branch '{BRANCH}': {sha}")
