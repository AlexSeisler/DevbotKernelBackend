"""
tag_rules.py — Subsystem tagging rules module

This module defines the `subsystem_map` used for tagging and classification
of semantic nodes during repository ingestion. It is extracted from the original
`tagging_hook.py` to allow for modular tuning and per-project overrides.

Future enhancements:
- Load rules dynamically from JSON/YAML
- Merge base rules with SaaS-specific rule sets at runtime
"""

subsystem_map = {
    "imports": {
        "auth": ["authlib", "jwt", "clerk", "supabase.auth", "firebase_admin.auth"],
        "queue": ["redis", "rq", "bullmq", "sidekiq"],
        "task": ["celery", "asyncio", "dramatiq", "taskiq"],
        "orchestration": ["langgraph", "crewai", "autogen"],
        "tools": ["openai", "anthropic", "serpapi", "cohere", "pydantic.v1", "function_schema"],
        "memory": ["pgvector", "chromadb", "weaviate", "qdrant", "supabase.vector"],
        "storage": ["boto3", "supabase.storage", "r2", "s3transfer"],
        "observability": ["sentry_sdk", "loguru", "prometheus_client", "opentelemetry"],
        "billing": ["stripe", "lemon", "paddle"],
        "rbac": ["fastapi_users", "casbin", "guardian"],
        "training": ["transformers", "trl", "peft", "lora", "openai.fine_tuning"],
        "infra": ["docker", "uvicorn", "gunicorn", "subprocess", "shutil"],
        "db": ["sqlalchemy", "psycopg", "alembic", "ormar"],
        "test": ["pytest", "mock", "unittest"],
        "analytics": ["posthog", "amplitude", "mixpanel"],
        "security": [
            "jwt", "authlib", "bcrypt", "secrets", "itsdangerous",
            "cryptography", "supabase.auth", "clerk", "fastapi.security", "oauthlib"
        ],
    },
    "filenames": {
        "auth": ["auth", "login", "signup", "session"],
        "queue": ["queue", "redis", "broker"],
        "task": ["task", "worker", "async"],
        "orchestration": ["orchestrator", "agent_graph", "dag"],
        "tools": ["tools", "functions", "toolset"],
        "memory": ["memory", "vector", "embed"],
        "storage": ["storage", "bucket", "uploader"],
        "observability": ["logger", "metrics", "telemetry"],
        "billing": ["billing", "payment", "stripe"],
        "rbac": ["roles", "permissions", "access"],
        "training": ["trainer", "finetune", "adapter"],
        "infra": ["docker", "deploy", "config"],
        "db": ["models", "schema", "migrations"],
        "test": ["test", "fixture", "mock"],
        "analytics": ["analytics", "telemetry"],
        "security": ["auth", "token", "rbac", "session", "login", "secure", "vault"],
    },
    "paths": {
        "auth": ["auth", "login", "signup"],
        "queue": ["queue"],
        "task": ["task", "worker"],
        "orchestration": ["orchestrator"],
        "tools": ["tools", "functions"],
        "memory": ["memory", "vector"],
        "storage": ["storage", "uploads"],
        "observability": ["logger", "monitor", "trace"],
        "billing": ["billing", "payment"],
        "rbac": ["roles", "access"],
        "training": ["training", "finetune"],
        "infra": ["ci", "deploy", "config", "infra"],
        "db": ["models", "db", "schema"],
        "test": ["tests", "fixtures"],
        "analytics": ["analytics"],
        "ux": ["pages", "dashboard", "ui"],
        "api": ["routes", "endpoints"],
        "security": ["auth", "security", "session", "token", "secrets", "rbac"],
    },
    "decorators": {
        "api": ["@app.get", "@app.post", "@router.get", "@router.post", "@route"],
        "task": ["@app.task", "@celery.task", "@shared_task"],
        "auth": ["@auth_required", "@login_required", "@jwt_required"],
        "security": ["requires_auth", "token_required", "authenticated"],
    },
    "content": {
        "training": ["model.fit(", "trainer.train(", "pipeline("],
        "tools": ["function_call", "tool_response"],
        "analytics": ["track_event(", "log_usage(", "capture_metric"],
        "memory": ["embed_text(", "similarity_search(", "vectorstore"],
        "storage": ["upload_file(", "save_to_bucket(", "store_file("],
        "security": [
            "Authorization", "Bearer", "Role", "AccessControl", "trace_id",
            "token", "TTL", ".env", "Vault", "authenticated"
        ],
    }
}

def get_subsystem_map():
    """
    Retrieve the current subsystem_map.
    Future versions may allow loading from DB or external config.
    """
    return subsystem_map