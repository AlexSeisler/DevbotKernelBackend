from fastapi import APIRouter, HTTPException
from services.orchestrator.orchestration_pipeline import OrchestrationPipeline

router = APIRouter(prefix="/orchestrate")
pipeline = OrchestrationPipeline()

@router.post("/replicate-saas")
async def replicate_saas(payload: dict):
    try:
        source_repo = payload["source_repo"]
        target_repo = payload["target_repo"]
        result = pipeline.run_full_replication(source_repo, target_repo)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
