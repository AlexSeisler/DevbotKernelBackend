10_prompt_templates.md
Purpose: Centralized, reusable prompt bank for the System Architect. Modular blocks cover diagnostics, planning, security checks, confirmations, and branching logic. Designed to reduce rewording time and ensure consistent reasoning.

Core Principles
Reusable & Modular — Each prompt is a stand-alone building block.

Directive First — No vague open-ended questions unless explicitly needed.

Context-Aware — Templates expect the relevant KB subset to already be loaded.

Minimal Token Overhead — No excessive framing; straight to the point.

CVL Embedded — All critical prompts include the Critical Validation Loop when appropriate.

Template Categories & Blocks
1. Diagnostics & Health Checks
Use: Quickly verify state, data freshness, and readiness before proceeding.

Templates:

plaintext
Copy
Edit
Run a /health check and confirm service status before continuing.
plaintext
Copy
Edit
Verify /repo-ingestion/node-summary for {repo_id} and confirm all expected subsystems are present.
plaintext
Copy
Edit
Re-ingest repo {repo_id} using /repo-ingestion/import-repo, then re-run /repo-ingestion/nodes to confirm node set matches expected subsystems.
2. Planning & Architecture
Use: Kick off structured planning phases or generate subsystem maps.

Templates:

plaintext
Copy
Edit
Using the alignment report, generate the Phase {n} milestone plan with dependencies and blocking flags. Apply CVL before output.
plaintext
Copy
Edit
Create a subsystem-to-target mapping for build level {L#}, ensuring all missing subsystems are scaffolded.
plaintext
Copy
Edit
Construct a DAG for the provided milestone plan, placing security-blocking milestones before their dependents.
3. Security Checks
Use: Apply security review logic or inject milestone scaffolds.

Templates:

plaintext
Copy
Edit
Review subsystems {subsystems[]} for security-blocking conditions using 08_security_scaffolding.md rules, then emit required milestones from 09_security_milestone_templates.md.
plaintext
Copy
Edit
Perform STRIDE threat model analysis on the planned architecture and list mitigation tasks for each threat type.
plaintext
Copy
Edit
Inject security_review_required=true for all public endpoints without validation or rate limits.
4. Task Decomposition & Routing
Use: Split milestones into atomic tasks with correct routing.

Templates:

plaintext
Copy
Edit
Decompose milestone {id} into atomic file-scoped tasks, route to DevBot if ≤2 files, AI IDE if ≥3 files, SecurityOpsArchitect if security-blocking.
plaintext
Copy
Edit
Populate task queue entries with repo_id, phase, milestone_id, subsystem[], file_path, context_files[], description, priority, dependencies[], security_flags{}.
plaintext
Copy
Edit
Apply CVL to each task before queue insertion. Do not emit if CVL fails.
5. Confirmations & Alignment
Use: Verify with the user before committing significant changes.

Templates:

plaintext
Copy
Edit
Confirm scope change: Level escalation from L{old} to L{new} due to {reason}. Proceed?
plaintext
Copy
Edit
Confirm addition of new subsystem {subsystem} due to missing core functionality. Proceed?
plaintext
Copy
Edit
Execution risk detected: {risk}. Recommend mitigation milestone before proceeding. Confirm?
6. Conditional Branching Prompts
Use: Dynamically adjust path based on results.

Templates:

plaintext
Copy
Edit
If repo appears stale, trigger /repo-ingestion/import-repo and re-fetch nodes. If still stale, request manual input from user.
plaintext
Copy
Edit
If CVL fails, re-run with reduced complexity or fallback template. If fails again, request user guidance.
plaintext
Copy
Edit
If DAG cycle detected, split milestone into smaller units with interface contracts before re-running DAG build.
Quick Reference
/health — Confirm services alive.

node-summary — Validate subsystem coverage.

import-repo — Refresh stale repos.

CVL — Validate before emit.

SecurityOpsArchitect — Always route blocking milestones.

Cross-References
04_phase_protocols.md

06_task_queue_emission.md

08_security_scaffolding.md

09_security_milestone_templates.md