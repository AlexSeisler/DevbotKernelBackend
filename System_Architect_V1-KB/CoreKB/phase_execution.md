# phase_execution.md

Purpose: run the Architect in five phases with Input → Process → Output. Tight, executable, V1 scope.

## Global rules
- Block until assumptions == ∅. No provisional tasks.
- Endpoints: GET /repo-ingestion/node-summary, GET /repo-ingestion/nodes, POST /repo-ingestion/import-repo, POST /task-queue/insert. `/file-structure` only for pinpoint edge cases.
- Routing: ≤2 files → DevBot, ≥3 files/pattern → AI IDE. Overrides need user approval + routing note.
- Security = scaffold only. Blocking areas set `security_review_required=true` (auth, data access/db, payments, webhooks, admin).
- CVL at end of every phase.

---

## Phase 1 — User Alignment (🧭)
**Input**
- Goal, requirements, docs/diagrams.
- Optional `repo_id`, `branch`.

**Process**
1) Normalize (see 05_input_processing.md).
2) If `repo_id` present:
   - `POST /repo-ingestion/import-repo` (if refresh needed).
   - `GET /repo-ingestion/node-summary?repo_id=...`
   - `GET /repo-ingestion/nodes?repo_id=...&fields=slim|slim-code|full` for scoped checks.
3) Classify **level** (L1–L5) and **project_phase** (new|partial|upgrade).
4) Detect subsystems from summary. Confirm tenancy, auth, data sensitivity, payments.
5) Resolve all ambiguities by asking the user.

**Output**
`alignment_report`:
```json
{
  "target_level": "L3",
  "project_phase": "partial",
  "subsystems": ["auth","api_gateway","database","ai","queue","vector","frontend_ui","observability","infra"],
  "gaps": [],
  "assumptions": [],
  "security_flags": {},
  "evidence": {
    "repo_ref": "Owner/Repo@main",
    "node_summary_ref": "ok",
    "scoped_nodes_refs": ["auth","api_gateway"],
    "ts_utc": "2025-08-10T12:34:56Z"
  }
}
Gate

If any hard block or assumptions non-empty → stop and ask.

Phase 2 — Infra + System Planning (🧱)
Input

alignment_report

Subsystem purposes (see build_levels_and_subsystems.md).

Process

For each subsystem: map current → target by level.

Create milestones (create/upgrade). Add deps and labels.

Attach security scaffolds where required (blocking tags).

Add cross-cutting milestones (observability, rate limits, quotas/billing at L4+).

Output
milestone_plan[] items:

json
Copy
Edit
{
  "id": "ms-001",
  "title": "Add RBAC and route guards",
  "description": "Implement role matrix and guards for protected routes",
  "phase_label": "3.1",
  "deps": [],
  "blocking": true,
  "subsystem": ["auth","api_gateway"],
  "security_flags": {"security_review_required": true}
}
Gate

CVL. Confirm scope matches level and user constraints.

Phase 3 — Timeline / DAG (📆)
Input

milestone_plan[].

Process

Build DAG. Place blocking security milestones before exposure.

Assign priority (1 high, 2 med, 3 low). Avoid parallel work on same module via deps.

Confirm order does not deadlock.

Output
execution_timeline:

json
Copy
Edit
{
  "nodes": [
    {"id":"ms-001","title":"RBAC guards","priority":1,"blocking":true},
    {"id":"ms-002","title":"Gateway validation","priority":1,"blocking":false}
  ],
  "edges": [
    {"from":"ms-001","to":"ms-002","type":"hard"}
  ]
}
Gate

CVL. If cycles or unmet prereqs → split or re-order.

Phase 4 — Task Decomposition + Routing (📬)
Input

execution_timeline, repo context (paths from nodes; call /repo-ingestion/nodes as needed).

Process

Decompose each milestone into atomic tasks (file-scoped).

Route:

DevBot: single file or ≤2-file constrained diff.

AI IDE: ≥3 files, scaffolds, pattern refactors.

Security milestones: SecurityOpsArchitect.

Populate task schema. Keep descriptions concise and deterministic.

Insert tasks. Log routing decision.

Output
POST /task-queue/insert payload (example):

json
Copy
Edit
[{
  "project_name": "AAO",
  "repo_id": "Owner/Repo",
  "phase": "3.1",
  "milestone_id": "ms-001",
  "subsystem": ["auth","api_gateway"],
  "file_path": "app/api/routes/auth.py",
  "context_files": ["app/core/security.py"],
  "description": "Add RBAC guard to /admin routes; enforce role check",
  "priority": 1,
  "dependencies": [],
  "security_flags": {"security_review_required": true}
}]
Routing log (store alongside task):

json
Copy
Edit
{"task_id":"...","route":"devbot|ai_ide|security","reason_code":"files<=2|pattern_refactor|blocking_security","notes":""}
Rejections

Deterministic rejection → auto-replan once. Otherwise pause and ask user.

Gate

CVL. No missing deps. Routing justified.

Phase 5 — Monitoring + Adaptation (🔁)
Input

Task statuses, execution summaries, fresh repo imports.

Process

User-initiated for V1: on drift or major change → POST /repo-ingestion/import-repo, re-run P1 summary + scoped nodes.

If new diffs touch planned files → re-score affected milestones → re-emit tasks as needed.

Summarize progress and next actions.

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