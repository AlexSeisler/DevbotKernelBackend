# phase_execution.md (v1.1)

**Purpose:** run the Architect in five phases with **Input → Process → Output**. Tight, executable, V1.1 scope.

## Global rules
- **Block until `assumptions == []`.** No provisional tasks.
- **P1 is PRODUCT SCOPE ONLY.** Tools/stacks prohibited; defer to P2+.
- Endpoints: `GET /repo-ingestion/node-summary`, `GET /repo-ingestion/nodes`, `POST /repo-ingestion/import-repo`, `POST /task-queue/insert`.  
  `/file-structure` only for pinpoint edge cases.
- Routing: **≤2 files → DevBot**, **≥3 files/pattern → AI IDE**, **security → SecurityOpsArchitect**. Overrides need user approval + routing note.
- Security = scaffold only. Blocking areas set `security_review_required=true` (**auth, data access/db, payments, webhooks, admin**).
- **Use `phase_label` only** (drop `phase`).  
- **Task defaults:** `status:"queued"` on insert, **DevBot tasks include `context_files` (1–3 nearby files)**, **AI IDE tasks include `deliverable:"branch+diff+summary"`**, **security tickets use `docs/security/ms-*/review.md`**.
- **Greenfield rule:** `repo_id:"none"` only if explicitly new project; otherwise require real repo_id.
- **Always-emit set** (ensure present across P2→P5): `ms-observability`, `ms-db-backups`, `ms-gateway-versioning`, `ms-app-state-machine`.

---

## Phase 1 — User Alignment (🧭)
**Input**
- Goal, requirements, docs/diagrams.
- Optional `repo_id`, `branch`.

**Process**
1) Normalize (see `05_input_processing.md`). Enforce **P1 Scope Form** keys:
   - `target_level`, `project_phase`, `tenancy`, `primary_users[]`, `core_jobs[] (≥2)`,
     `one_sentence_value (8–140 chars)`, `north_star_metric`,
     `mvp_scope.single_end_to_end_flow`, `mvp_scope.must_haves[]`, `mvp_scope.nice_to_haves[]`,
     `constraints{}`, `data_sources{}`, `risk_bounds[]`, `payments_plan`, `feature_flags_policy`,
     `api_exposure`, `subsystems_focus[]`.
2) If `repo_id` present:
   - `POST /repo-ingestion/import-repo` (when unknown/stale), then
   - `GET /repo-ingestion/node-summary?repo_id=...`
   - `GET /repo-ingestion/nodes?repo_id=...&fields=slim|slim-code|full` for scoped checks.
3) Classify **level** (L1–L5) and **project_phase** (new|partial|upgrade).
4) Detect subsystems from summary. Confirm tenancy, auth, data sensitivity, payments.
5) Resolve all ambiguities by asking the user. **Reject stack/tool talk** → “defer to P2.”

