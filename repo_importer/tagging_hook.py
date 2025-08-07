from collections import defaultdict

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
