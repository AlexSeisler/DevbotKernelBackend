from repo_importer import routes
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from dotenv import load_dotenv
import inspect

# 🚀 Trigger reload check comment
# If this line causes reload logs in Render, hot-reload is working

# 🧠 Import ALL existing route files
from routes import github, pull_request, health, federation, replication, orchestration, query, db_write
from services.federation_service import FederationService

# 🔐 Load .env credentials
load_dotenv()

# 🚀 Initialize FastAPI app
app = FastAPI(
    title="DevBot Kernel API",
    version="4.0.0",
    description="ACS DevBot Federation Kernel 🧠 Full SaaS Federation Engine"
)

# 🧠 Inject federation service for route dependencies
app.federation_service = FederationService()

# 🧠 CORS for GPT connector compatibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔧 Global Exception Handler (safe GPT schemas)
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"error": str(exc), "detail": "Internal Kernel Failure"}
    )

@app.on_event("startup")
async def print_routes():
    print("\n🚀 REGISTERED ROUTES:")

# 🔍 Request Logger for audit tracking
@app.middleware("http")
async def request_logger(request: Request, call_next):
    response = await call_next(request)
    print(f"{request.method} {request.url} --> {response.status_code}")
    return response

# 🔁 ROUTER MOUNT POINTS 🔐 FULL SYSTEM
app.include_router(health.router)
app.include_router(github.router)
app.include_router(pull_request.router)
app.include_router(federation.router)
app.include_router(replication.router)
app.include_router(orchestration.router)
app.include_router(query.router)
app.include_router(db_write.router)
app.include_router(routes.router)

# ✅ Add ai-plugin.json and OpenAPI serving routes
@app.get("/.well-known/ai-plugin.json", include_in_schema=False)
async def serve_manifest():
    return JSONResponse({
        "schema_version": "v1",
        "name_for_human": "DevBot Kernel API",
        "name_for_model": "devbot_kernel_api",
        "description_for_model": "Federation kernel interface for querying and patching SaaS module structure.",
        "auth": {"type": "none"},
        "api": {
            "type": "openapi",
            "url": "https://devbotkernelbackend-v1j2.onrender.com/openapi.yaml"
        },
        "contact_email": "alex@acsresultsai.net",
        "legal_info_url": "https://gist.github.com/AlexSeisler/0c5fcf534f39e40b1200887d55f0f7a3"
    })

@app.get("/openapi.yaml", include_in_schema=False)
async def get_openapi_yaml():
    return FileResponse("openapi.yaml")
    app.include_router(repo_importer_router)