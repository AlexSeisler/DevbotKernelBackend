# Core Zip → Node logic will be migrated here from FederationService

import os
import tempfile
from fastapi import HTTPException
from models.federation_schemas import ImportRepoRequest
from models.semantic_nodes import SemanticManager
from services.semantic_parser import SemanticParser
from services.repo_manager import RepoManager
from services.graph_manager import FederationGraphManager
from services.github_service import GitHubService
from repo_importer.tagging_hook import tag_semantic_node


def import_repo(payload: ImportRepoRequest):
    repo_id = payload.repo_id
    github_service = GitHubService()
    repo_manager = RepoManager()
    semantic_manager = SemanticManager()
    graph_manager = FederationGraphManager()
    parser = SemanticParser()

    try:
        zip_path = github_service.fetch_github_repo(payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch repo: {str(e)}")

    with tempfile.TemporaryDirectory() as temp_dir:
        os.system(f"unzip -q {zip_path} -d {temp_dir}")
        all_nodes = []
        failed_files = []
        files_scanned = 0

        for root, _, files in os.walk(temp_dir):
            for file in files:
                if not file.endswith((".py", ".ts", ".js", ".rs")):
                    continue

                full_path = os.path.join(root, file)
                files_scanned += 1

                try:
                    nodes = parser.extract_semantic_nodes(full_path, repo_id)
                    for node in nodes:
                        tag_semantic_node(node)
                    all_nodes.extend(nodes)
                except Exception:
                    failed_files.append(full_path)

        semantic_manager.bulk_save_semantic_nodes(all_nodes)

    return {
        "status": "ok",
        "repo_id": repo_id,
        "files_scanned": files_scanned,
        "semantic_nodes_extracted": len(all_nodes),
        "failed": failed_files
    }
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