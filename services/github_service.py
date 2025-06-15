import os
import requests
import base64
import urllib.parse
from utils.helpers import encode_file_content
from requests.exceptions import RequestException

class GitHubService:
    def __init__(self):
        self.base_url = "https://api.github.com"
        self.owner = os.getenv("GITHUB_OWNER")
        self.repo = os.getenv("GITHUB_REPO")
        self.headers = {
            "Authorization": f"Bearer {os.getenv('GITHUB_TOKEN')}",
            "Accept": "application/vnd.github.v3+json"
        }
        self.timeout = 10  # ✅ timeout everywhere to prevent hangs

    def _request(self, method, url, **kwargs):
        """
        Unified safe request executor with audit logging and error handling
        """
        try:
            response = requests.request(method, url, headers=self.headers, timeout=self.timeout, **kwargs)
            response.raise_for_status()
            return response.json()
        except RequestException as e:
            print(f"[GITHUB API ERROR] {method} {url} failed: {str(e)}")
            raise e

    # ✅ Hardened Repo Tree Retrieval
    def get_repo_tree(self, branch, recursive):
        url = f"{self.base_url}/repos/{self.owner}/{self.repo}/git/trees/{branch}?recursive={1 if recursive else 0}"
        return self._request("GET", url)

    # ✅ Hardened File Retrieval
    def get_file(self, file_path, branch):
        encoded_path = urllib.parse.quote(file_path, safe="")
        url = f"{self.base_url}/repos/{self.owner}/{self.repo}/contents/{encoded_path}?ref={branch}"
        return self._request("GET", url)

    # ✅ Hardened File History Retrieval
    def get_file_history(self, file_path, branch):
        url = f"{self.base_url}/repos/{self.owner}/{self.repo}/commits?path={file_path}&sha={branch}"
        return self._request("GET", url)

    # ✅ Hardened Branch SHA Retrieval
    def get_branch_sha(self, branch):
        url = f"{self.base_url}/repos/{self.owner}/{self.repo}/git/refs/heads/{branch}"
        return self._request("GET", url)

    # ✅ Hardened Branch Creation
    def create_branch(self, new_branch, base_branch):
        sha_url = f"{self.base_url}/repos/{self.owner}/{self.repo}/git/refs/heads/{base_branch}"
        base_sha = self._request("GET", sha_url)['object']['sha']

        url = f"{self.base_url}/repos/{self.owner}/{self.repo}/git/refs"
        payload = {"ref": f"refs/heads/{new_branch}", "sha": base_sha}
        return self._request("POST", url, json=payload)

    # ✅ Hardened Single File Commit
    def commit_patch(self, payload):
        encoded_path = urllib.parse.quote(payload.file_path, safe="")
        url = f"{self.base_url}/repos/{self.owner}/{self.repo}/contents/{encoded_path}"
        content_encoded = encode_file_content(payload.updated_content)
        body = {
            "message": payload.commit_message,
            "content": content_encoded,
            "branch": payload.branch
        }
        return self._request("PUT", url, json=body)

    # ✅ Hardened Multi-file Commit (Federation ready)
    def multi_file_commit(self, message, files, branch="main"):
        # Get latest SHA
        ref_url = f"{self.base_url}/repos/{self.owner}/{self.repo}/git/refs/heads/{branch}"
        latest_commit_sha = self._request("GET", ref_url)["object"]["sha"]

        commit_url = f"{self.base_url}/repos/{self.owner}/{self.repo}/git/commits/{latest_commit_sha}"
        base_tree_sha = self._request("GET", commit_url)["tree"]["sha"]

        # Create blobs
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

        # Create new tree
        tree_url = f"{self.base_url}/repos/{self.owner}/{self.repo}/git/trees"
        tree_resp = self._request("POST", tree_url, json={
            "base_tree": base_tree_sha,
            "tree": blobs
        })
        new_tree_sha = tree_resp["sha"]

        # Create new commit
        commit_create_url = f"{self.base_url}/repos/{self.owner}/{self.repo}/git/commits"
        commit_create_resp = self._request("POST", commit_create_url, json={
            "message": message,
            "tree": new_tree_sha,
            "parents": [latest_commit_sha]
        })
        new_commit_sha = commit_create_resp["sha"]

        # Update branch
        update_ref_url = f"{self.base_url}/repos/{self.owner}/{self.repo}/git/refs/heads/{branch}"
        self._request("PATCH", update_ref_url, json={"sha": new_commit_sha})

        return {"status": "committed", "commit_sha": new_commit_sha}

    # ✅ Hardened File Deletion
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

    # ✅ Hardened Pull Request Creation
    def create_pull_request(self, source_branch, target_branch, title, body):
        url = f"{self.base_url}/repos/{self.owner}/{self.repo}/pulls"
        payload = {
            "title": title,
            "body": body,
            "head": source_branch,
            "base": target_branch
        }
        return self._request("POST", url, json=payload)
