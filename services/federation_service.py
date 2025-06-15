import os
import requests
from models.federation_schemas import ImportRepoRequest, AnalyzeRepoRequest
from services.semantic_parser import SemanticParser

class FederationService:

    def __init__(self):
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"Bearer {os.getenv('FEDERATION_GITHUB_TOKEN')}",
            "Accept": "application/vnd.github.v3+json"
        }
        self.semantic_parser = SemanticParser()

    def import_repo(self, payload: ImportRepoRequest):
        owner = payload.owner
        repo = payload.repo
        branch = payload.default_branch

        branch_url = f"{self.base_url}/repos/{owner}/{repo}/git/ref/heads/{branch}"
        branch_resp = requests.get(branch_url, headers=self.headers)
        if branch_resp.status_code != 200:
            raise Exception(f"Failed to retrieve branch reference: {branch_resp.json()}")

        branch_sha = branch_resp.json()["object"]["sha"]

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

        ingestion_payload = {
            "repo_id": f"{owner}/{repo}",
            "branch": branch,
            "root_sha": tree_data.get("sha"),
            "files": files
        }

        return ingestion_payload

    def analyze_repo(self, payload: AnalyzeRepoRequest):
        owner, repo = payload.repo_id.split("/")

        # Get file list from prior ingestion call
        branch = "main"  # (assuming default for now, future: dynamic state)
        tree_url = f"{self.base_url}/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
        tree_resp = requests.get(tree_url, headers=self.headers)
        tree_resp.raise_for_status()
        tree_data = tree_resp.json()

        semantic_results = []
        for item in tree_data.get("tree", []):
            if item.get("type") == "blob" and item.get("path").endswith(".py"):
                file_path = item.get("path")

                # Fetch file content
                file_url = f"{self.base_url}/repos/{owner}/{repo}/contents/{file_path}?ref={branch}"
                file_resp = requests.get(file_url, headers=self.headers)
                file_resp.raise_for_status()

                file_data = file_resp.json()
                file_content = self._decode_github_content(file_data.get("content"))

                file_nodes = self.semantic_parser.parse_python_file(file_content)
                for node in file_nodes:
                    node["file_path"] = file_path
                    semantic_results.append(node)

        return {"repo_id": payload.repo_id, "semantic_nodes": semantic_results}

    def _decode_github_content(self, encoded_content):
        import base64
        decoded_bytes = base64.b64decode(encoded_content)
        return decoded_bytes.decode("utf-8")

    # The other federation functions remain as previous stage
    def propose_patch(self, payload):
        return {"proposal_id": "patch-001", "summary": payload.patch_summary}

    def commit_patch(self, payload):
        return {"patch_id": payload.patch_id, "commit_sha": "pending"}

    def scan_federation_graph(self):
        return {"repos_federated": [], "total_nodes": 0}
