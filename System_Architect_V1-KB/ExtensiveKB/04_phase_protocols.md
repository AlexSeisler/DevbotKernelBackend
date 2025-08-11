# 04_phase_protocols.md

Purpose: run the Architect in five phases with **Input → Process → Output**, explicit decision trees, security injection points, and re-planning triggers. Tight and directive.

## Global rules
- Classify level first (see `02_build_level_protocols.md`).
- Route by granularity: **≤2 files → DevBot**, **≥3 files/pattern → AI IDE**. Document overrides.
- Security = scaffold only. **Blocking** tags auto-enqueue `security_review_required=true`.
- CVL gate at end of every phase. Do not emit if CVL fails.
- Endpoints in scope:  
  - `GET /repo-ingestion/node-summary`  
  - `GET /repo-ingestion/nodes`  
  - `POST /repo-ingestion/import-repo` (refresh)  
  - `POST /task-queue/insert`  
  - `GET /file-structure` (pinpoint use only)

---

## Phase 1 — User Alignment (🧭)
### Input
- User goals, requirements, docs, diagrams.
- Optional `repo_id`.
- System defaults (global tech choices).

### Process
1) Normalize inputs (see `05_input_processing.md`).  
2) If `repo_id` present:  
   - `GET /repo-ingestion/node-summary`  
   - Pull scoped sets via `GET /repo-ingestion/nodes?repo_id=&subsystem=…`  
   - If repo appears stale by user signal → `POST /repo-ingestion/import-repo` then re-fetch.
3) Classify **L1–L5**.
4) Detect **missing context**; request immediately.
5) Draft **assumptions**; block until resolved.

### Decision tree
- No repo → plan **greenfield**; add “import_repo” milestone.  
- Goals exceed level capacity → pick higher level and add scope-reduction milestone.

### Security injection
- If high-risk subsystems (auth, queue, vector, webhooks, payments, admin, data_access) → add scaffold placeholders (see `08/09`).

### Output
`alignment_report` (in-memory):
```json
{
  "target_level": "L3",
  "project_phase": "new|partial|upgrade",
  "subsystems": [],
  "gaps": [],
  "assumptions": [],
  "security_flags": {}
}
Re-planning triggers
User changes goals.

Missing inputs resolved.

Repo refreshed with materially different state.

Phase 2 — Infra + System Planning (🧱)
Input
alignment_report

Node summary + filtered node sets

03_subsystem_map_reference.md

Process
For each required subsystem: Current → Target mapping by level.

Create milestones with dependencies and blocking flags.

Attach security milestones from triggers (08/09).

Add cross-cutting milestones (observability, rate limits; billing at L4+).

Validate tenancy, quotas, RLS at L4+.

Decision tree
Subsystem missing but required → add one global scaffold milestone for that subsystem.

Present but below target → add upgrade milestone.

Risk tags with blocking → schedule security milestone before dependents.

Security injection
Auth/RBAC, data access, webhooks, payments = blocking by default.

Queue idempotency, input validation, tracing = non-blocking but mandatory by level.

Output
milestone_plan (list of):

json
Copy
Edit
{
  "id": "ms-001",
  "title": "Enable vector store",
  "description": "Add pgvector with schema + DAO",
  "phase_label": "3.1",
  "deps": ["ms-000"],
  "blocking": false,
  "subsystem": ["vector"],
  "security_flags": {}
}
phase_label format is "n.m" only.

Re-planning triggers
New subsystem discovered.

Level escalates (multi-tenant, SSO, quotas).

Security scope expands (e.g., PII detected).

Phase 3 — Timeline + Prioritized Execution Map (📆 DAG)
Input
milestone_plan

Process
Build a DAG; compute critical path.

Assign phase order and priorities (1=high, 2=med, 3=low).

Place security blocking milestones before dependent deploys.

Capacity rules:

Avoid parallel work on the same file/module by ordering/dependencies (no locks).

Defer heavy vector/index jobs to later phases if they block core delivery.

Add upgrade triggers from 02_build_level_protocols.md.

Decision tree
DAG cycle → split milestone or insert interface contract step.

Any milestone needs L(n+1) → add infra milestone and confirm level bump with user.

Security injection
Place threat-model/audit steps before exposing public endpoints or external auth.

Output
execution_timeline (DAG JSON):

json
Copy
Edit
{
  "nodes": [{"id":"ms-001","title":"Enable vector","priority":2,"blocking":false}],
  "edges": [{"from":"ms-000","to":"ms-001","type":"hard"}]
}
prioritized_backlog (ordered milestones)

Re-planning triggers
Queue p95 wait or cost triggers from 02.

New compliance or SSO requirement.

Phase 4 — Task Decomposition + Routing (📬)
Input
prioritized_backlog

Repo context (use GET /file-structure only when pinpoint paths are required)

Process
Decompose each milestone into atomic tasks (file-scoped).

Routing:

DevBot: single file or ≤2-file constrained diff.

AI IDE: ≥3 files, scaffolds, pattern refactors.

SecurityOpsArchitect: all security milestones.

Populate fields (see 06_task_queue_emission.md):

repo_id, phase, milestone_id, subsystem[], file_path, context_files[], description, priority, dependencies[], security_flags{}

Token optimization: concise, deterministic descriptions.

CVL validation before insert.

Decision tree
File count unclear → clarify before emitting.

Blocking security tag → emit security task first; gate dependents.

Unresolved dependency → hold emission; add prerequisite task.

Security injection
Set security_review_required=true for blocking tags.

Add rate-limit and validation tasks for public endpoints.

Output
POST /task-queue/insert (batch allowed; no enforced limit)

routing_log entries:

json
Copy
Edit
{
  "task_id":"t-123",
  "route":"devbot|ai_ide|security",
  "reason_code":"<=2_files|>=3_files|pattern_refactor|security_blocking",
  "notes":""
}
Re-planning triggers
Deterministic rejection (missing dep, stale state) → one auto-replan, then pause for user input.

Ambiguous rejection → request user input.

Phase 5 — Continuous Monitoring + Adaptation (🔁)
Input
Task queue outputs, DevBot execution_summary, IDE branches/diffs.

(Events/heartbeats not implemented in V1)

Process
Manual review cadence (user-managed).

Detect drift:

User signals repo changed → POST /repo-ingestion/import-repo then re-ingest nodes.

Long-running tasks without updates → mark “blocked” in status report.

Evaluate KPIs:

Error rate, p95 latency, cost per task/tenant (from 02 thresholds).

Adaptive re-plan:

Deterministic failures → patch plan.

Scope changes → confirm with user.

Decision tree
Repo diffs touch planned files → re-score impacted milestones → re-emit tasks.

SLA breach → add capacity/optimization milestones first; level escalation only with user approval.

Security injection
New risk tags from fresh code → enqueue corresponding milestones immediately.

Output
status_report (chat-only in V1): progress, risks, next actions.

Updated milestones/tasks as needed.

CVL gates (phase-end)
Assumptions Check: any unresolved input → block.

Failure Pathways: single points of failure addressed.

Redundancy Check: duplicates removed.

Goal Alignment: level and user goals consistent.

Execution Risk: capacity, cost, security covered.

Strategic Soundness: simpler proven pattern available?

Cross-references
02_build_level_protocols.md

03_subsystem_map_reference.md

05_input_processing.md

06_task_queue_emission.md

07_monitoring_and_adaptation.md

08_security_scaffolding.md

09_security_milestone_templates.md