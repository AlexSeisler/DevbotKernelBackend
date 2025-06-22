
CREATE TABLE federation_repo (
    id SERIAL PRIMARY KEY,
    repo_id TEXT UNIQUE,
    branch TEXT,
    root_sha TEXT,
    ingestion_date TIMESTAMP DEFAULT NOW(),
    owner TEXT,
    name TEXT,
    repo TEXT
);

CREATE TABLE IF NOT EXISTS semantic_node (
    id SERIAL PRIMARY KEY,
    repo_id INTEGER REFERENCES federation_repo(id),  -- Changed to INTEGER for foreign key reference
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
    repo_id INTEGER REFERENCES federation_repo(id),
    branch TEXT NOT NULL,
    proposed_by TEXT NOT NULL,
    commit_message TEXT NOT NULL,
    patches JSONB NOT NULL,
    status TEXT DEFAULT 'pending',
    risk_class TEXT NOT NULL,
    diff_summary TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);


CREATE TABLE IF NOT EXISTS federation_graph (
    id SERIAL PRIMARY KEY,
    repo_id INTEGER REFERENCES federation_repo(id),  -- Changed to INTEGER for foreign key reference
    file_path TEXT,
    node_type TEXT, 
    name TEXT,
    cross_linked_to TEXT,
    federation_weight FLOAT DEFAULT 1.0,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
