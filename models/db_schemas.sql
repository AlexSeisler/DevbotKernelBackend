CREATE TABLE IF NOT EXISTS federation_repo (
    id SERIAL PRIMARY KEY,
    repo_id TEXT UNIQUE,
    branch TEXT,
    root_sha TEXT,
    ingestion_date TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS semantic_node (
    id SERIAL PRIMARY KEY,
    repo_id TEXT REFERENCES federation_repo(repo_id),
    file_path TEXT,
    node_type TEXT,
    name TEXT,
    args JSONB,
    docstring TEXT,
    methods JSONB,
    inherits_from TEXT,
    parsed_date TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS patch_proposal (
    proposal_id UUID PRIMARY KEY,
    repo_id TEXT REFERENCES federation_repo(repo_id),
    branch TEXT,
    proposed_by TEXT,
    commit_message TEXT,
    patches JSONB,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW()
);
