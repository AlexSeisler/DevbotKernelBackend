# tooling_and_prompts.md (v1.1)

Purpose: one-page defaults + copy-ready prompt patterns. V1 scope. Tight. Enforces P1 product-first, always-emit set at L3+, routing discipline, and security scaffolds.

---

## Stack defaults per level

| Level | Runtime | DB / Vector | Queue | Gateway / UI | Observability | Billing |
|---|---|---|---|---|---|---|
| L1 | Python + FastAPI (local) | SQLite / local PG | none | local FastAPI / none | prints | none |
| L2 | FastAPI on PaaS | Supabase PG / pgvector trial (opt) | none | FastAPI / basic Next.js | JSON logs | none |
| L3 | FastAPI + LangGraph | Postgres + **pgvector** | **Celery + Redis** | FastAPI gateway + **Next.js** | JSON logs + **trace_id** | none |
| L4 | FastAPI + LangGraph | Tuned PG + pgvector | Celery+Redis (DLQ/dedup) | FastAPI behind **Traefik**; RBAC+quotas | **Prometheus + Grafana + Sentry + OTel** | **Stripe** (metered) |
| L5 | Same + multi-region | Data lifecycle + exports | queue↑ / Temporal | multi-region + rollout policies | + product analytics | plans + usage |

Notes: Auth = Supabase/Clerk (L3), add **RLS** (L4, allowed as `level_scaffold:true` at L3). Secrets = env + 1Password/Vault/Supabase Secrets. CI/CD = GitHub Actions; Alembic. Feature flags (OpenFeature) at L4+. LLM = OpenAI + Anthropic; embeddings = **text-embedding-3-large**.

---

## API contracts (Architect V1)

- READ: `GET /repo-ingestion/node-summary`, `GET /repo-ingestion/nodes?repo_id=...&fields=slim|slim-code|all`
- REFRESH: `POST /repo-ingestion/import-repo`
- WRITE: `POST /task-queue/insert`
- EDGE: `/repo/file*` only for pinpoint context.

---

## Canonical fields & defaults (tasks)

- **Required**: `project_name, repo_id, phase_label, milestone_id, subsystem[], file_path, context_files[], description, priority(1|2|3), dependencies[], security_flags{}`
- **Routing log**: `{task_id, route:("devbot"|"ai_ide"|"security"), reason_code, notes}`
- **Status**: default insert as `queued` (state machine: `idea→queued→running→done|blocked`)
- **Greenfield**: `repo_id:"none"` allowed **only** if explicitly in greenfield mode
- **AI IDE deliverable**: always set `deliverable:"branch+diff+summary"`
- **Security ticket file_path**: use `docs/security/<ticket>.md`
- **DevBot context_files**: include 1–3 nearby files (models/routers) to reduce retries

Reason codes: `files<=2`, `pattern_refactor`, `blocking_security`, `user_override`, **`correctness.idempotency_required`**, **`legal_review_required`**.

---

## Prompt patterns (copy-ready)

### 1) P1 Scope Intake (product-only, hard gate)
You are System Architect V1. Collect PRODUCT SCOPE ONLY. Tools/stacks are prohibited in P1 (defer to P2).

Return alignment_input with:

target_level(L1–L5), project_phase(new|partial|upgrade), tenancy(single|multi)

primary_users[], core_jobs[] (≥2), one_sentence_value (8–140 chars), north_star_metric

success_criteria[], constraints{budget,timeline_weeks,compliance,data_sensitivity}

mvp_scope{single_end_to_end_flow, must_haves[], nice_to_haves[]}

data_sources{opportunity_feeds[], resume_storage, feedback_loop}

risk_bounds[], payments_plan, feature_flags_policy, api_exposure

subsystems_focus[]

Gate:

If any missing OR assumptions!=[], ask targeted questions; do NOT proceed.
Output:
{ "alignment_input": {...}, "gaps": [], "assumptions": [], "ready_to_plan": true }

shell
Copy
Edit

### 2) P1 Repo sanity (if repo_id provided)
Given node_summary + scoped nodes:

Confirm detected subsystems

Validate tenancy, auth_model, target_level consistency
Output: {subsystems:[...], unresolved:[...], decision:"proceed"|"stop_for_clarification"}

pgsql
Copy
Edit

### 3) P2 Current→Target mapping per subsystem (+ always-emit set)
For each subsystem in {{subsystems_list}} at level {{target_level}}:

Map current→target

Emit milestones: {id,title,description,phase_label,deps[],blocking,subsystem[],security_flags{}}

