import os, requests, base64
from fastapi import HTTPException
from models.federation_schemas import ImportRepoRequest, AnalyzeRepoRequest
from services.semantic_parser import SemanticParser
from services.db.repo_manager import RepoManager
from services.db.federation_graph_manager import FederationGraphManager
from services.db.semantic_manager import SemanticManager
from settings import Database
from services.github_service import GitHubService
from models.federation_schemas import CommitPatchObject
from services.db.proposal_manager import ProposalManager
from models.federation_schemas import CommitPatchRequest
import uuid

class FederationService:
    def __init__(self):
        self.base_url = "https://api.github.com"
        self.github_token = os.getenv("FEDERATION_GITHUB_TOKEN")
        self.headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        self.db = Database()
        self.repo_manager = RepoManager()
        self.graph_manager = FederationGraphManager()
        self.semantic_parser = SemanticParser()
        self.semantic_manager = SemanticManager()
        self.github = GitHubService()
        self.proposal_manager = ProposalManager()

    def analyze_repo(self, payload: AnalyzeRepoRequest):
        repo_pk = payload.repo_id
        logical_repo_id = self.repo_manager.resolve_repo_id_by_pk(repo_pk)
        owner, repo = logical_repo_id.split("/")
        semantic_results = []

        branch_sha = self.github.get_branch_sha("main")["object"]["sha"]
        repo_tree_data = self.github.get_repo_tree(branch_sha, recursive=True)
        repo_tree = repo_tree_data["tree"]

        for file in repo_tree:
            file_path = file.get("path", "")
            if not file_path.endswith(".py"):
                continue

            try:
                raw_file = self.github.get_file(file_path, "main", fallback=True)
                file_content = base64.b64decode(raw_file["content"]).decode()
            except Exception as e:
                print(f"⚠️ Skipped file {file_path} due to fetch error: {e}")
                continue

            nodes = self.semantic_parser.parse_python_file(file_content)
            for node in nodes:
                node["file_path"] = file_path
                self.semantic_manager.save_semantic_node(repo_pk, node)
                semantic_results.append(node)

        return {"repo_id": repo_pk, "semantic_nodes": semantic_results}