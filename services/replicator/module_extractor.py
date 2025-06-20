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
        self._cache = {}

    def fetch_file_content(self, owner, repo, file_path, branch):
        key = (file_path, branch)
        if key in self._cache:
            return self._cache[key]

        url = f"{self.base_url}/repos/{owner}/{repo}/contents/{file_path}?ref={branch}"
        resp = requests.get(url, headers=self.headers)
        resp.raise_for_status()
        content = resp.json()["content"]
        sha = resp.json()["sha"]
        self._cache[key] = (file_path, sha, content)
        return self._cache[key]