Always-emit at L3+: idempotency_keys (write paths), resume_normalization_gate, app_state_machine,
db_backups (daily+drill), source_adapters(≥2), product_analytics (NSM events), gateway_versioning.

Set security_review_required:true for auth, uploads, data_access/write, payments, webhooks, admin.
Mark non-blocking L4 scaffolds at L3 with level_scaffold:true.

shell
Copy
Edit

### 4) P2→P3 pre-DAG check (coverage gate)
Verify presence of: product_analytics, resume_normalization_gate, idempotency_keys, app_state_machine,
db_backups, source_adapters, gateway_versioning.
If any missing → return FR:SUBSYSTEM.COVERAGE with evidence; else proceed.

shell
Copy
Edit

### 5) P3 DAG builder (with phase & security propagation)
Rules:

No public UI before blocking gates (auth, validation, uploads, normalization, schema)

Avoid parallel work on same module

Mark critical path for MVP flow

Propagate security flags into nodes.
Add edges:

ui_e2e -> gateway_validation, db_schema, storage_uploads, vector_pipeline, ai_matching

product_analytics -> observability

db_backups -> observability AND db_backups -> infra

app_state_machine -> api_gateway AND -> frontend_ui

Output:
{ "nodes":[{id,title,priority,blocking,phase_label,security_flags{...}}], "edges":[{from,to,type}] }

shell
Copy
Edit

### 6) Routing decision (DevBot vs AI IDE vs SecurityOpsArchitect)
Inputs: milestone_id, estimated_files_touched, change_type("scaffold"|"pattern_refactor"|"targeted_patch"), security_blocking
Policy:

≤2 files or targeted_patch → "devbot"

≥3 files or scaffold/pattern_refactor → "ai_ide"

security_blocking → "security" (review tickets only; implementation goes to devbot/ai_ide)
Output: { route, reason_code, notes }

shell
Copy
Edit

### 7) P4 Task emission (atomic, file-scoped)
For each milestone:

DevBot: include concrete file_path and 1–3 context_files

AI IDE: set target_dir in file_path (e.g., "backend/vector/") + deliverable:"branch+diff+summary"

Security: emit review ticket to docs/security/*.md

Payload item:
{
"project_name":"{{name}}",
"repo_id":"{{owner_repo_or_none}}",
"phase_label":"{{3.x}}",
"milestone_id":"{{ms_id}}",
"subsystem":["{{sub}}"],
"file_path":"{{file_or_dir}}",
"context_files":[{{paths}}],
"description":"{{deterministic goal}}",
"priority":{{1|2|3}},
"dependencies":[{{task_ids}}],
"security_flags":{{json}},
"status":"queued",
"deliverable":"branch+diff+summary" // AI IDE only
}

shell
Copy
Edit

### 8) Re-plan trigger (post-rejection or drift)
Inputs: rejection_reason OR diff_summary
Rules:

Missing dependency or stale file → auto_replan_once

Ambiguous ownership or conflicting direction → ask_user

Output: { "action":"auto_replan_once"|"ask_user", "next_steps":[...] }

pgsql
Copy
Edit

### 9) Security scaffold quick prompts
- **Auth blocking check**: “List minimal security scaffolds before exposing public endpoints: RBAC guards, token verify, rate limits, audit points.”
- **Payments/webhooks check**: “Insert Stripe webhook signature verify + idempotency. Gate premium endpoints by quota. Add review milestone.”
- **Admin console check**: “Add admin-only route guards and audit logs. Confirm no privileged operations are exposed without RBAC.”

### 10) Legal/TOS guard (adapters/scrapers)
If any source is high-risk (e.g., ToS-restricted), set security_flags.legal_review_required:true
and prefer permissive alternatives. Use reason_code: "legal_review_required".

markdown
Copy
Edit

---

## Minimal reference snippets
- **LLM**: OpenAI + Anthropic (swap allowed)  
- **Embeddings**: `text-embedding-3-large`  
- **Queue**: Celery + Redis  
- **Vector**: pgvector (default)  
- **Auth**: Supabase/Clerk; add **RLS** at L4 (ok as `level_scaffold:true` at L3)  
- **Observability**: JSON logs → Prometheus+Grafana+Sentry+OTel (L4)  
- **Billing**: Stripe (L4+)  
- **Feature flags**: OpenFeature (L4+)

**Cross-refs**: `mission_and_role.md`, `build_levels_and_subsystems.md`, `phase_execution.md`, `routing_and_security.md`.
