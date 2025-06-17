import os, requests, base64
from fastapi import HTTPException
from models.federation_schemas import ImportRepoRequest, AnalyzeRepoRequest
from services.semantic_parser import SemanticParser
from services.diff_engine import DiffEngine
from services.proposal_queue import ProposalQueueManager
from services.db.federation_graph_manager import FederationGraphManager
from services.db.repo_manager import RepoManager
from services.db.semantic_manager import SemanticManager
from settings import Database

class FederationService:

    def __init__(self):
        self.base_url = "https://api.github.com"
        self.github_token = os.getenv("FEDERATION_GITHUB_TOKEN", os.getenv("GITHUB_TOKEN")).strip()

        self.headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        if not self.github_token:
            raise ValueError("GitHub OAuth token not found.")

        self.db = Database().get_connection()
        self.repo_manager = RepoManager()
        self.graph_manager = FederationGraphManager()
        self.semantic_manager = SemanticManager()
        self.semantic_parser = SemanticParser()
        self.diff_engine = DiffEngine()
        self.proposal_queue = ProposalQueueManager()

    def import_repo(self, payload: ImportRepoRequest):
        owner, repo, branch = payload.owner, payload.repo, payload.default_branch
        logical_repo_id = f"{owner}/{repo}"

        branch_resp = requests.get(f"{self.base_url}/repos/{owner}/{repo}/git/ref/heads/{branch}", headers=self.headers)
        if branch_resp.status_code != 200:
            raise Exception(f"Branch reference failed: {branch_resp.json()}")

        branch_sha = branch_resp.json()["object"]["sha"]

        tree_resp = requests.get(f"{self.base_url}/repos/{owner}/{repo}/git/trees/{branch_sha}?recursive=1", headers=self.headers)
        if tree_resp.status_code != 200:
            raise Exception(f"Tree retrieval failed: {tree_resp.json()}")

        files = [
            {"path": item["path"], "type": item["type"], "sha": item["sha"]}
            for item in tree_resp.json()["tree"]
        ]

        try:
            with self.db:
                with self.db.cursor() as cur:
                    repo_pk_id = self.repo_manager.save_repo_tx(cur, logical_repo_id, branch, branch_sha)
                    for file in files:
                        self.graph_manager.insert_graph_link_tx(
                            cur, logical_repo_id, file['path'], file['type'],
                            file['path'].split("/")[-1], None, 1, "Ingested file"
                        )
            return {"status": "success", "repo_id": repo_pk_id, "files_ingested": len(files)}
        except Exception as e:
            raise Exception(f"Ingestion failed: {str(e)}")

    def analyze_repo(self, payload: AnalyzeRepoRequest):
        repo_id = payload.repo_id
        logical_repo_id = self.repo_manager.resolve_repo_id_by_pk(repo_id)
        if not logical_repo_id:
            raise HTTPException(status_code=404, detail="Repo not found")

        graph_files = self.graph_manager.query_graph(logical_repo_id)
        owner, repo = logical_repo_id.split("/")
        branch = "main"

        semantic_results = []
        for file_entry in graph_files:
            file_path = file_entry["file_path"]
            if not file_path.endswith(".py"):
                continue

            file_resp = requests.get(f"{self.base_url}/repos/{owner}/{repo}/contents/{file_path}?ref={branch}", headers=self.headers)
            file_resp.raise_for_status()
            file_data = file_resp.json()

            file_content = self._decode_github_content(file_data["content"])
            file_nodes = self.semantic_parser.parse_python_file(file_content)

            for node in file_nodes:
                node["file_path"] = file_path
                self.semantic_manager.save_semantic_node(repo_id, node)
                semantic_results.append(node)

        return {"repo_id": repo_id, "semantic_nodes": semantic_results}

    def _decode_github_content(self, encoded_content):
        return base64.b64decode(encoded_content).decode("utf-8")
