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
    from settings import Database

class FederationService:
    def __init__(self):
        self.base_url = "https://api.github.com"
        self.github_token = os.getenv("FEDERATION_GITHUB_TOKEN")
        self.headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json"
        }

        # Setup a shared DB pool (not a raw connection)
        self.db = Database()  # store pool object
        self.repo_manager = RepoManager()
        self.graph_manager = FederationGraphManager()
        self.semantic_parser = SemanticParser()
        self.semantic_manager = SemanticManager()
        self.github = GitHubService()
        self.proposal_manager = ProposalManager()

    def import_repo(self, payload: ImportRepoRequest):
        owner, repo, branch = payload.owner, payload.repo, payload.default_branch
        logical_repo_id = f"{owner}/{repo}"

        # ✅ Cleanroom ingest stub
        files = [
            {
                "path": "dashboard/README.md",
                "type": "file",
                "sha": "bootstrap-sha-readme"
            },
            {
                "path": "dashboard/new_module.py",
                "type": "file",
                "sha": "bootstrap-sha-newmodule"
            }
        ]

        static_root_sha = "bootstrap-root-sha"
        
        conn = None
        try:
            conn = self.db.get_connection()
            with conn.cursor() as cur:
                existing_id = self.repo_manager.try_resolve_pk(logical_repo_id)
                if existing_id:
                    raise Exception(f"Repo already ingested: {logical_repo_id} (ID={existing_id})")

                pk_id = self.repo_manager.save_repo_tx(cur, logical_repo_id, branch, static_root_sha)

                for file in files:
                    self.graph_manager.insert_graph_link_tx(
                        cur,
                        logical_repo_id,  # Will be resolved to PK
                        file["path"],
                        file["type"],
                        file["path"].split("/")[-1],
                        None,
                        1.0,
                        "Bootstrap ingestion"
                    )

            conn.commit()
            return {"repo_id": pk_id, "files_ingested": len(files)}

        except Exception as e:
            if conn:
                conn.rollback()
            raise Exception(f"Federation ingestion transaction failed: {str(e)}")

        finally:
            if conn:
                self.db.release_connection(conn)




    def analyze_repo(self, payload: AnalyzeRepoRequest):
        repo_pk = payload.repo_id  # 🔧 Correct use of typed Pydantic input
        logical_repo_id = self.repo_manager.resolve_repo_id_by_pk(repo_pk)
        owner, repo = logical_repo_id.split("/")
        semantic_results = []

        # ✅ Step 1: Get branch SHA
        branch_sha = self.github.get_branch_sha("test-kernel-branch")["object"]["sha"]

        # ✅ Step 2: Get full repo tree (recursive)
        repo_tree_data = self.github.get_repo_tree(branch_sha, recursive=True)
        repo_tree = repo_tree_data["tree"]

        # ✅ Step 3: Scan .py files and parse AST
        for file in repo_tree:
            file_path = file.get("path", "")
            if not file_path.endswith(".py"):
                continue

            try:
                raw_file = self.github.get_file(file_path, "test-kernel-branch")
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




    def _get_branch_sha(self, owner, repo, branch):
        url = f"{self.base_url}/repos/{owner}/{repo}/git/ref/heads/{branch}"
        res = requests.get(url, headers=self.headers)
        res.raise_for_status()
        return res.json()["object"]["sha"]

    def get_repo_tree(self, owner, repo, branch):
        # Step 1: Get latest commit SHA for the branch
        ref_url = f"{self.base_url}/repos/{owner}/{repo}/git/ref/heads/{branch}"
        ref_res = requests.get(ref_url, headers=self.headers)
        ref_res.raise_for_status()
        sha = ref_res.json()["object"]["sha"]

        # Step 2: Get full tree using SHA
        return self.github._get_repo_tree(owner, repo, sha)



    def _get_file_content(self, owner, repo, path):
        url = f"{self.base_url}/repos/{owner}/{repo}/contents/{path}"
        res = requests.get(url, headers=self.headers)
        res.raise_for_status()
        data = res.json()
        return base64.b64decode(data["content"]).decode()

    def commit_patch(self, payload: CommitPatchRequest):
        conn = None
        result = []

        try:
            conn = self.db.get_connection()
            with conn.cursor() as cur:
                patch_obj = CommitPatchObject(
                    repo_id=payload.repo_id,
                    branch=payload.branch,
                    file_path=payload.file_path,
                    commit_message=payload.commit_message,
                    base_sha=payload.base_sha,
                    updated_content=payload.updated_content
                )
                result.append(self.github.commit_patch(patch_obj))

            conn.commit()
            return {"status": "committed", "results": result}

        except Exception as e:
            if conn:
                conn.rollback()
            raise Exception(f"Commit patch failed: {str(e)}")

        finally:
            if conn:
                self.db.release_connection(conn)



    def propose_patch(self, payload):
        proposal = {
            "proposal_id": str(uuid.uuid4()),
            "repo_id": int(payload.repo_id),  # ensure PK int if required
            "branch": payload.branch,
            "proposed_by": payload.proposed_by,
            "commit_message": payload.commit_message,
            "patches": [patch.dict() for patch in payload.patches],
            "status": "pending"
        }
        self.proposal_manager.save_proposal(proposal)
        return {"message": "Patch proposal saved"}