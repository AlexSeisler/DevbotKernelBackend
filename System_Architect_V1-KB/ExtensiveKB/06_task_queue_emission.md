06_task_queue_emission.md
Purpose: Define the canonical process for decomposing milestones into atomic tasks and emitting them into the project task queue with deterministic routing, priority, and dependency handling.

Core Principles
Atomicity First — Every task represents the smallest executable unit possible without losing clarity.

Routing by Scope — Route tasks to the execution agent best suited based on file count and complexity.

Token Discipline — Descriptions must be concise, deterministic, and context-rich without unnecessary verbosity.

Dependency Safety — Never insert a task into the queue if dependencies are unresolved.

Security Gating — Tasks tagged with blocking security flags must be executed before dependent tasks are queued.

Inputs
milestone_plan: Generated in Phase 2–3; contains milestone IDs, dependencies, subsystem tags, and security flags.

Repo Context (optional): GET /file-structure for pinpointed file paths only when required.

Subsystem Context: Derived from 03_subsystem_map_reference.md.

Processing Steps
Step 1 — Task Decomposition
Break down each milestone into file-scoped or function-scoped tasks.

Each task must:

Have a clear, bounded scope.

Avoid overlapping file edits with other in-progress tasks.

Contain all context needed for execution without referring to external assumptions.

Step 2 — Routing Logic
Routing is determined by file count and complexity pattern:

Scope Type	Route To	Reason Code
Single file or ≤ 2 tightly-related files	DevBot	<=2_files
≥ 3 files or broad pattern refactor	AI IDE	>=3_files or pattern_refactor
Any task with blocking security tags	SecurityOpsArchitect	security_blocking

Step 3 — Priority Scoring
Priority is assigned based on impact, dependencies, and security:

Priority	Definition	Examples
1	High — Blocking milestone, security fix, or critical path task	Fix auth flow, patch SQL injection
2	Medium — Important but non-blocking milestone	Add rate limiting, enhance observability
3	Low — Nice-to-have, non-critical feature	Add optional UI enhancement, refactor tests

Step 4 — Dependency Resolution
Check: All tasks must list dependencies[] from milestone dependencies.

Gate: If dependencies unresolved → hold emission until prerequisites are complete.

Special Rule: Blocking security tasks must be resolved before any dependent tasks enter the queue.

Step 5 — Token Optimization
Use short, structured descriptions that:

State action + target + context.

Avoid filler words or restating milestone text unnecessarily.

Example: "Add pgvector DAO in db/vector_store.py with unit tests"

Step 6 — CVL Validation
Before inserting into the queue:

Assumptions Check — All dependencies and required context confirmed.

Failure Pathways — No known blockers without mitigation.

Redundancy Check — Task is unique; no duplicates in queue.

Goal Alignment — Task supports current milestone and phase.

Execution Risk — No unmitigated high-risk changes.

Strategic Soundness — No simpler, proven alternative available.

Output Structure
All tasks emitted must conform to the following object schema:

json
Copy
Edit
{
  "task_id": "t-123",
  "repo_id": "Owner/Repo",
  "phase": "4",
  "milestone_id": "ms-001",
  "subsystem": ["auth", "queue"],
  "file_path": ["src/auth/login.py"],
  "context_files": ["src/auth/utils.py"],
  "description": "Add RBAC role validation to login handler",
  "priority": 1,
  "dependencies": ["t-122"],
  "security_flags": {"security_review_required": true},
  "route": "devbot|ai_ide|security",
  "reason_code": "<reason from routing table>",
  "notes": ""
}
Emission Process
Batch Allowed: Multiple tasks may be emitted in one request.

Endpoint: POST /task-queue/insert

Emission Log: Maintain a routing_log entry for each emitted task:

json
Copy
Edit
{
  "task_id": "t-123",
  "route": "devbot",
  "reason_code": "<reason>",
  "notes": "Scoped to single file"
}
Re-Planning Triggers
Dependency resolution failure after task emission.

Stale repo state (requires POST /repo-ingestion/import-repo).

Newly detected security risks from ongoing work.

Cross-References
02_build_level_protocols.md

03_subsystem_map_reference.md

04_phase_protocols.md

05_input_processing.md

