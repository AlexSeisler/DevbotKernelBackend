import os
import requests
import json
from fastapi import HTTPException
from models.federation_schemas import ImportRepoRequest, AnalyzeRepoRequest
from services.db.repo_manager import RepoManager
from services.db.federation_graph_manager import FederationGraphManager
from settings import Database
from services.semantic_parser import SemanticParser
from services.diff_engine import DiffEngine
from services.proposal_queue import ProposalQueueManager


class FederationService:

    def __init__(self):
        self.base_url = "https://api.github.com"
        self.github_token = os.getenv("FEDERATION_GITHUB_TOKEN", os.getenv("GITHUB_TOKEN")).strip()

        self.headers = {
            "Authorization": (
                f"Bearer {self.github_token}" if self.github_token.startswith("github_pat_")
                else f"token {self.github_token}"
            ),
            "Accept": "application/vnd.github.v3+json"
        }
        if not self.github_token:
            raise ValueError("GitHub OAuth token not found.")

        self.db = Database().get_connection()
        self.repo_manager = RepoManager()
        self.graph_manager = FederationGraphManager()
        self.semantic_parser = SemanticParser()
        self.diff_engine = DiffEngine()
        self.proposal_queue = ProposalQueueManager()

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
            file_path = item.get("path")
            files.append({
                "path": file_path,
                "type": item.get("type"),
                "sha": item.get("sha")
            })

        try:
            with self.db:
                with self.db.cursor() as cur:
                    # ✅ FIRST: Insert into federation_repo and retrieve PK
                    cur.execute("""
                        INSERT INTO federation_repo (repo_id, branch, root_sha)
                        VALUES (%s, %s, %s)
                        RETURNING id
                    """, (f"{owner}/{repo}", branch, tree_data.get("sha")))
                    repo_pk = cur.fetchone()[0]

                    # ✅ THEN: Insert graph records using committed PK
                    for file in files:
                        cur.execute("""
                            INSERT INTO federation_graph (repo_id, file_path, node_type, name, cross_linked_to, federation_weight, notes)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """, (
                            repo_pk,
                            file['path'],
                            file['type'],
                            file['path'].split("/")[-1],
                            None,
                            1,
                            "Ingested file"
                        ))

            return {
                "status": "success",
                "repo_id": repo_pk,
                "files_ingested": len(files)
            }

        except Exception as e:
            raise Exception(f"Federation ingestion transaction failed: {str(e)}")


    # 🔧 PATCHED: Repo ID resolver added here
    def resolve_repo_pk(self, owner, repo):
        full_repo_id = f"{owner}/{repo}"
        repo_entry = self.repo_manager.get_repo_by_repo_id(full_repo_id)
        if not repo_entry:
            raise HTTPException(status_code=404, detail="Repository not found in ingestion DB")
        return repo_entry['repo_id']

    def analyze_repo(self, payload: AnalyzeRepoRequest):
        repo_id = payload.repo_id

        # ✅ Translate repo_id PK to logical repo_id
        logical_repo_id = self.resolve_repo_id(repo_id)

        graph_files = self.federation_graph.query_graph(repo_id=logical_repo_id)
        owner, repo = logical_repo_id.split("/")
        branch = "master"  # still static for now

        semantic_results = []
        for file_entry in graph_files:
            file_path = file_entry["file_path"]
            if not file_path.endswith(".py"):
                continue

            file_url = f"{self.base_url}/repos/{owner}/{repo}/contents/{file_path}?ref={branch}"
            file_resp = requests.get(file_url, headers=self.headers)
            file_resp.raise_for_status()

            file_data = file_resp.json()
            file_content = self._decode_github_content(file_data.get("content"))

            file_nodes = self.semantic_parser.parse_python_file(file_content)
            for node in file_nodes:
                node["file_path"] = file_path
                semantic_results.append(node)

        return {"repo_id": repo_id, "semantic_nodes": semantic_results}





    def _decode_github_content(self, encoded_content):
        import base64
        decoded_bytes = base64.b64decode(encoded_content)
        return decoded_bytes.decode("utf-8")

    def propose_patch(self, payload):
        proposal = {
            "repo_id": payload.repo_id,
            "branch": payload.branch,
            "proposed_by": payload.proposed_by,
            "commit_message": payload.commit_message,
            "patches": [
                {
                    "file_path": patch.file_path,
                    "base_sha": patch.base_sha,
                    "updated_content": patch.updated_content
                } for patch in payload.patches
            ]
        }
        proposal_id = self.proposal_queue.submit_proposal(proposal)
        return {"proposal_id": proposal_id}

    def commit_patch(self, payload):
        owner, repo = payload.repo_id.split("/")
        result = self.diff_engine.apply_patch(
            owner=owner,
            repo=repo,
            branch=payload.branch,
            patches=payload.patches,
            commit_message=payload.commit_message
        )
        return result

    def scan_federation_graph(self):
        return {"repos_federated": [], "total_nodes": 0}

    def list_proposals(self):
        return self.proposal_queue.list_proposals()

    def approve_patch(self, proposal_id):
        proposal = self.proposal_queue.approve_proposal(proposal_id)
        owner, repo = proposal["repo_id"].split("/")
        result = self.diff_engine.apply_patch(
            owner=owner,
            repo=repo,
            branch=proposal["branch"],
            patches=proposal["patches"],
            commit_message=proposal["commit_message"]
        )
        self.proposal_queue.remove_proposal(proposal_id)
        return result

    def reject_patch(self, proposal_id):
        proposal = self.proposal_queue.reject_proposal(proposal_id)
        return {"status": "rejected", "proposal_id": proposal_id}
