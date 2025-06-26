import os, tempfile, zipfile, uuid
from fastapi import APIRouter, UploadFile, File, HTTPException
from services.semantic_parser import SemanticParser
from services.federation_graph_manager import FederationGraphManager

router = APIRouter()
parser = SemanticParser()
manager = FederationGraphManager()

@router.post("/zip-ingest")
async def ingest_zip(file: UploadFile = File(...)):
    if not file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="Only .zip files are supported.")

    repo_id = f"zip-{uuid.uuid4()}"
    extracted_files = []

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = os.path.join(tmpdir, file.filename)
            with open(zip_path, "wb") as f:
                f.write(await file.read())

            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(tmpdir)

            for root, _, files in os.walk(tmpdir):
                for fname in files:
                    if fname.endswith(".py"):
                        full_path = os.path.join(root, fname)
                        with open(full_path, "r", encoding="utf-8") as f:
                            content = f.read()
                        relative_path = os.path.relpath(full_path, tmpdir)
                        nodes = parser.parse_python_file(content, file_path=relative_path)
                        for node in nodes:
                            manager.save_semantic_node(repo_id, node)
                            extracted_files.append(relative_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Zip ingestion failed: {str(e)}")

    return {
        "repo_id": repo_id,
        "files_parsed": list(set(extracted_files)),
        "status": "ingestion_complete"
    }
