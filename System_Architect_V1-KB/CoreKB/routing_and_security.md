# routing_and_security.md

Purpose: decide where work goes and when to scaffold security. Tight, upstream-only rules for V1.

## Routing policy

### Granularity rule
- **DevBot** → single file or **≤2-file** constrained diff.
- **AI IDE (Cursor, Claude Code)** → **≥3 files**, cross-file scaffolds, or pattern refactors.
- **SecurityOpsArchitect** → all security milestones (enforcement tasks only).

### Overrides
- Any exception requires **explicit user approval** and a short routing note.
- Do not assign multi-file work to DevBot. Do not assign single-file patches to AI IDE without justification.

### Required task fields (min)
For each emitted task (to `/task-queue/insert`):
repo_id, phase, milestone_id, subsystem[], file_path, context_files[], description, priority(1|2|3), dependencies[], security_flags{}

shell
Copy
Edit

### Routing log (store alongside task)
task_id, route:("devbot"|"ai_ide"|"security"), reason_code, notes

markdown
Copy
Edit
Reason codes: `files<=2`, `pattern_refactor`, `blocking_security`, `user_override`.

### Rejections
- Deterministic rejection (missing dep, stale file, schema mismatch) → **auto-replan once**.
- Otherwise pause and ask user.

---

## Security scaffolding (V1)

**Scope:** Architect **flags and schedules**. SecurityOpsArchitect **enforces**.

### Blocking areas (set `security_review_required=true`)
- `auth` (identity, RBAC, token issuance/verification)
- `data_access/database` (RLS, PII handling, migrations with exposure risk)
- `payments` (Stripe/webhooks/quotas)
- `webhooks_integrations` (inbound/outbound signatures, idempotency)
- `admin_console` (privileged routes, audit trails)

**Effect:** place blocking security milestones **before** dependent public exposure in the DAG.

### Non-blocking but level-mandatory
- Rate limiting for public endpoints (L3+)
- Basic request validation/schema checks (L3+)
- Metrics/tracing exporters (L4+)
- Feature flags around risky deploys (L4+)

Emit as normal milestones (no gate), but include notes in `security_flags`.

### Minimal milestone templates (examples)
phase: "3.1"
subsystem: ["auth","api_gateway"]
description: "Add RBAC guards to admin routes; require role=admin"
security_flags: { security_review_required: true }

phase: "3.2"
subsystem: ["api_gateway"]
description: "Enable request validation for /v1/*"
security_flags: { schema_validation: "pydantic" }

yaml
Copy
Edit

---

## CVL checklist (apply before emission in every phase)
- **Assumptions**: empty.
- **Failure Pathways**: identified; security gates positioned.
- **Redundancy**: no duplicate milestones/tasks.
- **Goal Alignment**: level, tenancy, auth, scope confirmed.
- **Execution Risk**: capacity/cost/security addressed.
- **Strategic Soundness**: simplest proven pattern chosen.

---

## Quick routing examples

1) Add role check in `app/api/admin.py` and update `app/core/security.py`  
→ **DevBot** (`files<=2`, file-scoped patch)

2) Scaffold new `jobs/` module + workers + wiring across 6 files  
→ **AI IDE** (`pattern_refactor`, multi-file scaffold)

3) Verify Stripe webhook signature and add idempotency for charges  
→ **SecurityOpsArchitect** (`blocking_security` milestone → enforcement tasks)

---

## Cross-refs
- `mission_and_role.md` — mandate, boundaries, CVL gate
- `build_levels_and_subsystems.md` — subsystem purposes and phase hooks
- `phase_execution.md` — when routing and security gates are applied