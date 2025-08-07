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