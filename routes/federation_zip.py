import os, tempfile, base64, uuid
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.semantic_parser import SemanticParser
from services.db.federation_graph_manager import FederationGraphManager
from services.github_service import GitHubService

router = APIRouter()
parser = SemanticParser()
manager = FederationGraphManager()
github = GitHubService()

class ZipIngestGitRequest(BaseModel):
    owner: str
    repo: str
    branch: str
    repo_id: int

@router.post("/zip-ingest")
async def ingest_zip(payload: ZipIngestGitRequest):
    print("[ZIP-INGEST] GitHub ingest route hit ✅")
    extracted_files = []
    repo_id = payload.repo_id

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            print(f"[ZIP-INGEST] Fetching tree for {payload.owner}/{payload.repo}@{payload.branch}")
            tree = github.get_repo_tree(payload.owner, payload.repo, payload.branch, recursive=True).get("tree", [])
            print(f"[ZIP-INGEST] Total files in tree: {len(tree)}")

            for entry in tree:
                if entry["path"].endswith(".py"):
                    print(f"[FETCHING] {entry['path']}")
                    try:
                        file_data = github.get_file(payload.owner, payload.repo, entry["path"], payload.branch)
                        decoded = base64.b64decode(file_data["content"]).decode()
                        abs_path = os.path.join(tmpdir, entry["path"])
                        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
                        with open(abs_path, "w", encoding="utf-8") as f:
                            f.write(decoded)
                    except Exception as e:
                        print(f"[⚠ FETCH ERROR] {entry['path']}: {e}")

            print("[ZIP-INGEST] Starting semantic parsing...")
            for root, _, files in os.walk(tmpdir):
                for fname in files:
                    if fname.endswith(".py"):
                        full_path = os.path.join(root, fname)
                        try:
                            with open(full_path, "r", encoding="utf-8") as f:
                                content = f.read()
                            rel_path = os.path.relpath(full_path, tmpdir)
                            print(f"[PARSING] {rel_path}")
                            nodes = parser.parse_python_file(content, file_path=rel_path)
                            for node in nodes:
                                manager.save_semantic_node(repo_id, node)
                            extracted_files.append(rel_path)
                        except Exception as e:
                            print(f"[⚠ PARSE ERROR] {fname}: {e}")

    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print(f"[CRITICAL FAILURE]\n{tb}")
        raise HTTPException(status_code=500, detail=f"Zip ingestion failed: {str(e)}")

    return {
        "repo_id": repo_id,
        "files_parsed": list(set(extracted_files)),
        "status": "ingestion_complete"
    }
