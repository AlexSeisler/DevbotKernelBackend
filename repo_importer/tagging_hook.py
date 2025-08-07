from collections import defaultdict
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


class TaggingHook:

    def _tag_semantic_node(self, node):
        tags = []

        name = node.get("name", "")
        node_type = node.get("node_type", "")
        decorators = node.get("decorators", [])
        file_path = node.get("file_path", "")

        if "test" in file_path:
            tags.append("test")
        if "infra" in file_path or "ops" in file_path:
            tags.append("infra")
        if node_type == "decorator":
            tags.append("decorator")
        if name in {"main", "__init__", "run"}:
            tags.append("entrypoint")
        if name.startswith("_"):
            tags.append("internal")
        if any(k in d for d in decorators for k in ("get", "post", "route")):
            tags.append("http")
        if not tags:
            tags.append("util")

        node["tags"] = tags
        return node

    def _tag_all_semantic_nodes(self, nodes):
        # Group nodes by file
        file_groups = defaultdict(list)
        for node in nodes:
            file_groups[node["file_path"]].append(node)

        for file_path, group in file_groups.items():
            imports = set()
            decorators = set()
            lines = []
            for node in group:
                imports.update(node.get("imports", []))
                decorators.update(node.get("decorators", []))
                lines.extend(node.get("source_code", "").splitlines())

            subsystems = self.infer_subsystem(file_path, list(imports), list(decorators), lines)
            for node in group:
                node["subsystem"] = subsystems
                self._tag_semantic_node(node)

        return nodes
    def _normalize_subsystems(self, scores):
        # Filter subsystems with confidence above threshold
        threshold = 1.0
        selected = [k for k, v in scores.items() if v >= threshold]
        
        # Fallback: choose highest-scoring subsystem(s)
        if not selected and scores:
            max_score = max(scores.values())
            selected = [k for k, v in scores.items() if v == max_score]

        return selected

    def infer_subsystem(self, file_path, imports, decorators, content_lines):
        from collections import defaultdict

        subsystems = defaultdict(float)
        file = file_path.split("/")[-1]

        subsystems.update(self._score_path(file_path))
        subsystems.update(self._score_filename(file))
        subsystems.update(self._score_imports(imports))
        subsystems.update(self._score_decorators(decorators))
        subsystems.update(self._score_inline_content(content_lines))

        if not subsystems:
            return ["core"]

        normalized = self._normalize_subsystems(subsystems)
        return normalized or ["core"]

    def _score_path(self, path):
        from collections import defaultdict
        scores = defaultdict(float)

        normalized_path = path.lower()

        for subsystem, patterns in subsystem_map.get("paths", {}).items():
            for pattern in patterns:
                if pattern in normalized_path:
                    scores[subsystem] += 1.0  # Full weight for path match
        return scores


    def _score_filename(self, file):
        from collections import defaultdict
        scores = defaultdict(float)

        normalized_filename = file.lower()

        for subsystem, keywords in subsystem_map.get("filenames", {}).items():
            for keyword in keywords:
                if keyword in normalized_filename:
                    scores[subsystem] += 0.9  # Strong filename match
        return scores


    def _score_imports(self, imports):
        from collections import defaultdict
        scores = defaultdict(float)

        for imp in imports:
            normalized_imp = imp.lower()
            for subsystem, keywords in subsystem_map.get("imports", {}).items():
                for keyword in keywords:
                    if keyword.lower() in normalized_imp:
                        scores[subsystem] += 1.0  # Full hit for confidence
        return scores


    def _score_decorators(self, decorators):
        from collections import defaultdict
        scores = defaultdict(float)

        for d in decorators:
            for subsystem, patterns in subsystem_map.get("decorators", {}).items():
                for pattern in patterns:
                    if pattern in d:
                        scores[subsystem] += 0.6
        return scores

    def _score_inline_content(self, lines):
        from collections import defaultdict
        scores = defaultdict(float)

        for line in lines:
            normalized_line = line.lower()
            for subsystem, patterns in subsystem_map.get("content", {}).items():
                for pattern in patterns:
                    if pattern.lower() in normalized_line:
                        scores[subsystem] += 0.5  # Medium weight for inline signals
        return scores
