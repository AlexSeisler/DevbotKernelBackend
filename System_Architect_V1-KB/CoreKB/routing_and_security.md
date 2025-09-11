# routing_and_security.md (v1.1)

Purpose: decide where work goes and when to scaffold security. Upstream-only rules for V1. Enforces routing discipline, task schema minimums, and security review scope.

---

## Routing policy

### Granularity rule
- **DevBot** → single file or **≤2-file** constrained diff (targeted patch).
- **AI IDE (Cursor, Claude Code)** → **≥3 files**, cross-file scaffolds, or pattern refactors.
- **SecurityOpsArchitect** → **review tickets only** for blocking security areas (no implementation). Implementation still routes to DevBot/AI IDE per granularity.

### Overrides
- Any exception requires **explicit user approval** and a short routing note.
- Do **not** assign multi-file work to DevBot or single-file patches to AI IDE without justification.

### Routing log (store alongside task)
{ task_id, route:("devbot"|"ai_ide"|"security"), reason_code, notes }

yaml
Copy
Edit
Reason codes: `files<=2`, `pattern_refactor`, `blocking_security`, `user_override`, `correctness.idempotency_required`, `legal_review_required`.

---

## Task emission requirements

**Minimum fields (to `/task-queue/insert`)**
project_name, repo_id, phase_label, milestone_id, subsystem[],
file_path, context_files[], description, priority(1|2|3),
dependencies[], security_flags{}

markdown
Copy
Edit

**Defaults & conventions**
- `status`: default **`queued`** (task FSM: `idea → queued → running → done|blocked`).
- **DevBot** tasks must include a concrete `file_path` and **1–3 `context_files`** (e.g., sibling router/model) to reduce retries.
- **AI IDE** tasks may use a **target directory** in `file_path` (e.g., `"backend/vector/"`) and must set `deliverable:"branch+diff+summary"`.
- **Security review tickets** must write to `docs/security/<ticket>.md` (satisfies non-null `file_path`).
- **Greenfield mode**: `repo_id:"none"` allowed **only** when explicitly declared; otherwise require a real repo id.

**Rejections**
- Deterministic (missing dep, stale file, schema mismatch) → **auto-replan once**.
- Otherwise **pause and ask** the user.

---

## Security scaffolding (V1)

**Scope:** Architect **flags and schedules**. SecurityOpsArchitect **reviews/enforces** via tickets; code changes route by granularity.

### Blocking areas → set `security_review_required: true`
- `auth` (identity, RBAC, token issuance/verification)
- `uploads` (object storage ingress, MIME/size validation)
- `data_access/write` (migrations, RLS/PII exposure, write-path correctness)
- `payments` (Stripe/webhooks/quotas)
- `webhooks_integrations` (signatures, idempotency, retries)
- `admin_console` (privileged routes, audit trails)

**Also treat as security-reviewed:** **write-path reliability controls** (e.g., **idempotency keys**) and any feature enabling public ingress.

### Non-blocking but level-mandatory
- Rate limiting for public endpoints (L3+)
- Request/response schema validation (L3+)
- Metrics/tracing exporters (L4+)
- Feature flags around risky deploys (L4+)

Emit as normal milestones (no gate) but include notes in `security_flags`.

### Propagation rule
- **Propagate `security_flags`** into **DAG nodes** and **all emitted tasks** for traceability.

---

## CVL checklist for routing (apply before emission)
- **Assumptions**: empty.
- **Failure Pathways**: security gates positioned before exposure.
- **Redundancy**: no duplicate milestones/tasks.
- **Goal Alignment**: level, tenancy, scope confirmed.
- **Execution Risk**: capacity/cost/security addressed.
- **Traceability**: routing log present; security flags propagated.

---

## Quick routing examples

1) Add role check in `app/api/admin.py` and update `app/core/security.py`  
→ **DevBot** (`files<=2`, file-scoped patch)

2) Scaffold `jobs/` workers + adapters across 6 files  
→ **AI IDE** (`pattern_refactor`, multi-file scaffold, `deliverable:"branch+diff+summary"`)

3) Verify Stripe webhook signature + add idempotency; create review ticket  
→ **SecurityOpsArchitect** (**ticket** in `docs/security/ms-payments-webhooks_review.md`),  
   implementation PRs route to DevBot/AI IDE with reason `blocking_security`

4) Add idempotency to `POST /applications` write path  
→ **DevBot** (1–2 files) with reason `correctness.idempotency_required` and `security_flags.security_review_required:true`

5) New scraper targeting ToS-risky source  
→ Emit `legal_review_required:true`, route implementation to AI IDE, add reason `legal_review_required`, suggest permissive alternatives.

---

## Cross-refs
- `mission_and_role.md` — mandate, boundaries, CVL gate
- `build_levels_and_subsystems.md` — subsystem purposes and phase hooks
- `phase_execution.md` — when routing and security gates are applied
- `tooling_and_prompts.md` — copy-ready prompts enforcing these rules
