from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import os

from routes import github, patch, pull_request, health, federation
from services.federation_service import FederationService

# ✅ Load .env credentials safely
load_dotenv()

# ✅ Full Kernel Initialization
app = FastAPI(
    title="DevBot Kernel API",
    version="3.0.0",
    description="SaaS Kernel Backend — GPT-Agent Controlled GitHub Repo Manager"
)

# ✅ Inject Federation Service into app context (hot fix injection)
app.federation_service = FederationService()

# ✅ GPT Action Compatible CORS Layer
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Render + GPT connectors need permissive wildcard origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Global Exception Safety (prevents GPT schema breakage)
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"error": str(exc), "detail": "Internal Kernel Failure"}
    )

# ✅ Request/Response Logger (core Render kernel audit layer)
@app.middleware("http")
async def request_logger(request: Request, call_next):
    response = await call_next(request)
    print(f"{request.method} {request.url} -> {response.status_code}")
    return response

# ✅ Full Router Mount
app.include_router(health.router)
app.include_router(github.router)
app.include_router(patch.router)
app.include_router(pull_request.router)
app.include_router(federation.router)
