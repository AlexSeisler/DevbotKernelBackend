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



class FederationService:
    def __init__(self):
        self.base_url = "https://api.github.com"
        self.github_token = os.getenv("FEDERATION_GITHUB_TOKEN")
        self.headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        self.db = Database().get_connection()
        self.repo_manager = RepoManager()
        self.graph_manager = FederationGraphManager()
        self.semantic_parser = SemanticParser()
        self.semantic_manager = SemanticManager()
        self.github = GitHubService()

    def import_repo(self, payload: ImportRepoRequest):
        owner, repo, branch = payload.owner, payload.repo, payload.default_branch
        logical_repo_id = f"{owner}/{repo}"

        # ✅ REMOVE GITHUB API CALLS — Direct internal ingestion logic
        # ✅ For cleanroom bootstrap, manually define files you want to ingest:
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

        # ✅ Static root SHA for initial bootstrap (since no external tree is loaded)
        static_root_sha = "bootstrap-root-sha"

        try:
            with self.db:
                with self.db.cursor() as cur:
                    # ✅ Insert directly into federation_repo
                    pk_id = self.repo_manager.save_repo_tx(cur, logical_repo_id, branch, static_root_sha)

                    # ✅ Insert each file into federation_graph using full PK resolver
                    for file in files:
                        self.graph_manager.insert_graph_link_tx(
                            cur,
                            logical_repo_id,  # 🔧 This will be resolved to PK internally by graph manager
                            file['path'],
                            file['type'],
                            file['path'].split("/")[-1],
                            None,
                            1.0,
                            "Bootstrap ingestion"
                        )

            return {"repo_id": pk_id, "files_ingested": len(files)}

        except Exception as e:
            raise Exception(f"Federation ingestion transaction failed: {str(e)}")


    def analyze_repo(self, payload: AnalyzeRepoRequest):
        repo_pk = payload.repo_id
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

    def commit_patch(self, payload):
        """
        Wrapper to GitHubService.commit_patch that aligns with Federation logic
        """
        result = []
        for patch in payload["patches"]:
            patch_obj = CommitPatchObject(**patch)
            patch_obj.commit_message = payload["commit_message"]
            patch_obj.branch = payload["branch"]
            result.append(
                self.github.commit_patch(patch_obj)
            )
        return {"status": "committed", "results": result}
