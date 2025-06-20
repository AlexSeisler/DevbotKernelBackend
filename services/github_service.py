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
        self.owner = os.getenv("GITHUB_OWNER")       # ✅ REQUIRED
        self.repo = os.getenv("GITHUB_REPO")         # ✅ REQUIRED
        self.timeout = 10
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }

    def _request(self, method, url, **kwargs):
        try:
            response = requests.request(method, url, headers=self.headers, timeout=self.timeout, **kwargs)
            response.raise_for_status()
            return response.json()
        except RequestException as e:
            print(f"[GITHUB API ERROR] {method} {url} failed: {str(e)}")
            raise

    def get_repo_tree(self, branch, recursive):
        url = f"{self.base_url}/repos/{self.owner}/{self.repo}/git/trees/{branch}?recursive={1 if recursive else 0}"
        return self._request("GET", url)

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

    def get_file_history(self, file_path, branch):
        url = f"{self.base_url}/repos/{self.owner}/{self.repo}/commits?path={file_path}&sha={branch}"
        return self._request("GET", url)

    def get_branch_sha(self, branch):
        url = f"{self.base_url}/repos/{self.owner}/{self.repo}/git/refs/heads/{branch}"
        return self._request("GET", url)

    def create_branch(self, new_branch: str, base_branch: str):
        try:
            sha_url = f"{self.base_url}/repos/{self.owner}/{self.repo}/git/refs/heads/{base_branch}"
            response = requests.get(sha_url, headers=self.headers)
            response.raise_for_status()
            base_sha = response.json()["object"]["sha"]

            url = f"{self.base_url}/repos/{self.owner}/{self.repo}/git/refs"
            payload = {
                "ref": f"refs/heads/{new_branch}",
                "sha": base_sha
            }
            post_response = requests.post(url, headers=self.headers, json=payload)
            post_response.raise_for_status()

            return post_response.json()

        except RequestException as e:
            print(f"[❌] create_branch failed: {str(e)}")
            raise

    def commit_patch(self, payload):
        encoded_path = urllib.parse.quote(payload.file_path, safe="")
        owner, repo = payload.repo_id.split("/")

        if not payload.base_sha or payload.base_sha == "latest":
            payload.base_sha = self.get_latest_file_sha(payload.file_path, payload.branch)

        url = f"{self.base_url}/repos/{owner}/{repo}/contents/{encoded_path}"
        content_encoded = encode_file_content(payload.updated_content)

        body = {
            "message": payload.commit_message,
            "content": content_encoded,
            "branch": payload.branch,
            "sha": payload.base_sha
        }

        r = requests.put(url, headers=self.headers, json=body)

        if r.status_code not in [200, 201]:
            raise Exception(f"Commit failed: {r.status_code} {r.text}")

        return r.json()

    def multi_file_commit(self, message, files, branch="main"):
        ref_url = f"{self.base_url}/repos/{self.owner}/{self.repo}/git/refs/heads/{branch}"
        latest_commit_sha = self._request("GET", ref_url)["object"]["sha"]

        commit_url = f"{self.base_url}/repos/{self.owner}/{self.repo}/git/commits/{latest_commit_sha}"
        base_tree_sha = self._request("GET", commit_url)["tree"]["sha"]

        blobs = []
        for file in files:
            blob_url = f"{self.base_url}/repos/{self.owner}/{self.repo}/git/blobs"
            blob_resp = self._request("POST", blob_url, json={
                "content": file["content"],
                "encoding": "utf-8"
            })
            blobs.append({
                "path": file["path"],
                "mode": "100644",
                "type": "blob",
                "sha": blob_resp["sha"]
            })

        tree_url = f"{self.base_url}/repos/{self.owner}/{self.repo}/git/trees"
        tree_resp = self._request("POST", tree_url, json={
            "base_tree": base_tree_sha,
            "tree": blobs
        })
        new_tree_sha = tree_resp["sha"]

        commit_create_url = f"{self.base_url}/repos/{self.owner}/{self.repo}/git/commits"
        commit_create_resp = self._request("POST", commit_create_url, json={
            "message": message,
            "tree": new_tree_sha,
            "parents": [latest_commit_sha]
        })
        new_commit_sha = commit_create_resp["sha"]

        update_ref_url = f"{self.base_url}/repos/{self.owner}/{self.repo}/git/refs/heads/{branch}"
        self._request("PATCH", update_ref_url, json={"sha": new_commit_sha})

        return {"status": "committed", "commit_sha": new_commit_sha}

    def delete_file(self, file_path, message, sha, branch="main"):
        encoded_path = urllib.parse.quote(file_path, safe="")
        url = f"{self.base_url}/repos/{self.owner}/{self.repo}/contents/{encoded_path}"

        body = {
            "message": message,
            "sha": sha,
            "branch": branch
        }

        self._request("DELETE", url, json=body)
        return {"status": "deleted"}

    def create_pull_request(self, owner, repo, source_branch, target_branch, title, body):
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls"
        payload = {
            "title": title,
            "body": body,
            "head": source_branch,
            "base": target_branch
        }

        print(f"[PR DEBUG] POST to: {url}")
        print(f"[PR PAYLOAD] {payload}")

        return self._request("POST", url, json=payload)

    def get_latest_file_sha(self, file_path: str, branch: str = "main") -> str:
        encoded_path = urllib.parse.quote(file_path, safe="")
        url = f"{self.base_url}/repos/{self.owner}/{self.repo}/contents/{encoded_path}?ref={branch}"
        r = requests.get(url, headers=self.headers)
        if r.status_code == 200:
            return r.json()["sha"]
        raise Exception(f"Failed to fetch latest SHA: {r.status_code} {r.text}")
