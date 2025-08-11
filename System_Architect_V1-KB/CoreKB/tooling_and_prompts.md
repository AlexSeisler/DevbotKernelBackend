# tooling_and_prompts.md

Purpose: one-page defaults + minimal prompt patterns. V1 scope. Tight.

## Stack defaults per level

| Level | Runtime | DB / Vector | Queue | Gateway / UI | Observability | Billing |
|---|---|---|---|---|---|---|
| L1 | Python + FastAPI (local) | SQLite or local PG / none | none | local FastAPI / none | prints | none |
| L2 | FastAPI on PaaS | Supabase PG / optional pgvector trial | none | FastAPI / basic Next.js | JSON logs | none |
| L3 | FastAPI + LangGraph | Postgres + **pgvector** | **Celery + Redis** | FastAPI gateway + **Next.js** | logs + **trace_id** | none |
| L4 | FastAPI + LangGraph | Tuned PG + pgvector | Celery+Redis (DLQ/dedup) | FastAPI behind **Traefik** + RBAC + quotas | **Prometheus + Grafana + Sentry + OTel** | **Stripe** (metered) |
| L5 | Same + multi-region | Data lifecycle + exports | queue as above or Temporal | multi-region + rollout policies | + product analytics | plans + usage |

Notes
- Auth: Supabase/Clerk at L3, org RBAC + RLS at L4, SSO optional L4/L5.
- Frontend: Next.js + Tailwind.
- Secrets: env + 1Password/Vault/Supabase Secrets.
- CI/CD: GitHub Actions; migrations via Alembic; feature flags (OpenFeature) at L4+.
- LLM: OpenAI + Anthropic; embeddings **text-embedding-3-large**; swap allowed.

## API contracts (V1)
- Read: `GET /repo-ingestion/node-summary`, `GET /repo-ingestion/nodes?repo_id=...&fields=slim|slim-code|full`
- Refresh: `POST /repo-ingestion/import-repo`
- Write: `POST /task-queue/insert`
- `/file-structure`: edge only.

---

## Prompt patterns (copy-ready)

### 1) P1 Diagnostic intake (normalize + block until clear)
You are the System Architect V1. Normalize inputs and refuse to proceed until all assumptions are resolved.

Inputs:

goal: {{project_goal}}

constraints: {{constraints_text}}

repo_id: {{repo_id_or_none}}

docs/diagrams: {{artifacts_list}}

Tasks:

Produce canonical object fields: target_level (L1–L5), project_phase (new|partial|upgrade), tenancy, auth_model, data_sensitivity, payments, subsystems_focus.

Call out gaps as questions. Do not draft milestones if any gaps remain.

Output JSON:
{ "alignment_input": {...}, "gaps": [...], "assumptions": [], "ready_to_plan": {{true|false}} }

shell
Copy
Edit

### 2) P1 Repo sanity + subsystem confirmation
Given node summary and scoped nodes, confirm detected subsystems and block if core unknowns remain.

Inputs:

node_summary: {{summary_blob}}

scoped_nodes: {{scoped_list}}

required confirmations: tenancy, auth_model, target_level

Output:

subsystems: [...]

unresolved: [tenancy?|auth_model?|target_level?]

decision: "proceed" | "stop_for_clarification"

shell
Copy
Edit

### 3) P2 Current→Target mapping per subsystem
For each subsystem in {{subsystems_list}}, map current→target for level {{target_level}}.

Output (array of milestones):
[
{ "id":"ms-{{n}}", "title":"...", "description":"...", "phase_label":"3.{{n}}",
"deps":[], "blocking":{{true|false}},
"subsystem":["{{sub}}"], "security_flags":{} }
]
Rules:

Place blocking security scaffolds for auth, data access/db, payments, webhooks, admin.

Keep milestone text deterministic and file-agnostic (files come in P4).

shell
Copy
Edit

### 4) Routing decision (DevBot vs AI IDE vs SecurityOps)
Decide route for each task candidate.

Inputs:

milestone_id: {{id}}

estimated_files_touched: {{int}}

change_type: "scaffold"|"pattern_refactor"|"targeted_patch"

security_blocking: {{true|false}}

Policy:

≤2 files or targeted_patch → DevBot

≥3 files or scaffold/pattern_refactor → AI_IDE

security_blocking → SecurityOpsArchitect

Output:
{ "route":"devbot|ai_ide|security", "reason_code":"files<=2|pattern_refactor|blocking_security|user_override", "notes":"" }

shell
Copy
Edit

### 5) P4 Task emission template (atomic, file-scoped)
Emit atomic tasks for DevBot or high-level spec for AI IDE.

Common fields:
{
"project_name":"{{name}}",
"repo_id":"{{owner_repo}}",
"phase":"{{phase_label}}",
"milestone_id":"{{ms_id}}",
"subsystem":["{{sub}}"],
"file_path":"{{primary_file}}",
"context_files":[{{optional_files}}],
"description":"{{deterministic_goal}}",
"priority":{{1|2|3}},
"dependencies":[{{task_ids}}],
"security_flags":{{json}}
}

shell
Copy
Edit

### 6) Re-plan trigger (post-rejection or drift)
A task was rejected or the repo changed. Decide to auto-replan once or ask user.

Inputs:

rejection_reason or diff_summary
Decision rules:

Missing dependency or stale file → auto-replan once.

Ambiguous or conflicting ownership → stop and request user input.

Output:
{ "action":"auto_replan_once"|"ask_user", "next_steps":[...] }

shell
Copy
Edit

### 7) Security scaffold quick prompts (use sparingly)
Auth blocking check:
"List minimal security scaffolds before exposing public endpoints: RBAC guards, token verify, rate limits, audit points."

Payments/webhooks blocking check:
"Insert Stripe webhook signature verify + idempotency. Gate premium endpoints by quota. Add review milestone."

Admin console blocking check:
"Add admin-only route guards and audit logs. Confirm no privileged operations are exposed without RBAC."

markdown
Copy
Edit

---

## Minimal reference snippets

**LLM providers:** OpenAI + Anthropic. Swap allowed.  
**Embeddings:** `text-embedding-3-large`.  
**Queue:** Celery + Redis.  
**Vector:** pgvector by default.  
**Auth:** Supabase or Clerk; RLS at L4.  
**Observability:** JSON logs → Prometheus+Grafana+Sentry+OTel at L4.  
**Billing:** Stripe at L4+.  
**Feature flags:** OpenFeature (L4+).

Cross-refs: `mission_and_role.md`, `build_levels_and_subsystems.md`, `phase_execution.md`, `routing_and_security.md`.