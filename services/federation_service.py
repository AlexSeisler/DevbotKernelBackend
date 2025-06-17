import os, requests, base64
from fastapi import HTTPException
from models.federation_schemas import ImportRepoRequest, AnalyzeRepoRequest
from services.semantic_parser import SemanticParser
from services.db.repo_manager import RepoManager
from services.db.federation_graph_manager import FederationGraphManager
from services.db.semantic_manager import SemanticManager
from settings import Database

class FederationService:
    def __init__(self):
        self.base_url = "https://api.github.com"
        self.github_token = os.getenv("FEDERATION_GITHUB_TOKEN").strip()
        self.headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        self.db = Database().get_connection()
        self.repo_manager = RepoManager()
        self.graph_manager = FederationGraphManager()
        self.semantic_parser = SemanticParser()
        self.semantic_manager = SemanticManager()

    def import_repo(self, payload: ImportRepoRequest):
        owner, repo, branch = payload.owner, payload.repo, payload.default_branch
        logical_repo_id = f"{owner}/{repo}"

        branch_sha = self._get_branch_sha(owner, repo, branch)
        tree_data = self._get_repo_tree(owner, repo, branch_sha)

        files = [{"path": i["path"], "type": i["type"], "sha": i["sha"]} for i in tree_data.get("tree", [])]

        with self.db:
            with self.db.cursor() as cur:
                pk_id = self.repo_manager.save_repo_tx(cur, logical_repo_id, branch, tree_data["sha"])
                for file in files:
                    self.graph_manager.insert_graph_link_tx(cur, logical_repo_id, file['path'], file['type'], file['path'].split("/")[-1], None, 1, "Ingested file")

        return {"repo_id": pk_id, "files_ingested": len(files)}

    def analyze_repo(self, payload: AnalyzeRepoRequest):
        repo_pk = payload.repo_id
        logical_repo_id = self.repo_manager.resolve_repo_id_by_pk(repo_pk)
        graph_files = self.graph_manager.query_graph(logical_repo_id)

        owner, repo = logical_repo_id.split("/")
        semantic_results = []

        for file in graph_files:
            if not file["file_path"].endswith(".py"):
                continue
            file_content = self._get_file_content(owner, repo, file["file_path"])
            nodes = self.semantic_parser.parse_python_file(file_content)
            for node in nodes:
                node["file_path"] = file["file_path"]
                self.semantic_manager.save_semantic_node(repo_pk, node)
                semantic_results.append(node)

        return {"repo_id": repo_pk, "semantic_nodes": semantic_results}

    def _get_branch_sha(self, owner, repo, branch):
        url = f"{self.base_url}/repos/{owner}/{repo}/git/ref/heads/{branch}"
        res = requests.get(url, headers=self.headers)
        res.raise_for_status()
        return res.json()["object"]["sha"]

    def _get_repo_tree(self, owner, repo, sha):
        url = f"{self.base_url}/repos/{owner}/{repo}/git/trees/{sha}?recursive=1"
        res = requests.get(url, headers=self.headers)
        res.raise_for_status()
        return res.json()

    def _get_file_content(self, owner, repo, path):
        url = f"{self.base_url}/repos/{owner}/{repo}/contents/{path}"
        res = requests.get(url, headers=self.headers)
        res.raise_for_status()
        data = res.json()
        return base64.b64decode(data["content"]).decode()
