from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv


# ✅ Import ALL existing route files
from routes import github, patch, pull_request, health, federation, replication, orchestration
from services.federation_service import FederationService

# ✅ Load .env credentials
load_dotenv()

# ✅ Initialize FastAPI app
app = FastAPI(
    title="DevBot Kernel API",
    version="4.0.0",
    description="ACS DevBot Federation Kernel — Full SaaS Federation Engine"
)

# ✅ Inject federation service for route dependencies
app.federation_service = FederationService()

# ✅ CORS for GPT connector compatibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Global Exception Handler (safe GPT schemas)
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"error": str(exc), "detail": "Internal Kernel Failure"}
    )

# ✅ Request Logger for audit tracking
@app.middleware("http")
async def request_logger(request: Request, call_next):
    response = await call_next(request)
    print(f"{request.method} {request.url} -> {response.status_code}")
    return response

# ✅ ROUTER MOUNT POINTS — FULL SYSTEM
app.include_router(health.router)
app.include_router(github.router)
app.include_router(patch.router)
app.include_router(pull_request.router)
app.include_router(federation.router)
app.include_router(replication.router)
app.include_router(orchestration.router)
