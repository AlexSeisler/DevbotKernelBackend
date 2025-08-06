# Wrapper to integrate subsystem_tagging during ingestion

def tag_semantic_node(node):
    node['subsystem'] = infer_subsystem(node)
    return node


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

def tag_semantic_node(node):
    # Placeholder for tagging logic
    return node