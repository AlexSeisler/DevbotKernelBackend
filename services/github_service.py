import os
import requests
import base64
import urllib.parse
from utils.helpers import encode_file_content
from requests.exceptions import RequestException
from dotenv import load_dotenv

load_dotenv()

class GitHubService:
    def __init__(self):
        self.base_url = "https://api.github.com"
        self.token = os.getenv("FEDERATION_GITHUB_TOKEN")
        self.owner = os.getenv("GITHUB_OWNER")  # ✅ REQUIRED
        self.repo = os.getenv("GITHUB_REPO")    # ✅ REQUIRED
        self.timeout = 10
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }

    def _request(self, method, url, **kwargs):
        """
        Unified safe request executor with audit logging and error handling
        """
        try:
            response = requests.request(method, url, headers=self.headers, timeout=self.timeout, **kwargs)
            response.raise_for_status()
            return response.json()
        except RequestException as e:
            print(f"[GITHUB API ERROR] {method} {url} failed: {str(e)}")  # Retain minimal trace for error triage
            raise

    # 🔐 Hardened File Retrieval with optional fallback
    def get_file(self, file_path, branch, fallback=True):
        encoded_path = urllib.parse.quote(file_path, safe="")
        url = f"{self.base_url}/repos/{self.owner}/{self.repo}/contents/{encoded_path}?ref={branch}"
        try:
            return self._request("GET", url)
        except RequestException as e:
            if fallback and "404" in str(e):
                print(f"⚠️ File {file_path} not found on branch {branch}, retrying on 'main'")
                fallback_url = f"{self.base_url}/repos/{self.owner}/{self.repo}/contents/{encoded_path}?ref=main"
                return self._request("GET", fallback_url)
            raise