# Wrapper to integrate subsystem_tagging during ingestion


def infer_subsystem(node):
    path = node.get('file_path', '')
    if 'auth' in path:
        return 'auth'
    elif 'queue' in path:
        return 'queue'
    elif 'worker' in path or 'celery' in path:
        return 'task'
    else:
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
