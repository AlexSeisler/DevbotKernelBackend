Mapping
mission_and_role.md ← 00_mission + 01_role_definition
Include: upstream-only, CVL gate, routing boundaries, handoffs.

build_levels_and_subsystems.md ← 02 + condensed 03
Include: L1–L5 table (users, gates, exits), quick subsystem table with indicators + risk tags.

phase_execution.md ← 04 + 05 core gates
Include: 5 phases as Input→Process→Output, decision trees, re-plan triggers, “assumptions must be empty” before plan.

routing_and_security.md ← 06–09 minimums
Include: ≤2 files→DevBot, ≥3/pattern→AI IDE, override rules; blocking tags→security_review_required=true; minimal CVL checklist.

tooling_and_prompts.md (optional) ← 10–11
Include: one-line stack defaults per level; 3–5 prompt snippets (diagnostics, missing context, security scaffold).

Non-negotiables to keep
Block planning until assumptions == ∅.

No /refresh/repo; re-run /repo-ingestion/import-repo.

Use /node-summary and /nodes only; /file-structure rare edge.

Level escalation requires user approval.

Security: scaffold only; blocking = auth/data access/payments/webhooks.

Dry-run checklist
Load only compressed KB.

Run on a small FastAPI repo.

Expect: level classify → milestones → routed tasks → no clarifications needed.

Patch gaps, iterate.