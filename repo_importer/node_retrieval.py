from services.db.query_executor import execute_query
from settings import _db_instance

db = _db_instance

def _resolve_uuid(repo_id: str) -> str:
    filters = {"logical_repo_id": repo_id}
    results = execute_query(db, "federation_repo", filters)
    if not results:
        raise ValueError(f"No repo found for logical_repo_id={repo_id}")
    return results[0]["id"]  # Correct field

def fetch_nodes_by_subsystem(repo_id: str, subsystem: str = None, columns: list = None):
    uuid = _resolve_uuid(repo_id)
    filters = {"repo_id": uuid}
    if subsystem:
        filters["subsystem"] = [subsystem]
    return execute_query(db, "semantic_node", filters, limit=10000, columns=columns)

def generate_node_summary(repo_id: str):
    uuid = _resolve_uuid(repo_id)
    filters = {"repo_id": uuid}
    rows = execute_query(db, "semantic_node", filters, limit=10000)

    total_nodes = len(rows)
    subsystems = set()
    tagged_nodes = 0

    for row in rows:
        if row.get("subsystem"):
            tagged_nodes += 1
            subsystems.update(row["subsystem"])

    tag_coverage = round((tagged_nodes / total_nodes) * 100, 2) if total_nodes else 0.0

    return {
        "total_nodes": total_nodes,
        "tag_coverage": tag_coverage,
        "subsystems_detected": sorted(subsystems)
    }