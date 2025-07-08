import os, requests, base64
from fastapi import HTTPException
from models.federation_schemas import ImportRepoRequest
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
from models.federation_schemas import PatchASTProposal
from services.replicator.manual_review_queue import submit_to_manual_review_queue
from services.replicator.federation_patch_planner import FederatedCSTPatchPlanner
from services.github_service import GitHubService
import uuid
import json
import logging
import zipfile, io


GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")


logger = logging.getLogger(__name__)
from models.federation_schemas import PatchProposalResponse

class FederationService():
    from settings import Database

class FederationService():

    def __init__(self):
        self.base_url = 'https://api.github.com'
        self.github_token = os.getenv('FEDERATION_GITHUB_TOKEN')
        self.headers = {'Authorization': f'token {self.github_token}', 'Accept': 'application/vnd.github.v3+json'}
        self.db = Database()
        self.repo_manager = RepoManager()
        self.graph_manager = FederationGraphManager()
        self.semantic_parser = SemanticParser()
        self.semantic_manager = SemanticManager()
        self.github = GitHubService()
        self.proposal_manager = ProposalManager(self.db)
        self.ast_composer = ASTPatchComposer()
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





    def _get_branch_sha(self, owner, repo, branch):
        url = f'{self.base_url}/repos/{owner}/{repo}/git/ref/heads/{branch}'
        res = requests.get(url, headers=self.headers)
        res.raise_for_status()
        return res.json()['object']['sha']

    def get_repo_tree(self, owner, repo, branch):
        ref_url = f'{self.base_url}/repos/{owner}/{repo}/git/ref/heads/{branch}'
        ref_res = requests.get(ref_url, headers=self.headers)
        ref_res.raise_for_status()
        sha = ref_res.json()['object']['sha']
        return self.github._get_repo_tree(owner, repo, sha)

    def _get_file_content(self, owner, repo, path):
        print(f"[DEBUG] get_file_content: file_path={path}, repo={repo}, owner={owner}")
        url = f'{self.base_url}/repos/{owner}/{repo}/contents/{path}'
        res = requests.get(url, headers=self.headers)
        res.raise_for_status()
        data = res.json()
        return base64.b64decode(data['content']).decode()

    def handle_propose_patch(self, request):
        print("[propose] ▶️ Handling patch proposal request")
        proposals = []

        for patch in request.patches:
            owner, repo = request.repo_id.split("/")
            print(f"[propose] 🔍 Resolving structure for: {patch.file_path}")
            structure = self.github.parse_structure_for_file(owner, repo, patch.file_path, request.branch)
            print(f"[propose-debug] 🔬 Full structure response:\n{json.dumps(structure, indent=2)}")

            # Anchor path resolution (supports nested paths)
            anchor_match = next((s for s in structure["structure"] if s["name"] == patch.anchor), None)
            if not anchor_match:
                print("[propose] ❌ Anchor not found in structure — aborting")
                raise ValueError("Anchor not found in parsed structure")

            anchor_path = anchor_match.get("path", [patch.anchor])
            anchor_lines = [anchor_match["start_line"], anchor_match["end_line"]]

            print(f"[propose] 🎯 Resolved anchor path: {anchor_path}")
            print(f"[propose] 🧬 Anchor lines: {anchor_lines}")

            chunk_result = self.github.get_file_chunk(
                owner, repo, patch.file_path, request.branch,
                start_line=anchor_lines[0]
            )

            chunk_code = chunk_result["content"]
            print(f"[propose] 📦 Chunk lines: {chunk_result['start_line']}–{chunk_result['end_line']}, size={len(chunk_code)}")

            self.planner.context = {
                "repo_id": request.repo_id,
                "file_path": patch.file_path,
                "base_sha": chunk_result["sha"],
                "anchor_lines": anchor_lines,
                "anchor_path": anchor_path
            }

            print("[propose] 🔧 Generating patch diff")
            patch_result = self.planner.generate_patch(
                old_code=chunk_code,
                anchor=patch.anchor,
                code_block=patch.code_block
            )

            full_file_code = self.github.get_large_file_blob(owner, repo, patch.file_path, request.branch)
            old_lines = full_file_code.splitlines()
            start, end = anchor_lines
            prefix = old_lines[:start - 1]
            suffix = old_lines[end:]
            final_lines = prefix + patch_result["patched_code"].splitlines() + suffix
            patched_full_file = "\n".join(final_lines)

            sha = self.github.get_latest_file_sha(owner, repo, patch.file_path, request.branch)
            print(f"[propose-debug] Structure keys: {list(structure.keys())}")
            print(f"[propose-debug] Total anchors: {len(structure['structure'])}")
            print(f"[propose-debug] First 3 anchors: {structure['structure'][:3]}")
            print(f"[propose-debug] Looking for anchor: {patch.anchor}")
            print(f"[propose-debug] Anchor match found: {anchor_match}")

            patch_payload = {
                "repo_id": request.repo_id,
                "branch": request.branch,
                "file_path": patch.file_path,
                "base_sha": sha,
                "proposed_by": request.proposed_by,
                "commit_message": request.commit_message,
                "anchor": patch.anchor,
                "code_block": patch.code_block,
                "patched_code": patched_full_file,
                "diff": patch_result["diff"],
                "metadata": patch_result.get("metadata", {}),
                "anchor_lines": anchor_lines
            }

            print("[propose] 💾 Saving patch proposal to DB")
            proposal_id = self.proposal_manager.save_patch_proposal(patch_payload)
            print(f"[propose] ✅ Saved with ID: {proposal_id}")
            patch_payload["proposal_id"] = proposal_id

            print("[propose] 🌀 Auto-committing patch")
            self.commit_patch(patch_payload)
            proposals.append(patch_payload)

        print("[propose] ✅ Proposal flow complete")
        return proposals




    def handle_commit_patch(self, payload):
        print("[commit] ▶️ Manual commit triggered")
        proposal = self.proposal_manager.get_patch_by_id(payload.proposal_id)
        if not proposal:
            raise Exception("Patch proposal not found")

        if proposal.status not in ["approved", "manual"]:
            raise Exception("Patch not approved")

        if (
            proposal.file_path != payload.file_path or
            proposal.base_sha != payload.base_sha or
            proposal.updated_content.strip() != payload.updated_content.strip()
        ):
            raise Exception("Patch payload does not match proposal")

        patch_dict = {
            "repo_id": proposal.repo_id,
            "branch": payload.branch,
            "file_path": proposal.file_path,
            "base_sha": proposal.base_sha,
            "commit_message": payload.commit_message,
            "patched_code": payload.updated_content,
            "proposal_id": payload.proposal_id
        }

        result = self.commit_patch(patch_dict)
        print("[commit] ✅ Commit finished")
        self.proposal_manager.update_patch_status(payload.proposal_id, "committed")
        return result


    def commit_patch(self, patch):
        print("[patch] ▶️ Commit patch flow triggered")
        get = lambda obj, key: obj[key] if isinstance(obj, dict) else getattr(obj, key)

        owner, repo = get(patch, "repo_id").split("/")
        print(f"[patch] 📂 Fetching live file: {get(patch, 'file_path')} from {get(patch, 'repo_id')}@{get(patch, 'branch')}")
        live_file = self.github.get_file(
            owner=owner,
            repo=repo,
            file_path=get(patch, "file_path"),
            branch=get(patch, "branch"),
            include_meta=True
        )

        print("[patch] 🧬 Verifying SHA match")
        if live_file["sha"] != get(patch, "base_sha"):
            print(f"[patch] ❌ SHA mismatch: {live_file['sha']} vs {get(patch, 'base_sha')}")
            raise Exception("SHA mismatch: file has changed since patch proposal")

        if live_file["content"].strip() == get(patch, "patched_code").strip():
            print("[patch] 🚫 No changes detected — skipping")
            return {"status": "noop", "reason": "No changes to apply"}

        print("[patch] 🌀 Committing to GitHub")
        commit_result = self.commit_patch_to_github(
            owner=owner,
            repo=repo,
            file_path=get(patch, "file_path"),
            branch=get(patch, "branch"),
            content=get(patch, "patched_code"),
            sha=get(patch, "base_sha"),
            message=get(patch, "commit_message")
        )


        if hasattr(patch, "proposal_id") or (isinstance(patch, dict) and "proposal_id" in patch):
            pid = get(patch, "proposal_id")
            print(f"[patch] 📦 Updating DB status to committed for proposal {pid}")
            self.proposal_manager.update_patch_status(pid, "committed")

        print("[patch] ✅ Patch committed")
        return {"status": "patch_committed", "data": commit_result}

    def commit_patch_to_github(self, owner, repo, file_path, branch, content, sha, message):
        url = f"{self.base_url}/repos/{owner}/{repo}/contents/{file_path}"
        payload = {
            "message": message,
            "content": base64.b64encode(content.encode("utf-8")).decode("utf-8"),
            "sha": sha,
            "branch": branch
        }
        res = requests.put(url, headers=self.headers, json=payload)
        if not res.ok:
            print(f"[commit] ❌ GitHub error: {res.status_code} - {res.text}")
        res.raise_for_status()
        return res.json()
