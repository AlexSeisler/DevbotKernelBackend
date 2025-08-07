from services.db.query_executor import execute_query
from settings import _db_instance

db = _db_instance

def fetch_nodes_by_subsystem(repo_id: str, subsystem: str = None):
    filters = {"repo_id": repo_id}
    if subsystem:
        filters["subsystem"] = [subsystem]  # wrap in list for Postgres overlap
    return execute_query(db, "semantic_node", filters)

def generate_node_summary(repo_id: str):
    filters = {"repo_id": repo_id}
    rows = execute_query(db, "semantic_node", filters)

    total_nodes = len(rows)
    subsystems = set()
    tagged_nodes = 0
    file_node_map = {}

    for row in rows:
        if row.get("subsystem"):
            tagged_nodes += 1
            subsystems.update(row["subsystem"])
        fp = row["file_path"]
        file_node_map.setdefault(fp, []).append(row)

    orphan_files = [fp for fp, nodes in file_node_map.items() if all(not n.get("subsystem") for n in nodes)]
    tag_coverage = round((tagged_nodes / total_nodes) * 100, 2) if total_nodes else 0.0

    return {
        "total_nodes": total_nodes,
        "tag_coverage": tag_coverage,
        "subsystems_detected": sorted(subsystems),
        "orphan_files": orphan_files
    }