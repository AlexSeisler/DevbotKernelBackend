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
from services.replicator.ast_patch_composer import ASTPatchComposer
from services.replicator.manual_review_queue import submit_to_manual_review_queue
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
        self.db = Database() 
        self.repo_manager = RepoManager()
        self.graph_manager = FederationGraphManager()
        self.semantic_parser = SemanticParser()
        self.semantic_manager = SemanticManager()
        self.github = GitHubService()
        self.proposal_manager = ProposalManager()
        self.ast_composer = ASTPatchComposer()

    # PATCHED import_repo WITH owner/repo PERSISTENCE

    def import_repo(self, payload: ImportRepoRequest):
        owner, repo, branch = payload.owner, payload.repo, payload.default_branch
        logical_repo_id = f"{owner}/{repo}"
        print(f"[FEDERATION IMPORT] Attempting import for: {logical_repo_id}")

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
                    print(f"[FEDERATION IMPORT] Repo already ingested: {logical_repo_id} (ID={existing_id})")
                    return {"repo_id": existing_id, "files_ingested": 0}

                print(f"[FEDERATION IMPORT] New repo detected: {logical_repo_id}")
                print(f"[INSERT CALL] About to insert repo_id={resolved_id}, owner={owner}, repo={repo}")

                pk_id = self.repo_manager.insert_or_update_repo(
                    repo_id=self.github.get_repo_id(owner, repo),
                    owner=owner,
                    repo=repo,
                    branch=branch,
                    root_sha=static_root_sha
                )

                for file in files:
                    self.graph_manager.insert_graph_link_tx(
                        cur,
                        logical_repo_id,
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
            print(f"[FEDERATION IMPORT ERROR] {type(e).__name__}: {e}")
            if conn:
                conn.rollback()
            raise Exception(f"Federation ingestion transaction failed: {str(e)}")

        finally:
            if conn:
                self.db.release_connection(conn)





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
        try:
            # Assume we already have updated_content from AST composer
            if not payload.updated_content:
                old_content = self.github.get_file_content(payload.file_path, payload.branch)
                base_sha = self.github.get_latest_file_sha(payload.file_path, payload.branch)

                def noop_mutator(tree): return tree
                patch = self.ast_composer.compose_patch(
                    old_content=old_content,
                    new_ast_mutator=noop_mutator,
                    file_path=payload.file_path,
                    base_sha=base_sha
                )
                payload.updated_content = patch.updated_content

            repo_name = self.repo_manager.get_slug_by_id(payload.repo_id)
            result = self.github.commit_patch(
                repo_name=repo_name,  # ✅ use owner/repo slug
                branch=payload.branch,
                file_path=payload.file_path,
                commit_message=payload.commit_message,
                base_sha=payload.base_sha,
                updated_content=payload.updated_content
            )
            return {"status": "committed", "result": result}

        except Exception as e:
            submit_to_manual_review_queue(
                file_path=payload.file_path,
                old_content=old_content if 'old_content' in locals() else "",
                new_content=payload.updated_content if payload.updated_content else "",
                base_sha=payload.base_sha,
                error_reason=str(e)
            )
            raise Exception(f"Commit patch failed and was routed to review queue: {str(e)}")




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