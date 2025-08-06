import os, requests, base64
from fastapi import HTTPException
from models.federation_schemas import ImportRepoRequest
from services.semantic_parser import SemanticParser
from services.db.repo_manager import RepoManager
from services.db.federation_graph_manager import FederationGraphManager
from services.db.semantic_manager import SemanticManager
from settings import _db_instance
from services.github_service import GitHubService
from services.db.proposal_manager import ProposalManager
from services.replicator.federation_patch_planner import FederatedCSTPatchPlanner
from services.github_service import GitHubService
import uuid
import json
import logging
import zipfile, io


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

            anchor_match = next((s for s in structure["structure"] if s["name"] == patch.anchor), None)
            if not anchor_match:
                raise ValueError(f"Anchor '{patch.anchor}' not found in file structure")

            anchor_path = anchor_match.get("path", [patch.anchor])

            # 🔐 Patch strategy validation
            if patch.patch_strategy in ("replace", "delete"):
                if patch.anchor_lines:
                    anchor_lines = patch.anchor_lines  # ✅ Explicit override
                else:
                    raise ValueError(f"❌ Strategy '{patch.patch_strategy}' requires explicit 'anchor_lines' — none provided.")
            else:
                # ✅ Fallback to parsed structure only for safe strategies
                if patch.anchor_lines:
                    anchor_lines = patch.anchor_lines
                else:
                    anchor_lines = [anchor_match["start_line"], anchor_match["end_line"]]

            print(f"[propose] 🎯 Resolved anchor path: {anchor_path}")
            print(f"[propose] 🧬 Anchor lines: {anchor_lines}")

            full_file_code = self.github.get_large_file_blob(owner, repo, patch.file_path, request.branch)
            print(f"[propose-debug] 📄 Original file preview (first 300 chars):\n{full_file_code[:300]}")

            latest_sha = self.github.get_latest_file_sha(owner, repo, patch.file_path, request.branch)
            print(f"[DEBUG] get_latest_file_sha for: {patch.file_path}, branch={request.branch} = {latest_sha}")

            patch_strategy = getattr(patch, "patch_strategy", "insert")  # 🔧 Default strategy handling

            self.planner.context = {
                "repo_id": request.repo_id,
                "file_path": patch.file_path,
                "base_sha": latest_sha,
                "anchor_lines": anchor_lines,
                "anchor_path": anchor_path,
                "patch_strategy": patch_strategy  # 🔧 Pass into planner
            }

            print("[propose] 🔧 Generating patch diff")
            patch_result = self.planner.generate_patch(
                old_code=full_file_code,
                anchor=patch.anchor,
                code_block=patch.code_block,
                patch_strategy=patch_strategy  # 🔧 Planner injection
            )

            patch_payload = {
                "repo_id": request.repo_id,
                "branch": request.branch,
                "file_path": patch.file_path,
                "base_sha": self.planner.context["base_sha"],
                "proposed_by": request.proposed_by,
                "commit_message": request.commit_message,
                "anchor": patch.anchor,
                "code_block": patch.code_block,
                "patched_code": patch_result["patched_code"],
                "diff": patch_result["diff"],
                "metadata": patch_result.get("metadata", {}),
                "anchor_lines": anchor_lines,
                "anchor_path": anchor_path,
                "patch_strategy": patch_strategy  # 🔧 Add to DB payload
            }


            proposal_id = self.proposal_manager.save_patch_proposal(patch_payload)
            patch_payload["proposal_id"] = proposal_id

            print("[propose] 🌀 Auto-committing patch")
            self.commit_patch(patch_payload)
            proposals.append(patch_payload)

        print("[propose] ✅ Proposal flow complete")
        return proposals

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
        # 🧠 Structure Cache Refresh (post-commit only)
        from services.db.structure_cache_manager import StructureCacheManager
        from datetime import datetime

        structure_manager = StructureCacheManager(self.db)
        new_sha = commit_result['content']['sha']

        structure_result = self.github.parse_structure_for_file(
            owner, repo, file_path=get(patch, "file_path"), branch=get(patch, "branch"), update_cache=True
        )

        structure_rows = []
        for anchor in structure_result['structure']:
            structure_rows.append({
                'repo_id': get(patch, "repo_id"),
                'branch': get(patch, "branch"),
                'file_path': get(patch, "file_path"),
                'sha': new_sha,
                'anchor_path': anchor.get('path') or [anchor['name']],
                'anchor_name': anchor['name'],
                'anchor_type': anchor['type'],
                'start_line': anchor['start_line'],
                'end_line': anchor['end_line'],
                'created_at': datetime.utcnow()
            })

        structure_manager.delete_structure_cache(
            get(patch, "repo_id"),
            get(patch, "file_path"),
            get(patch, "branch"),
            new_sha
        )
        structure_manager.insert_structure_rows(structure_rows)
        print("[patch] 🧠 Structure cache refreshed")

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