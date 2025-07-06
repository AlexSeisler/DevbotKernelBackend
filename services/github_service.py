# FULLY PATCHED GitHubService - No self.owner/repo usage

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
        self.tokens = []

        primary = os.getenv("FEDERATION_GITHUB_TOKEN")
        if primary:
            self.tokens = [primary.strip()]
        else:
            multi = os.getenv("FEDERATION_GITHUB_TOKENS", "")
            self.tokens = [t.strip() for t in multi.split(",") if t.strip()]

        if not self.tokens:
            raise ValueError("No valid GitHub token found in environment.")

        self.current_token_index = 0
        self.token = self.tokens[0]
        self.timeout = 10
        self.headers = self._build_headers(self.token)

    def _build_headers(self, token):
        return {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }

    def _rotate_token(self):
        if len(self.tokens) > 1:
            self.current_token_index = (self.current_token_index + 1) % len(self.tokens)
            self.token = self.tokens[self.current_token_index]
            self.headers = self._build_headers(self.token)
            print(f"[GITHUB] Token rotated to index {self.current_token_index}")

    def _request(self, method, url, **kwargs):
        try:
            response = requests.request(method, url, headers=self.headers, timeout=self.timeout, **kwargs)
            response.raise_for_status()
            return response.json()
        except RequestException as e:
            if hasattr(e.response, 'status_code') and e.response.status_code == 403:
                if "rate limit" in str(e).lower():
                    print(f"[GITHUB RATE LIMIT] rotating token...")
                    self._rotate_token()
                    return self._request(method, url, **kwargs)
            print(f"[GITHUB API ERROR] {method} {url} failed: {str(e)}")
            raise

    # Replace or extend this method inside GitHubService:

    def get_repo_tree(self, owner, repo, branch, recursive, limit=None, offset=None, path_prefix=None):
        url = f"{self.base_url}/repos/{owner}/{repo}/git/trees/{branch}?recursive={1 if recursive else 0}"
        tree_data = self._request("GET", url)["tree"]

        if path_prefix:
            tree_data = [item for item in tree_data if item["path"].startswith(path_prefix)]
        if offset is not None and limit is not None:
            tree_data = tree_data[offset:offset+limit]

        return tree_data


    # Replace or extend this method inside GitHubService:

    def get_file(self, owner, repo, file_path, branch, fallback=True, include_meta=False):
        encoded_path = urllib.parse.quote(file_path, safe="")
        url = f"{self.base_url}/repos/{owner}/{repo}/contents/{encoded_path}?ref={branch}"

        try:
            file_data = self._request("GET", url)
            size = file_data.get("size", 0)
            if size > 1000000:  # ~1MB size limit
                print(f"[get_file] ⚠️ File too large ({size} bytes), falling back to blob API")
                content = self.get_large_file_blob(owner, repo, file_path, branch)
                return {
                    "content": content,
                    "sha": file_data.get("sha"),  # From /contents metadata
                    "size": size,
                    "encoding": "utf-8"
                }
        except RequestException as e:
            if fallback and "404" in str(e):
                print(f"⚠️ File {file_path} not found on branch {branch}, retrying on 'main'")
                fallback_url = f"{self.base_url}/repos/{owner}/{repo}/contents/{encoded_path}?ref=main"
                file_data = self._request("GET", fallback_url)
            else:
                raise

        if include_meta:
            return {
                "content": base64.b64decode(file_data["content"]).decode("utf-8"),
                "sha": file_data.get("sha"),
                "size": file_data.get("size"),
                "encoding": file_data.get("encoding", "utf-8")
            }

        return file_data


    def get_large_file_blob(self, owner, repo, file_path, branch):
        print(f"[blob] 🔍 Fetching tree for branch: {branch}")
        tree_url = f"{self.base_url}/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
        tree_data = self._request("GET", tree_url)

        blob_entry = next((item for item in tree_data["tree"] if item["path"] == file_path), None)
        if not blob_entry:
            raise ValueError(f"[blob] ❌ File {file_path} not found in branch tree")

        print(f"[blob] 📦 Blob SHA: {blob_entry['sha']}")
        blob_url = f"{self.base_url}/repos/{owner}/{repo}/git/blobs/{blob_entry['sha']}"
        blob_data = self._request("GET", blob_url)

        if blob_data.get("encoding") != "base64":
            raise ValueError(f"[blob] ❌ Unexpected encoding: {blob_data.get('encoding')}")

        decoded = base64.b64decode(blob_data["content"]).decode("utf-8")
        return decoded

    def get_file_history(self, owner, repo, file_path, branch):
        url = f"{self.base_url}/repos/{owner}/{repo}/commits?path={file_path}&sha={branch}"
        return self._request("GET", url)

    def get_branch_sha(self, owner, repo, branch):
        print(f"[DEBUG] get_branch_sha called with: {owner}, {repo}, {branch}")
        url = f"{self.base_url}/repos/{owner}/{repo}/git/refs/heads/{branch}"
        return self._request("GET", url)

    def create_branch(self, owner, repo, new_branch: str, base_branch: str):
        try:
            sha_url = f"{self.base_url}/repos/{owner}/{repo}/git/refs/heads/{base_branch}"
            response = requests.get(sha_url, headers=self.headers)
            response.raise_for_status()
            base_sha = response.json()["object"]["sha"]

            url = f"{self.base_url}/repos/{owner}/{repo}/git/refs"
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
    
    def delete_file(self, owner, repo, file_path, message, sha, branch="main"):
        encoded_path = urllib.parse.quote(file_path, safe="")
        url = f"{self.base_url}/repos/{owner}/{repo}/contents/{encoded_path}"

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

    def get_latest_file_sha(self, owner, repo, file_path: str, branch: str = "main") -> str:
        print(f"[DEBUG] get_latest_file_sha for: {file_path}, branch={branch}")

        encoded_path = urllib.parse.quote(file_path, safe="")
        url = f"{self.base_url}/repos/{owner}/{repo}/contents/{encoded_path}?ref={branch}"
        r = requests.get(url, headers=self.headers)
        if r.status_code == 200:
            return r.json()["sha"]
        raise Exception(f"Failed to fetch latest SHA: {r.status_code} {r.text}")

    def get_repo_id(self, owner: str, repo: str) -> int:
        url = f"{self.base_url}/repos/{owner}/{repo}"
        response = requests.get(url, headers=self.headers)
        print(f"[DEBUG] Calling GitHub repo: https://api.github.com/repos/{owner}/{repo}")
        print(f"[DEBUG] Headers: {self.headers}")

        if response.status_code != 200:
            raise Exception(f"Failed to fetch repo ID: {response.status_code} {response.text}")
        
        repo_data = response.json()
        if "id" not in repo_data:
            raise Exception(f"GitHub response missing 'id': {repo_data}")
        
        return repo_data["id"]

