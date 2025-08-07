class TaggingHook():
    def infer_subsystem(self, node):
        path = node.get('file_path', '')
        file = path.split('/')[-1]
        imports = node.get('imports', [])

        if 'auth' in path or 'user' in path:
            return 'auth'
        elif 'queue' in path or 'task_queue' in path:
            return 'queue'
        elif 'worker' in path or 'celery' in path:
            return 'task'
        elif 'replicator' in path:
            return 'replicator'
        elif 'training' in path:
            return 'training'
        elif 'orchestrator' in path:
            return 'orchestration'

        if file.endswith('_auth.py'):
            return 'auth'
        elif file.endswith('_worker.py'):
            return 'task'
        elif file.endswith('_queue.py'):
            return 'queue'

        if any("jwt" in i or "authlib" in i for i in imports):
            return 'auth'
        if any("celery" in i for i in imports):
            return 'task'
        if any("sqlalchemy" in i or "orm" in i for i in imports):
            return 'db'

        return 'core'

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

        return tags

    def _tag_all_semantic_nodes(self, nodes):
        for node in nodes:
            node['tags'] = self._tag_semantic_node(node)
        return nodes