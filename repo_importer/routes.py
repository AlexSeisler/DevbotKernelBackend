from fastapi import APIRouter, HTTPException
from models.federation_schemas import ImportRepoRequest
from repo_importer.importer import import_repo_logic

router = APIRouter(prefix='/federation')

@router.post('/import-repo')
async def import_repo(payload: ImportRepoRequest):
    try:
        return import_repo_logic(payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
