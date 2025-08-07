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
    },
    "decorators": {
        "api": ["@app.get", "@app.post", "@router.get", "@router.post", "@route"],
        "task": ["@app.task", "@celery.task", "@shared_task"],
        "auth": ["@auth_required", "@login_required", "@jwt_required"],
    },
    "content": {
        "training": ["model.fit(", "trainer.train(", "pipeline("],
        "tools": ["function_call", "tool_response"],
        "analytics": ["track_event(", "log_usage(", "capture_metric"],
        "memory": ["embed_text(", "similarity_search(", "vectorstore"],
        "storage": ["upload_file(", "save_to_bucket(", "store_file("],
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

    def infer_subsystem(self, file_path, imports, decorators, content_lines):
        subsystems = defaultdict(float)
        file = file_path.split("/")[-1]

        subsystems.update(self._score_path(file_path))
        subsystems.update(self._score_filename(file))
        subsystems.update(self._score_imports(imports))
        subsystems.update(self._score_decorators(decorators))
        subsystems.update(self._score_inline_content(content_lines))

        if not subsystems:
            return ["core"]

        return [k for k, v in subsystems.items() if v >= 1.0] or ["core"]

    def _score_path(self, path):
        scores = defaultdict(float)
        path_map = {
            'auth': 1.0,
            'queue': 1.0,
            'task': 1.0,
            'orchestrator': 1.0,
            'training': 1.0,
            'replicator': 1.0,
        }
        for key, weight in path_map.items():
            if key in path:
                scores[key] += weight
        return scores

    def _score_filename(self, file):
        scores = defaultdict(float)
        if file.endswith('_auth.py'):
            scores['auth'] += 0.9
        if file.endswith('_worker.py'):
            scores['task'] += 0.9
        if file.endswith('_queue.py'):
            scores['queue'] += 0.9
        return scores

    def _score_imports(self, imports):
        scores = defaultdict(float)
        import_map = {
            'jwt': 'auth', 'authlib': 'auth', 'bcrypt': 'auth',
            'celery': 'queue', 'kombu': 'queue',
            'sqlalchemy': 'db', 'orm': 'db',
            'torch': 'training', 'tensorflow': 'training',
        }
        for i in imports:
            for key, subsystem in import_map.items():
                if key in i:
                    scores[subsystem] += 0.7
        return scores

    def _score_decorators(self, decorators):
        scores = defaultdict(float)
        for d in decorators:
            if any(k in d for k in ("route", "get", "post")):
                scores['http'] += 0.6
            if "task" in d:
                scores['queue'] += 0.6
        return scores

    def _score_inline_content(self, lines):
        scores = defaultdict(float)
        signals = {
            'model.fit': 'training',
            'db.session': 'db',
            'queue.enqueue': 'queue',
        }
        for line in lines:
            for key, subsystem in signals.items():
                if key in line:
                    scores[subsystem] += 0.5
        return scores
