# 05_input_processing.md

Purpose: normalize minimal inputs, infer context, and hard-gate planning. Tight and directive.

## Core input (minimal)
```json
{
  "project_goal": "string",
  "target_level": "L1|L2|L3|L4|L5|unknown",
  "project_phase": "new|partial|upgrade|unknown",
  "repo": {"repo_id":"Owner/Repo|nullable","present":true|false},
  "notes":"string|optional"
}
Auto-computed (do not store; compute on read)
objectives[] from project_goal.

subsystems_focus[] from repo node summary.

tenancy|auth|data_sensitivity|payments inferred from repo; ask only if inference fails.

evidence.repo_ref = "Owner/Repo@main" if repo present; else "none".

Normalization + inference
If repo.present=true and repo.repo_id set:

GET /repo-ingestion/node-summary?repo_id=...

Optionally: GET /repo-ingestion/nodes?repo_id=...&subsystem=...&fields=slim|slim-code

If user signals stale, POST /repo-ingestion/import-repo then re-fetch.

Infer project_phase when user did not set:

No repo ⇒ new

Repo present ⇒ compare snapshot vs goal: major delta ⇒ upgrade; partial alignment ⇒ partial.

Infer target_level if unknown after repo analysis (see 02_build_level_protocols.md).

Auto-fill subsystems_focus from detection when empty (warning, not block).

If code/schema shows PII/PHI while data_sensitivity=unknown ⇒ upgrade to pii or phi and warn.

Defaults: assume “no” until evidence says “yes.” Ask only when inference fails.

Hard gates (block)
project_goal empty.

target_level=unknown after repo analysis.

project_phase=unknown after inference.

For L3+: tenancy unknown or auth unknown.

Payments mentioned but provider unknown.

Repo declared but node summary not retrievable.

Warnings (non-blocking)
Vector/AI/Queue/UI flags unknown at L3.

subsystems_focus auto-filled.

No diagrams/docs.

Clarifiers (max 3 in Phase 1)
Scale/level: “Target users and concurrency? Confirm L1–L5.”

Tenancy: “Single or multi-tenant?”

Auth: “Auth provider and required roles?”

Only when triggered by risk surface:

“Any PII/PHI?” (if user data present)

“Stripe needed?” (if payments endpoints detected)

Validation gate
Emit alignment_input.json and ready_to_plan.

Success

json
Copy
Edit
{
  "alignment_input": {
    "project_goal":"...",
    "target_level":"L3",
    "project_phase":"partial",
    "repo":{"repo_id":"Owner/Repo","present":true},
    "subsystems_focus":["auth","api_gateway","vector"],
    "assumptions":[]
  },
  "ready_to_plan": true
}
Failure

json
Copy
Edit
{
  "ready_to_plan": false,
  "gaps": ["target_level_unknown","tenancy_unknown","auth_model_unknown","repo_unreadable"],
  "next_questions": [
    "Target users and concurrency? Confirm L1–L5.",
    "Single or multi-tenant?",
    "Auth provider and required roles?"
  ]
}
CVL pre-check
assumptions must be empty.

Any hard block ⇒ stop.

API references
Refresh: POST /repo-ingestion/import-repo

Nodes: GET /repo-ingestion/nodes?repo_id=...&subsystem=...&fields=slim|slim-code

Summary: GET /repo-ingestion/node-summary?repo_id=...

Cross-references
Levels: 02_build_level_protocols.md

Subsystems: 03_subsystem_map_reference.md

Phases: 04_phase_protocols.md

Emission: 06_task_queue_emission.md