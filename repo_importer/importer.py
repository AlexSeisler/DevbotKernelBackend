# Core Zip → Node logic will be migrated here from FederationService

from fastapi import HTTPException
from models.federation_schemas import ImportRepoRequest
from services.federation_service import FederationService

service = FederationService()
import os
import tempfile
from fastapi import HTTPException
from services.github_service import fetch_github_repo
from services.semantic_parser import extract_semantic_nodes
from models.semantic_nodes import insert_nodes
from repo_importer.tagging_hook import tag_semantic_node
from repo_importer.import_quality import emit_quality_report

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")


logger = logging.getLogger(__name__)


class FederationService():

    def __init__(self):
        self.base_url = 'https://api.github.com'
        self.github_token = os.getenv('FEDERATION_GITHUB_TOKEN')
        self.headers = {'Authorization': f'token {self.github_token}', 'Accept': 'application/vnd.github.v3+json'}
        self.db = _db_instance
        self.repo_manager = RepoManager()
        self.graph_manager = FederationGraphManager()
        self.semantic_parser = SemanticParser()
        self.semantic_manager = SemanticManager()
        self.github = GitHubService()
        self.proposal_manager = ProposalManager(self.db)
        self.planner = FederatedCSTPatchPlanner()


    def _tag_semantic_node(self, node):
        tags = []

        name = node.get("name", "")
        node_type = node.get("node_type", "")
        decorators = node.get("decorators", [])
        file_path = node.get("file_path", "")

        if "test" in file_path:
            tags.append("test")
        if "infra" in file_path or "ops" in file_path:
            tags.append("infra")
        if node_type == "decorator":
            tags.append("decorator")
        if name in {"main", "__init__", "run"}:
            tags.append("entrypoint")
        if name.startswith("_"):
            tags.append("internal")
        if any(k in d for d in decorators for k in ("get", "post", "route")):
            tags.append("http")
        if not tags:
            tags.append("util")

        return tags

    def _tag_all_semantic_nodes(self, nodes):
        for node in nodes:
            node['tags'] = self._tag_semantic_node(node)
        return nodes

    def import_repo(self, payload: ImportRepoRequest):
        import tempfile
        from services.semantic_parser import parse_large_python_file

        (owner, repo, branch) = (payload.owner, payload.repo, payload.default_branch)
        local_repo_id = f'{owner}/{repo}'
        print(f'[FEDERATION IMPORT] Starting import for: {local_repo_id}')

        existing_id = self.repo_manager.try_resolve_pk(local_repo_id)
        if existing_id:
            print(f'[FEDERATION IMPORT] Repo already ingested: {local_repo_id} (ID={existing_id})')
            return {'repo_id': existing_id, 'files_ingested': 0}

        print(f'[FEDERATION IMPORT] New repo detected: {local_repo_id}')
        try:
            gh_repo_id = self.github.get_repo_id(owner, repo)
        except Exception as e:
            raise Exception(f'GitHub repo ID resolution failed: {str(e)}')

        pk_id = self.repo_manager.insert_or_update_repo(
            repo_id=gh_repo_id,
            owner=owner,
            repo=repo,
            branch=branch,
            root_sha=self._get_branch_sha(owner, repo, branch),
        )
        print(f'[FEDERATION IMPORT] Finalized ingest: local={local_repo_id}, pk={pk_id}')

        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        zip_url = f"https://api.github.com/repos/{owner}/{repo}/zipball/{branch}"
        print(f"[ZIPBALL] Downloading: {zip_url}")
        response = requests.get(zip_url, headers=headers, stream=True)
        if response.status_code != 200:
            raise Exception(f"Zipball download failed: {response.status_code} — {response.text}")

        supported_exts = {".py", ".rs", ".ts", ".js"}
        files_scanned = 0
        semantic_results = []
        failed = []
        heavy_file_queue = []

        MAX_INLINE_LINES = 1500

        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = os.path.join(tmpdir, f"{repo}.zip")
            with open(zip_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                print("[ZIPBALL] Streaming and parsing source files...")
                for zip_info in zip_ref.infolist():
                    fname = zip_info.filename
                    if not any(fname.endswith(ext) for ext in supported_exts):
                        continue
                    try:
                        with zip_ref.open(zip_info) as file:
                            try:
                                content = file.read().decode("utf-8", errors="ignore")
                            except Exception as decode_error:
                                print(f"[💣 DECODE ERROR] {fname}: {decode_error}")
                                failed.append((fname, 'decode'))
                                continue

                            rel_path = fname
                            line_count = content.count("\n")

                            if line_count > MAX_INLINE_LINES:
                                heavy_file_queue.append((rel_path, content))
                                print(f"[QUEUED] {fname} ({line_count} lines) → heavy parser queue")
                                continue

                            try:
                                nodes = self.semantic_parser.parse_python_file(content, file_path=rel_path)
                            except Exception:
                                nodes = [{
                                    "name": os.path.basename(rel_path),
                                    "node_type": "blob",
                                    "docstring": None,
                                    "args": [],
                                    "decorators": [],
                                    "parents": [],
                                    "returns": None,
                                    "file_path": rel_path,
                                    "code_block": "",
                                    "interface_type": None
                                }]

                            for node in nodes:
                                node['file_path'] = rel_path
                            nodes = self._tag_all_semantic_nodes(nodes)
                            semantic_results.extend(nodes)
                            files_scanned += 1
                    except Exception as e:
                        print(f'[FAIL] Skipped {fname} 💥 parse error: {e}')
                        failed.append((fname, 'parse'))

            # 🧠 Phase 1: Offload heavy files to subprocess-based parser
            for rel_path, content in heavy_file_queue:
                try:
                    nodes = parse_large_python_file(content)
                    for node in nodes:
                        node['file_path'] = rel_path
                    nodes = self._tag_all_semantic_nodes(nodes)
                    semantic_results.extend(nodes)
                    files_scanned += 1
                except Exception as e:
                    print(f"[SUBPROCESS FAIL] {rel_path}: {e}")
                    failed.append((rel_path, 'heavy_parse'))

        self.semantic_manager.bulk_save_semantic_nodes(pk_id, semantic_results)
        print(f'✅ Saved {len(semantic_results)} semantic nodes from {files_scanned} files.')

        return {
            'repo_id': pk_id,
            'files_scanned': files_scanned,
            'semantic_nodes_extracted': len(semantic_results),
            'failed': failed
        }
