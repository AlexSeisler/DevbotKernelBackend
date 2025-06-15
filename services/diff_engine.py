import os
import requests
import base64

class DiffEngine:
    def __init__(self):
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"Bearer {os.getenv('FEDERATION_GITHUB_TOKEN')}",
            "Accept": "application/vnd.github.v3+json"
        }

    def apply_patch(self, owner, repo, branch, patches, commit_message):
        # Step 1: Get latest commit SHA & tree SHA
        ref_url = f"{self.base_url}/repos/{owner}/{repo}/git/ref/heads/{branch}"
        ref_resp = requests.get(ref_url, headers=self.headers)
        ref_resp.raise_for_status()
        latest_commit_sha = ref_resp.json()["object"]["sha"]

        commit_url = f"{self.base_url}/repos/{owner}/{repo}/git/commits/{latest_commit_sha}"
        commit_resp = requests.get(commit_url, headers=self.headers)
        commit_resp.raise_for_status()
        base_tree_sha = commit_resp.json()["tree"]["sha"]

        # Step 2: Upload new blobs for each updated file
        blobs = []
        for patch in patches:
            file_path = patch["file_path"]
            base_sha = patch["base_sha"]
            updated_content = patch["updated_content"]

            # Verify SHA state (safety guard)
            existing_file_sha = self._get_file_sha(owner, repo, branch, file_path)
            if existing_file_sha != base_sha:
                raise Exception(f"SHA mismatch on file {file_path}: expected {base_sha}, found {existing_file_sha}")

            blob_sha = self._create_blob(owner, repo, updated_content)
            blobs.append({
                "path": file_path,
                "mode": "100644",
                "type": "blob",
                "sha": blob_sha
            })

        # Step 3: Create new tree object
        tree_sha = self._create_tree(owner, repo, base_tree_sha, blobs)

        # Step 4: Create new commit object
        commit_sha = self._create_commit(owner, repo, commit_message, tree_sha, latest_commit_sha)

        # Step 5: Move branch reference to new commit
        self._move_branch(owner, repo, branch, commit_sha)

        return {"commit_sha": commit_sha}

    def _get_file_sha(self, owner, repo, branch, file_path):
        url = f"{self.base_url}/repos/{owner}/{repo}/contents/{file_path}?ref={branch}"
        resp = requests.get(url, headers=self.headers)
        resp.raise_for_status()
        return resp.json()["sha"]

    def _create_blob(self, owner, repo, content):
        url = f"{self.base_url}/repos/{owner}/{repo}/git/blobs"
        body = {
            "content": content,
            "encoding": "utf-8"
        }
        resp = requests.post(url, headers=self.headers, json=body)
        resp.raise_for_status()
        return resp.json()["sha"]

    def _create_tree(self, owner, repo, base_tree_sha, blobs):
        url = f"{self.base_url}/repos/{owner}/{repo}/git/trees"
        body = {
            "base_tree": base_tree_sha,
            "tree": blobs
        }
        resp = requests.post(url, headers=self.headers, json=body)
        resp.raise_for_status()
        return resp.json()["sha"]

    def _create_commit(self, owner, repo, message, tree_sha, parent_commit_sha):
        url = f"{self.base_url}/repos/{owner}/{repo}/git/commits"
        body = {
            "message": message,
            "tree": tree_sha,
            "parents": [parent_commit_sha]
        }
        resp = requests.post(url, headers=self.headers, json=body)
        resp.raise_for_status()
        return resp.json()["sha"]

    def _move_branch(self, owner, repo, branch, commit_sha):
        url = f"{self.base_url}/repos/{owner}/{repo}/git/refs/heads/{branch}"
        body = {"sha": commit_sha}
        resp = requests.patch(url, headers=self.headers, json=body)
        resp.raise_for_status()
