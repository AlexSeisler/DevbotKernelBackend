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
import uuid
import json
import logging

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
        self.proposal_manager = ProposalManager()
        self.ast_composer = ASTPatchComposer()

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

        repo_tree = self.github.get_repo_tree(owner, repo, branch, recursive=True)

        chunk_size = 50
        semantic_results = []
        failed = []

        for i in range(0, len(repo_tree), chunk_size):
            chunk = repo_tree[i:i+chunk_size]
            for file in chunk:
                file_path = file.get('path', '')
                if not file_path.endswith('.py'):
                    continue

                try:
                    if self.semantic_manager.semantic_nodes_exist(pk_id, file_path):
                        print(f'[DUP SKIP] Already ingested: {file_path}')
                        continue

                    raw_file = self.github.get_file(owner, repo, file_path, branch)
                    file_content = base64.b64decode(raw_file['content']).decode()

                    nodes = self.semantic_parser.parse_python_file(file_content)
                    for node in nodes:
                        node['file_path'] = file_path
                    nodes = self._tag_all_semantic_nodes(nodes)
                    for node in nodes:
                        self.semantic_manager.save_semantic_node(pk_id, node)
                        semantic_results.append(node)
                except Exception as e:
                    print(f'[FAIL] Skipped {file_path} – parse error: {e}')
                    failed.append((file_path, 'parse'))

        return {
            'repo_id': pk_id,
            'files_scanned': len(repo_tree),
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

    def commit_patch(self, proposal_id: str):
        try:

            print(f"[TRACE] commit_patch() called with proposal_id: {proposal_id}")

            proposal = self.proposal_manager.get_proposal_by_id(proposal_id)
            if not proposal:
                raise Exception(f"Patch proposal ID '{proposal_id}' not found.")
            
            print(f"[DEBUG] commit_patch: proposal_id={proposal_id}")
            print(f"[DEBUG] repo_id from proposal: {proposal['repo_id']} ({type(proposal['repo_id'])})")
            print(f"[DEBUG] file_path: {patch['file_path']}")

            
            patch = proposal['patches'][0]
            file_path = patch['file_path']
            updated_content = patch['updated_content']
            base_sha = patch['base_sha']
            repo_id = proposal['repo_id']
            manual = patch.get('manual', False)
            slug = self.repo_manager.get_slug_by_id(repo_id)
            (owner, repo) = slug.split('/')
            current_file = self.github.get_file(owner, repo, file_path, proposal['branch'])
            current_content = base64.b64decode(current_file['content']).decode()
            current_sha = current_file['sha']

            if not manual:
                import ast
                from services.replicator.ast_patch_composer import compare_ast
                old_ast = ast.parse(current_content)
                new_ast = ast.parse(updated_content)
                compare_ast(old_ast, new_ast)

            if (current_sha != base_sha) and (base_sha != 'MANUAL'):
                raise Exception(f"File SHA has changed since proposal: now {current_sha}, was {base_sha}")

            result = self.github.commit_patch(
                repo_name=slug,
                branch=proposal['branch'],
                file_path=file_path,
                commit_message=proposal['commit_message'],
                base_sha=current_sha,
                updated_content=updated_content
            )
            return {'status': 'committed', 'result': result}
        except Exception as e:
            raise Exception(f"Commit failed: {str(e)}")

    def propose_patch(self, owner, repo, file_path, branch, manual: bool = False, updated_content: str = None):
        try:
            if not updated_content:
                raise Exception(f"[PATCH REJECTED] No updated content provided.")

            current_file = self.github.get_file(owner, repo, file_path, branch)
            current_content = base64.b64decode(current_file['content']).decode()
            current_sha = current_file['sha']

            if not manual:
                from services.replicator.ast_patch_composer import compare_ast
                old_ast = ast.parse(current_content)
                new_ast = ast.parse(updated_content)

                if ast.dump(old_ast) == ast.dump(new_ast):
                    raise Exception(f"[PATCH REJECTED] No AST-level change detected.")

            patch = {
                'file_path': file_path,
                'base_sha': current_sha,
                'updated_content': updated_content,
                'manual': manual,
                'risk_class': 'MANUAL' if manual else 'AUTO',
                'diff_summary': 'Manual override' if manual else 'AST-computed diff'
            }

            proposal_id = str(uuid.uuid4())
            self.proposal_manager.save_proposal({
                'proposal_id': proposal_id,
                'repo_id': self.repo_manager.get_repo_by_slug(f'{owner}/{repo}'),
                'branch': branch,
                'proposed_by': 'DevBot',
                'patches': [patch],
                'status': 'pending'
            })

            return PatchProposalResponse(patches=[PatchASTProposal(**patch)])
        except Exception as e:
            print(f"[ERROR] propose_patch failed: {str(e)}")
            raise
