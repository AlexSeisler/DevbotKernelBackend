import os, tempfile, zipfile, uuid, base64
from fastapi import APIRouter, UploadFile, File, HTTPException, Body
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
async def ingest_zip(
    file: UploadFile = File(None),
    git_payload: ZipIngestGitRequest = Body(None)
):
    extracted_files = []
    repo_id = f"zip-{uuid.uuid4()}"

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            if file:
                if not file.filename.endswith(".zip"):
                    raise HTTPException(status_code=400, detail="Only .zip files are supported.")
                zip_path = os.path.join(tmpdir, file.filename)
                with open(zip_path, "wb") as f:
                    f.write(await file.read())
                with zipfile.ZipFile(zip_path, "r") as zip_ref:
                    zip_ref.extractall(tmpdir)
                print("[ZIP-INGEST] Uploaded zip extracted.")

            elif git_payload:
                print(f"[ZIP-INGEST] GitHub ingest: {git_payload.owner}/{git_payload.repo}@{git_payload.branch}")
                repo_id = git_payload.repo_id
                tree = github.get_repo_tree(
                    git_payload.owner,
                    git_payload.repo,
                    git_payload.branch,
                    recursive=True
                ).get("tree", [])

                print(f"[ZIP-INGEST] Files in tree: {len(tree)}")

                for entry in tree:
                    if entry["path"].endswith(".py"):
                        print(f"[FETCHING] {entry['path']}")
                        try:
                            file_data = github.get_file(
                                git_payload.owner,
                                git_payload.repo,
                                entry["path"],
                                git_payload.branch
                            )
                            decoded = base64.b64decode(file_data["content"]).decode()
                            abs_path = os.path.join(tmpdir, entry["path"])
                            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
                            with open(abs_path, "w", encoding="utf-8") as f:
                                f.write(decoded)
                        except Exception as e:
                            print(f"[⚠ FETCH ERROR] {entry['path']}: {e}")
            else:
                raise HTTPException(status_code=400, detail="Must provide zip file or GitHub payload")

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
        print(f"[CRITICAL FAILURE] {e}")
        raise HTTPException(status_code=500, detail=f"Zip ingestion failed: {str(e)}")

    return {
        "repo_id": repo_id,
        "files_parsed": list(set(extracted_files)),
        "status": "ingestion_complete"
    }
