from fastapi import APIRouter, Request
import os

router = APIRouter(prefix="/health")

@router.get("/ping")
async def health_check(request: Request):
    return {
        "kernel_status": "online",
        "github_owner": os.getenv("GITHUB_OWNER"),
        "repo_target": os.getenv("GITHUB_REPO"),
        "version": request.app.version  # ✅ dynamic from main.py
    }
