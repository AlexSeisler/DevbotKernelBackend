import os
import requests

class ModuleExtractor:
    def __init__(self):
        self.github_token = os.getenv("FEDERATION_GITHUB_TOKEN")
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"Bearer {self.github_token}",
            "Accept": "application/vnd.github.v3+json"
        }

    def fetch_file_content(self, owner, repo, file_path, branch):
        url = f"{self.base_url}/repos/{owner}/{repo}/contents/{file_path}?ref={branch}"
        resp = requests.get(url, headers=self.headers)
        resp.raise_for_status()
        content = resp.json()["content"]
        sha = resp.json()["sha"]
        return (file_path, sha, content)
