class TaggingHook():
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

        return [k for k, v in subsystems.items() if v >= 1.0] or ["core"]
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

        node['tags'] = tags
        node['subsystem'] = self.infer_subsystem(node)
        return node
        

    def _tag_all_semantic_nodes(self, nodes):
        for node in nodes:
            node['tags'] = self._tag_semantic_node(node)
        return nodes