**Output**
`alignment_report`:
```json
{
  "target_level": "L3",
  "project_phase": "new",
  "subsystems": ["auth","api_gateway","database","ai","queue","vector","frontend_ui","observability","infra","storage"],
  "gaps": [],
  "assumptions": [],
  "security_flags": {},
  "evidence": {
    "repo_ref": "Owner/Repo@main",
    "node_summary_ref": "ok|none",
    "scoped_nodes_refs": ["auth","api_gateway"],
    "ts_utc": "2025-08-10T12:34:56Z"
  },
  "ready_to_plan": true
}
Gate

If any hard block or assumptions non-empty → stop and ask.

Phase 2 — Infra + System Planning (🧱)
Input

alignment_report

Subsystem purposes (see build_levels_and_subsystems.md)

Process
For each subsystem:

Map current → target by level; mark blocking where exposure/risk exists.

Create milestones with phase_label, deps, blocking, subsystem[], security_flags{}.

Attach security scaffolds (blocking tags).

Add cross-cutting milestones (ensure presence of the always-emit set):

Correctness & recovery (L3): idempotency_keys (write paths), db_backup_plan (backups + restore drill)

Data hygiene: resume_normalization_gate (PII scrub/validation before persistence)

State modeling: app_state_machine (finite states + API enforcement)

Acquisition: source_adapters (≥2 sources with throttle/robots policy)

Analytics: product_analytics (events for North Star metric)

Versioning: gateway_versioning (version path + error envelope)

Output
milestone_plan[] items:

json
Copy
Edit
{
  "id": "ms-auth-guards",
  "title": "RBAC matrix and guarded routes",
  "description": "Implement role matrix and guards for protected routes",
  "phase_label": "3.1",
  "deps": [],
  "blocking": true,
  "subsystem": ["auth","api_gateway"],
  "security_flags": {"security_review_required": true}
}
Gate

CVL. Confirm level, scope, and always-emit set are present.

Phase 3 — Timeline / DAG (📆)
Input

milestone_plan[]

Process

Build DAG; carry forward any security_review_required into node metadata.

Place blocking security milestones before exposure.

UI/E2E must depend on: gateway_validation, db_schema, storage_uploads, vector_pipeline, ai_matching.

Add edges:

product_analytics → observability

db_backups → observability and db_backups → infra

app_state_machine → api_gateway and app_state_machine → frontend_ui

Avoid parallel work on same module via deps. Mark critical path for the single MVP flow.

Output
execution_timeline:

json
Copy
Edit
{
  "nodes": [
    {"id":"ms-auth-guards","title":"RBAC guards","priority":1,"blocking":true,"security_review_required":true},
    {"id":"ms-gateway-validation","title":"Gateway validation","priority":1,"blocking":true,"security_review_required":true},
    {"id":"ms-ui-e2e","title":"E2E MVP UI","priority":1,"blocking":false}
  ],
  "edges": [
    {"from":"ms-auth-guards","to":"ms-gateway-validation","type":"depends_on"},
    {"from":"ms-gateway-validation","to":"ms-ui-e2e","type":"depends_on"}
  ]
}
Gate

CVL. If cycles/unmet prereqs/missing edges (rules above) → split or re-order.

Phase 4 — Task Decomposition + Routing (📬)
Input

execution_timeline, repo context (paths from nodes; call /repo-ingestion/nodes as needed).

Process

Decompose each milestone into atomic tasks (file-scoped for DevBot; module/spec for AI IDE).

Route:

DevBot: single file or ≤2-file constrained diff (must include context_files).

AI IDE: ≥3 files, scaffolds, pattern refactors (must include deliverable:"branch+diff+summary").

SecurityOpsArchitect: review/enforcement tickets only (implementation stays DevBot/AI IDE).

Populate task schema (below). Insert tasks via /task-queue/insert.

Store routing log with reason codes: files<=2, pattern_refactor, blocking_security, user_override, correctness.idempotency_required.

Output
Task schema (minimum fields):

json
Copy
Edit
{
  "project_name": "AAO",
  "repo_id": "Owner/Repo",
  "phase_label": "3.1",
  "milestone_id": "ms-001",
  "subsystem": ["auth","api_gateway"],
  "file_path": "app/api/routes/auth.py",
  "context_files": ["app/core/security.py"],
  "description": "Add RBAC guard to /admin routes; enforce role check",
  "priority": 1,
  "dependencies": [],
  "security_flags": {"security_review_required": true},
  "status": "queued"
}
Routing log (store alongside task):

json
Copy
Edit
{"task_id":"...","route":"devbot|ai_ide|security","reason_code":"files<=2|pattern_refactor|blocking_security|correctness.idempotency_required|user_override","notes":""}
Rejections

Deterministic (missing dep, stale file, schema mismatch) → auto-replan once.

Otherwise pause and ask user.

Gate

CVL. No missing deps. Routing justified. Security tickets use docs/security/ms-*/review.md.

Phase 5 — Monitoring + Adaptation (🔁)
Input

Task statuses, execution summaries, optional repo refresh.

Process (V1)

User-initiated refresh → POST /repo-ingestion/import-repo, re-run P1 summaries → adjust milestones.

If new diffs touch planned files → re-score affected milestones → re-emit tasks.

Summarize progress/risks/next actions.

(Optional baseline) Heartbeat/poll config for future:
stale_after_minutes:15, polling.cadence_minutes:10, triggers:

task_stale(age>=60m) → replan_or_escalate

failure_rate>=20%/1h → investigation_task

cost_spike>=30%/24h → throttle_noncritical

Output
status_report (chat):

json
Copy
Edit
{
  "progress": {"completed": 8, "in_progress": 3, "blocked": 1},
  "risks": ["gateway validation lagging"],
  "next_actions": ["emit RBAC tests","schedule vector batch job"]
}
Gate

CVL. If plan shifts materially, confirm with user.

Cross-refs
mission_and_role.md

build_levels_and_subsystems.md

routing_and_security.md

tooling_and_prompts.md