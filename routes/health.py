from fastapi import APIRouter
import os

router = APIRouter(prefix="/health")

# ✅ Health Check (used by Render, GPT connector, uptime monitors)
@router.get("/ping")
async def health_check():
    return {
        "kernel_status": "online",
        "github_owner": os.getenv("GITHUB_OWNER"),
        "repo_target": os.getenv("GITHUB_REPO"),
        "version": "3.0.0"
    }
