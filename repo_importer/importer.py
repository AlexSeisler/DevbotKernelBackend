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


def import_repo_logic(payload):
    repo_id = payload.repo_id
    try:
        zip_path = fetch_github_repo(payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch repo: {str(e)}")

    with tempfile.TemporaryDirectory() as temp_dir:
        os.system(f"unzip -q {zip_path} -d {temp_dir}")
        all_nodes = []
        stats = {"files_scanned": 0, "nodes_extracted": 0, "tagged_files": 0, "failed": 0}

        for root, _, files in os.walk(temp_dir):
            for file in files:
                if not file.endswith((".py", ".ts", ".js", ".rs")):
                    continue

                full_path = os.path.join(root, file)
                stats["files_scanned"] += 1

                try:
                    nodes = extract_semantic_nodes(full_path, repo_id)
                    for node in nodes:
                        tag_semantic_node(node)
                    all_nodes.extend(nodes)
                    stats["nodes_extracted"] += len(nodes)
                    stats["tagged_files"] += 1
                except Exception:
                    stats["failed"] += 1

        insert_nodes(all_nodes)
        return emit_quality_report(stats)
from repo_importer.import_quality import emit_quality_report


def import_repo_logic(payload):
    repo_id = payload.repo_id
    try:
        zip_path = fetch_github_repo(payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch repo: {str(e)}")

    with tempfile.TemporaryDirectory() as temp_dir:
        os.system(f"unzip -q {zip_path} -d {temp_dir}")
        all_nodes = []
        stats = {"files_scanned": 0, "nodes_extracted": 0, "tagged_files": 0, "failed": 0}

        for root, _, files in os.walk(temp_dir):
            for file in files:
                if not file.endswith((".py", ".ts", ".js", ".rs")):
                    continue

                full_path = os.path.join(root, file)
                stats["files_scanned"] += 1

                try:
                    nodes = extract_semantic_nodes(full_path, repo_id)
                    for node in nodes:
                        tag_semantic_node(node)
                    all_nodes.extend(nodes)
                    stats["nodes_extracted"] += len(nodes)
                    stats["tagged_files"] += 1
                except Exception:
                    stats["failed"] += 1

        insert_nodes(all_nodes)
        return emit_quality_report(stats)
def import_repo_logic(payload):
    # Placeholder for migrated ingestion logic
    pass