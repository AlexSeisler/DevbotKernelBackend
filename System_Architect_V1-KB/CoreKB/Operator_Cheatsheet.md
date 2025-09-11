# System Architect V1 — Operator Cheatsheet (v1.1)

Use these prompts verbatim to run the 5 phases with minimal back-and-forth.  
Rules baked in: **P1 is product scope only** · **CVL gate each phase** · **routing discipline**.

---

## 0) Kickoff (no repo)

**Prompt**  
> You are System Architect V1 (v1.1). Run **P1 only (product scope)**. Tools/stacks are **prohibited** in P1. Collect the **P1 Scope Form** and block until **assumptions == []**.  
> Goal: {{plain goal}}. Constraints: {{timeline, budget, sensitivity}}. **No repo** (greenfield).  
> Return `alignment_report` with `ready_to_plan=true` when complete.

**Kickoff (with repo)**  
> Same as above, but `repo_id={{Owner/Repo}}` `branch={{main}}`. Refresh if needed, then use `node-summary` and scoped `nodes` only for subsystem confirmation. **Still product scope only**.

---

## 1) P1 Nudge (if Architect drifts into tools)

**Prompt**  
> **P1 guardrail:** product scope only. Defer all stack/tool choices to **P2**.  
> Ask only for missing P1 Scope Form fields (**primary_users**, **core_jobs**, **one_sentence_value**, **north_star_metric**, **MVP single flow**).  
> Re-issue the `alignment_report` when **assumptions == []**.

---

## 2) Move to P2 — Infra + System Planning

**Prompt**  
> Proceed to **P2**. Create a `milestone_plan` per subsystem for level **{{L3/L4}}**.  
> Include the **L3 baselines**: `product_analytics`, `resume_normalization_gate` (blocking for uploads), `idempotency_keys`, `app_state_machine`, `db_backup_plan`, `source_adapters`.  
> Mark `security_review_required=true` for **auth, uploads, data_access/write (incl. idempotency), payments/webhooks/admin**.  
> Tag L4 scaffolds as `level_scaffold:true`.  
> Output only **`milestone_plan[]`**.

---

## 3) P3 — Build the DAG with required edges

**Prompt**  
> Build the **execution_timeline** DAG. Include **phase_label** on each node; **propagate security_flags**.  
> Enforce edges:  
> - `product_analytics → observability`  
> - `db_backup_plan → observability` **and** `infra`  
> - `app_state_machine → api_gateway` **and** `frontend_ui`  
> - `ms-ui-e2e` depends on `gateway_validation`, `db_schema`, `storage_uploads`, `vector_pipeline`, `ai_matching`  
> If any missing, return **FR:SUBSYSTEM.COVERAGE** with evidence.

---

## 4) P4 — Emit tasks + routing discipline

**Prompt**  
> Decompose into **atomic tasks**.  
> - **DevBot** ≤2 files with **1–3 `context_files`**  
> - **AI IDE** ≥3 files with `deliverable:"branch+diff+summary"`  
> - **SecurityOpsArchitect** = **review tickets** under `docs/security/*.md`  
> Use task schema:  
> `{ project_name, repo_id, phase_label, milestone_id, subsystem[], file_path, context_files[], description, priority, dependencies[], security_flags{} , status:"queued" }`  
> Include **routing_log** with `reason_code` (`files<=2|pattern_refactor|blocking_security|correctness.idempotency_required|legal_review_required|user_override`).  
> Output the exact JSON payload(s) for **POST /task-queue/insert**.

---

## 5) P5 — Monitoring + Adaptation (V1)

**Prompt**  
> Generate a **status_report** with `progress {completed,in_progress,blocked}`, `risks`, and `next_actions`.  
> If a task is rejected for deterministic reasons (missing dep/stale file), **auto-replan once** and note it; otherwise **ask me**.  
> Offer a **repo refresh plan** if drift suspected.

---

## 🔧 Execution Process: Phase 0 → L3 MVP (drop-in pack)

Use this section when starting from a fresh repo or converting an internal service into a user-facing MVP console. Paste the blocks into the Architect when prompted.

