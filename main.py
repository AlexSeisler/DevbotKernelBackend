from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

from routes import federation
from services.federation_service import FederationService

load_dotenv()

app = FastAPI(title="DevBot Kernel API", version="3.0.0", description="ACS Federation Kernel")

app.federation_service = FederationService()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"error": str(exc), "detail": "Internal Kernel Failure"})

@app.middleware("http")
async def request_logger(request: Request, call_next):
    response = await call_next(request)
    print(f"{request.method} {request.url} -> {response.status_code}")
    return response

app.include_router(federation.router)
