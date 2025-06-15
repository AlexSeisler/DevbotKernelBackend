import os
import requests
from models.federation_schemas import ImportRepoRequest

class FederationService:

    def __init__(self):
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"Bearer {os.getenv('FEDERATION_GITHUB_TOKEN')}",
            "Accept": "application/vnd.github.v3+json"
        }

    def import_repo(self, payload: ImportRepoRequest):
        owner = payload.owner
        repo = payload.repo
        branch = payload.default_branch

        # STEP 1 — Validate branch and get latest SHA
        branch_url = f"{self.base_url}/repos/{owner}/{repo}/git/ref/heads/{branch}"
        branch_resp = requests.get(branch_url, headers=self.headers)
        if branch_resp.status_code != 200:
            raise Exception(f"Failed to retrieve branch reference: {branch_resp.json()}")

        branch_sha = branch_resp.json()["object"]["sha"]

        # STEP 2 — Retrieve full tree (recursive)
        tree_url = f"{self.base_url}/repos/{owner}/{repo}/git/trees/{branch_sha}?recursive=1"
        tree_resp = requests.get(tree_url, headers=self.headers)
        if tree_resp.status_code != 200:
            raise Exception(f"Failed to retrieve repo tree: {tree_resp.json()}")

        tree_data = tree_resp.json()

        files = []
        for item in tree_data.get("tree", []):
            files.append({
                "path": item.get("path"),
                "type": item.get("type"),
                "sha": item.get("sha")
            })

        # Build ingestion payload for future stages
        ingestion_payload = {
            "repo_id": f"{owner}/{repo}",
            "branch": branch,
            "root_sha": tree_data.get("sha"),
            "files": files
        }

        return ingestion_payload

    # Stubs remain in place for future stages:
    def analyze_repo(self, payload):
        return {"repo_id": payload.repo_id, "semantic_nodes": []}

    def propose_patch(self, payload):
        return {"proposal_id": "patch-001", "summary": payload.patch_summary}

    def commit_patch(self, payload):
        return {"patch_id": payload.patch_id, "commit_sha": "pending"}

    def scan_federation_graph(self):
        return {"repos_federated": [], "total_nodes": 0}
