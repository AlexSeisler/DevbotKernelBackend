create table if not exists file_structure_cache (
  repo_id text not null,
  branch text not null,
  file_path text not null,
  sha text not null,
  anchor_path jsonb not null,
  anchor_name text not null,
  anchor_type text not null,
  start_line integer not null,
  end_line integer not null,
  created_at timestamptz default now()
);

create table if not exists patch_proposal (
  proposal_id uuid primary key,
  repo_id text not null,
  branch text not null,
  file_path text not null,
  base_sha text not null,
  anchor text not null,
  code_block text,
  patched_code text,
  diff text,
  metadata jsonb,
  proposed_by text not null default 'devbot',
  commit_message text not null default 'Federated patch proposal',
  anchor_lines integer[],
  anchor_path jsonb,
  patch_strategy text not null default 'insert',
  status text default 'pending',
  risk_class text default 'UNKNOWN',
  diff_summary text,
  created_at timestamptz default now()
);

create table if not exists semantic_node (
  repo_id text not null,
  file_path text not null,
  node_type text not null,
  name text not null,
  args jsonb,
  docstring text,
  methods jsonb,
  inherits_from text,
  return_type text,
  decorators jsonb,
  code_block text,
  interface_type text,
  tags text[],
  subsystem text[],  -- 🔧 NEW FIELD
  primary key (repo_id, file_path, name)
);

create table if not exists federation_graph (
  id serial primary key,
  repo_id text not null,
  file_path text not null,
  node_type text not null,
  name text not null,
  cross_linked_to text,
  federation_weight numeric,
  notes text,
  tags jsonb
);
CREATE TABLE if not exists federation_repo (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  repo_id TEXT NOT NULL UNIQUE,           -- ✅ Conflict key
  owner TEXT NOT NULL,
  repo TEXT NOT NULL,
  name TEXT NOT NULL,
  logical_repo_id TEXT NOT NULL,
  branch TEXT NOT NULL,
  root_sha TEXT NOT NULL,
  ingestion_date TIMESTAMPTZ DEFAULT now(),
  created_at TIMESTAMPTZ DEFAULT now()
);
create table if not exists positional_context (
  id uuid primary key default gen_random_uuid(),
  title text not null,
  summary text not null, -- Condensed insight for fast reference
  full_context jsonb not null, -- Full alignment block (question, analysis, conclusion, tags)
  linked_system text check (linked_system in ('DevBot', 'Architect', 'SMMAA', 'General')) not null,
  tags text[] default '{}',
  created_by text not null default 'CIAN',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  version text,
  visibility text check (visibility in ('global_read_only', 'internal', 'archived')) default 'global_read_only'
);
create table if not exists task_queue (
  id uuid primary key default gen_random_uuid(),
  title text not null,
  description text not null,
  assigned_to text check (assigned_to in ('Architect', 'DevBot', 'SMMAA')) not null,
  status text check (status in ('idea', 'active', 'in_progress', 'complete', 'rejected')) not null default 'idea',
  created_by text not null default 'CIAN',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  executed_by text,
  execution_summary text,
  linked_context_id uuid references positional_context(id) on delete set null,
  priority text check (priority in ('low', 'medium', 'high')) default 'medium',
  tags text[] default '{}'
);
create table if not exists agent_extended_memory (
  id uuid primary key default gen_random_uuid(),
  agent_name text not null,
  title text not null,
  content text not null,
  linked_milestone_id text,
  tags text[] default '{}',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
-- Create status enum
create type task_status as enum (
  'idea',
  'active',
  'in_progress',
  'blocked',
  'complete',
  'rejected'
);

-- Create task queue table
create table project_task_queue (
  id uuid primary key default gen_random_uuid(),
  project_name text not null,
  repo_id text not null,                                -- "Owner/Repo"
  phase text,                                           -- e.g. "3.1"
  subsystem text[],                                     -- ["auth","queue"]
  file_path text,                                       -- primary target file
  context_files text[] default '{}',                    -- optional extras
  description text not null,
  priority smallint default 2,                          -- 1=high 2=med 3=low
  status task_status default 'idea',
  dependencies uuid[] default '{}',                     -- other task ids
  security_flags jsonb default '{}'::jsonb,             -- scaffolding only
  created_by text,
  executed_by text,
  execution_summary text,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);