### Phase 0 (Bootstrap) — milestones
```json
[
  {"id":"ms-repo-scaffold","title":"Repo scaffold + CI","description":"Init monorepo roots (apps/frontend, services/api); GitHub Actions CI; .env templates.","phase_label":"0.1","blocking":true,"subsystem":["infra"]},
  {"id":"ms-api-shell","title":"FastAPI shell","description":"Health endpoint, JWT middleware, error envelope, trace_id logging.","phase_label":"0.2","blocking":true,"subsystem":["api_gateway","observability"]},
  {"id":"ms-auth-shell","title":"Auth + RBAC skeleton","description":"Supabase/Clerk login, roles (owner, member), guarded routes.","phase_label":"0.3","blocking":true,"subsystem":["auth","api_gateway"]},
  {"id":"ms-db-migrations","title":"DB init + migrations","description":"users, orgs, memberships, repos, plans, milestones, tasks, events.","phase_label":"0.4","blocking":true,"subsystem":["database"]},
  {"id":"ms-frontend-shell","title":"Next.js console","description":"Routes: /dashboard, /repos, /plans, /tasks, /security, /settings; org switch + guards.","phase_label":"0.5","blocking":false,"subsystem":["frontend_ui"]},
  {"id":"ms-kernel-integration","title":"Kernel API wiring","description":"Proxy + client for import_repo, node_summary, nodes, task_queue.insert.","phase_label":"0.6","blocking":false,"subsystem":["api_gateway","infra"]},
  {"id":"ms-obs-baseline","title":"Observability baseline","description":"JSON logs, trace_id propagation, product events emitter, dashboard NS metric stub.","phase_label":"0.7","blocking":false,"subsystem":["observability"]}
]
L3 MVP slice — must-have milestones
json
Copy
Edit
[
  {"id":"ms-auth-guards","title":"RBAC matrix + guards","description":"Enforce role checks on protected routes.","phase_label":"3.1","blocking":true,"subsystem":["auth","api_gateway"],"security_flags":{"security_review_required":true}},
  {"id":"ms-gateway-validation","title":"Schema validation","description":"Request/response schemas for repo import, planning, task emission.","phase_label":"3.1","blocking":true,"subsystem":["api_gateway"],"security_flags":{"security_review_required":true}},
  {"id":"ms-idempotency-keys","title":"Idempotency on writes","description":"Keys for task emission and imports; reject duplicates.","phase_label":"3.2","blocking":false,"subsystem":["api_gateway"]},
  {"id":"ms-db-schema","title":"MVP schema","description":"Finalize tables + indexes for plans/milestones/tasks/events.","phase_label":"3.1","blocking":true,"subsystem":["database"],"security_flags":{"security_review_required":true}},
  {"id":"ms-ui-e2e","title":"E2E console flow","description":"Run P1→P3, view DAG, emit tasks, see routing logs.","phase_label":"3.3","blocking":false,"subsystem":["frontend_ui"]},
  {"id":"ms-product-analytics","title":"KPI events","description":"Events: plan_generated, task_emitted(route), task_done/rejected; NS metric card.","phase_label":"3.3","blocking":false,"subsystem":["observability"]},
  {"id":"ms-infra-health","title":"Health + graceful shutdown","description":"/health/ping, worker shutdown hooks.","phase_label":"3.3","blocking":false,"subsystem":["infra"]}
]
P4 task template (fill per milestone)
json
Copy
Edit
{
  "project_name":"DevBot Console",
  "repo_id":"<owner/repo>",
  "phase_label":"3.1",
  "milestone_id":"ms-gateway-validation",
  "subsystem":["api_gateway"],
  "route":"devbot",
  "priority":1,
  "file_path":"services/api/app/validation.py",
  "context_files":["services/api/app/main.py"],
  "description":"Add Pydantic schemas + validation for POST /repo-ingestion/import-repo and /task-queue/insert.",
  "dependencies":[],
  "security_flags":{"security_review_required":true},
  "status":"queued"
}
Routing rules (apply when emitting)
DevBot: ≤2 files or targeted patch

AI IDE: ≥3 files / scaffolds / pattern refactors (add "deliverable":"branch+diff+summary")

Security: review tickets only (docs path), not implementation

P6 monitors (drop-in defaults)
json
Copy
Edit
{
  "heartbeat":{"source":"task_queue","field":"updated_at","stale_after_minutes":15},
  "polling":{"cadence_minutes":10},
  "triggers":[
    {"type":"task_stale","age_minutes":60,"action":"replan_or_escalate"},
    {"type":"failure_rate","pct":20,"window":"1h","action":"open_investigation_task"},
    {"type":"cost_spike","pct_over_baseline":30,"window":"24h","action":"throttle_noncritical"}
  ]
}
Quick Corrections (micro-prompts)
Tech drift in P1
“Defer tools/stacks to P2. Re-ask only for missing P1 Scope Form fields.”

Security tickets mis-routed
“Implementation → DevBot/AI IDE; reviews only → SecurityOpsArchitect. Re-route and re-emit.”

Missing baselines (P2)
“Add: product_analytics, resume_normalization_gate, idempotency_keys, app_state_machine, db_backup_plan, source_adapters.”

UI missing deps (P3)
“Make ms-ui-e2e depend on gateway_validation, db_schema, storage_uploads, vector_pipeline, ai_matching.”

Idempotency not flagged
“Set security_review_required:true on write-path idempotency milestones.”

Output Checks (per phase)
P1: Scope Form filled; assumptions==[]; north_star_metric present; MVP single flow present.

P2: Baselines present; security flags on risky areas; L4 scaffolds tagged.

P3: phase_label on nodes; required edges present; no cycles.

P4: Every task has file_path (or target dir for AI IDE), context_files (DevBot), routing_log, status:"queued".

P5: Clear risks + next_actions; auto-replan count ≤1 per rejection.

Tip: Store this as OPERATOR_PLAYBOOK.md. Update in lockstep with KB version bumps (v1.1 → v1.2).