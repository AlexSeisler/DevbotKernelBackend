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
from models.federation_schemas import PatchASTProposal
from services.replicator.manual_review_queue import submit_to_manual_review_queue
import uuid
import json
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

    def import_repo(self, payload: ImportRepoRequest):
        (owner, repo, branch) = (payload.owner, payload.repo, payload.default_branch)
        logical_repo_id = f'{owner}/{repo}'
        print(f'[FEDERATION IMPORT] Attempting import for: {logical_repo_id}')
        existing_id = self.repo_manager.try_resolve_pk(logical_repo_id)
        if existing_id:
            print(f'[FEDERATION IMPORT] Repo already ingested: {logical_repo_id} (ID={existing_id})')
            return {'repo_id': existing_id, 'files_ingested': 0}
        print(f'[FEDERATION IMPORT] New repo detected: {logical_repo_id}')
        print(f'[INSERT CALL] About to insert logical_repo_id={logical_repo_id}, owner={owner}, repo={repo}')
        try:
            gh_repo_id = self.github.get_repo_id(owner, repo)
        except Exception as e:
            raise Exception(f'GitHub repo ID resolution failed: {str(e)}')
        pk_id = self.repo_manager.insert_or_update_repo(repo_id=gh_repo_id, owner=owner, repo=repo, branch=branch, root_sha='bootstrap-root-sha')
        print(f'[FEDERATION IMPORT] Finalized ingest: logical={logical_repo_id}, pk={pk_id}')
        return {'repo_id': pk_id, 'files_ingested': 0}

    def analyze_repo(self, payload: AnalyzeRepoRequest):
        repo_pk = payload.repo_id
        logical_repo_id = self.repo_manager.resolve_repo_id_by_pk(repo_pk)
        (owner, repo) = logical_repo_id.split('/')
        semantic_results = []
        branch_sha = self.github.get_branch_sha('AlexSeisler', 'DevbotKernelBackend', 'main')['object']['sha']
        repo_tree_data = self.github.get_repo_tree('AlexSeisler', 'DevbotKernelBackend', 'main', recursive=True)
        repo_tree = repo_tree_data['tree']
        for file in repo_tree:
            file_path = file.get('path', '')
            if (not file_path.endswith('.py')):
                continue
            try:
                raw_file = self.github.get_file('AlexSeisler', 'DevbotKernelBackend', file_path, 'main', fallback=True)
                file_content = base64.b64decode(raw_file['content']).decode()
            except Exception as e:
                print(f'⚠️ Skipped file {file_path} due to fetch error: {e}')
                continue
            nodes = self.semantic_parser.parse_python_file(file_content)
            for node in nodes:
                node['file_path'] = file_path
                self.semantic_manager.save_semantic_node(repo_pk, node)
                semantic_results.append(node)
        return {'repo_id': repo_pk, 'semantic_nodes': semantic_results}

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
        url = f'{self.base_url}/repos/{owner}/{repo}/contents/{path}'
        res = requests.get(url, headers=self.headers)
        res.raise_for_status()
        data = res.json()
        return base64.b64decode(data['content']).decode()

    def commit_patch(self, proposal_id: str):
        try:
            proposal = self.proposal_manager.get_proposal_by_id(proposal_id)
            if not proposal:
                raise Exception(f"Patch proposal ID '{proposal_id}' not found.")

            file_path = proposal['patches'][0]['file_path']
            updated_content = proposal['patches'][0]['updated_content']
            base_sha = proposal['patches'][0]['base_sha']
            repo_id = proposal['repo_id']
            manual = proposal['patches'][0].get('manual', False)

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
            else:
                if (current_sha != base_sha) and (base_sha != 'MANUAL'):
                    raise Exception(f"File SHA has changed since proposal: now {current_sha}, was {base_sha}")

            # New: Re-run LibCST comparison to validate final patch diff
            from services.replicator.libcst_comparator import LibCSTDeltaEngine
            deltas = LibCSTDeltaEngine.compare(current_content, updated_content)
            if not deltas:
                raise Exception("LibCST validation failed: no meaningful delta found.")

            # Commit
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
            raise Exception(f'Commit failed: {str(e)}')


    def propose_patch(self, owner, repo, file_path, branch, manual: bool = False, updated_content: str = None):
        try:
            if manual:
                patch_dict = {
                    'file_path': file_path,
                    'base_sha': 'MANUAL',
                    'updated_content': updated_content,
                    'risk_class': 'MANUAL',
                    'diff_summary': 'Manual override patch',
                    'manual': True
                }
            else:
                file_data = self.github.get_file(owner, repo, file_path, branch)
                b64_content = file_data.get('content')
                sha = file_data.get('sha')
                if not b64_content:
                    raise Exception('File has no content')

                old_content = base64.b64decode(b64_content).decode()
                base_sha = sha

                # LibCST Transformer path (real patch)
                from services.replicator.transformers import DocstringUpdateTransformer
                from services.replicator.libcst_patch_core import LibCSTMutator, LibCSTDeltaEngine
                import json

                transformer = lambda: DocstringUpdateTransformer("Patched by LibCST engine")
                updated_content = LibCSTMutator.apply(old_content, transformer)
                deltas = LibCSTDeltaEngine.compare(old_content, updated_content)

                summary = [delta.detail for delta in deltas]
                risk_class = 'SAFE' if len(deltas) <= 3 else 'REVIEW'
                diff_summary = json.dumps(summary, indent=2)

                patch_dict = {
                    'file_path': file_path,
                    'base_sha': base_sha,
                    'updated_content': updated_content,
                    'risk_class': risk_class,
                    'diff_summary': diff_summary,
                    'manual': False
                }

            proposal_id = str(uuid.uuid4())
            self.proposal_manager.save_proposal({
                'proposal_id': proposal_id,
                'repo_id': self.repo_manager.get_repo_by_slug(f'{owner}/{repo}'),
                'branch': branch,
                'proposed_by': 'DevBot',
                'commit_message': f'Proposed patch for {file_path}',
                'patches': [patch_dict],
                'status': 'pending',
                'risk_class': patch_dict['risk_class'],
                'diff_summary': patch_dict['diff_summary']
            })

            return PatchProposalResponse(patches=[PatchASTProposal(**patch_dict)])

        except Exception as e:
            print(f'[ERROR] propose_patch failed: {str(e)}')
            raise
