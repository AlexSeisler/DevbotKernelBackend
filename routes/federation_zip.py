import os, tempfile, zipfile, uuid, requests
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.semantic_parser import SemanticParser
from services.db.semantic_manager import SemanticManager  # ✅ Corrected manager

router = APIRouter()
parser = SemanticParser()
manager = SemanticManager()  # ✅ Corrected instance

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

class ZipIngestGitRequest(BaseModel):
    owner: str
    repo: str
    branch: str
    repo_id: int

@router.post("/zip-ingest")
async def ingest_zip(payload: ZipIngestGitRequest):
    print("[ZIP-INGEST] GitHub zipball ingest route hit ✅")
    extracted_files = []
    repo_id = payload.repo_id

    try:
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "X-GitHub-Api-Version": "2022-11-28"
        }

        zip_url = f"https://api.github.com/repos/{payload.owner}/{payload.repo}/zipball/{payload.branch}"
        print(f"[ZIPBALL] Downloading: {zip_url}")

        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = os.path.join(tmpdir, f"{payload.repo}.zip")

            response = requests.get(zip_url, headers=headers, stream=True, allow_redirects=True)
            if response.status_code != 200:
                raise Exception(f"Zipball download failed: {response.status_code} — {response.text}")

            with open(zip_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            print(f"[ZIPBALL] Extracting zipball to temp dir...")
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(tmpdir)

            print("[SEMANTIC] Starting parsing of .py files")
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
                                manager.save_semantic_node(repo_id, node)  # ✅ Corrected usage
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
