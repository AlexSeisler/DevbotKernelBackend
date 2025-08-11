08_security_scaffolding.md
Purpose: Define how the System Architect detects, injects, and routes security scaffolds at the planning stage, ensuring risks are addressed early and consistently across all build phases.

Core Principles
Security-by-Default — Assume every subsystem can be attacked; mitigate proactively.

Early Injection — Security scaffolds are inserted before implementation tasks begin.

Blocking as a Feature — Certain risks must block execution until resolved (e.g., broken auth, exposed PII).

Level-Aware Security — Higher build levels (L4–L5) have stricter security expectations.

CVL Enforcement — Security gates run through the Critical Validation Loop before approving downstream work.

Inputs
Subsystem Mapping from 03_subsystem_map_reference.md

Build Level Protocols from 02_build_level_protocols.md

Phase Protocols from 04_phase_protocols.md

Risk Indicators from:

STRIDE

DREAD scoring

OWASP Top 10 alignment

Repo Context:

GET /repo-ingestion/node-summary

GET /repo-ingestion/nodes

Security Injection Triggers
Trigger Source	Example	Action
Subsystem Type	auth, queue, vector, payments, admin, data_access, webhooks	Auto-insert scaffold milestones
Build Level Escalation	L3 → L4 (multi-tenant)	Add RLS, quota enforcement, SSO/OIDC scaffolds
Risk Tags	security_high, PII_detected, unvalidated_input	Insert blocking milestone, require SecurityOpsArchitect
User Requirement	Compliance (HIPAA, PCI-DSS, SOC2)	Add compliance-specific security patterns
Drift Detection (Phase 5)	New risky file detected	Inject mid-phase scaffold milestone

Security Scaffold Types
1. Blocking Scaffolds (execution halts until resolved)
Authentication/RBAC

Payment processing

Admin panel access

PII handling

External-facing webhooks with write access

2. Non-Blocking Scaffolds (must be done but can run in parallel)
Input validation

Rate limiting

Request/response logging

Queue idempotency

Threat monitoring hooks

STRIDE Alignment
Threat	Scaffold Example
Spoofing	Strong auth, signed requests, MFA integration
Tampering	Checksums, immutability guarantees, DB write audit logs
Repudiation	Signed logs, non-repudiation audit trail
Information Disclosure	Encryption at rest/in transit, field-level masking
Denial of Service	Rate limits, circuit breakers, autoscaling guardrails
Elevation of Privilege	Strict RBAC, privilege separation, security audits

DREAD Scoring Use
Score each subsystem for Damage, Reproducibility, Exploitability, Affected Users, Discoverability.

Auto-block execution for scores ≥ 8/10 in any category.

OWASP Top 10 Coverage
Injection, broken auth, sensitive data exposure, XML external entities, broken access control, security misconfigurations, XSS, insecure deserialization, using vulnerable components, insufficient logging & monitoring.

Injection Workflow
Step 1 — Detect Trigger
From subsystem map, repo scan, or user input.

Step 2 — Classify Risk Level
Blocking vs non-blocking.

Step 3 — Insert Scaffold Milestone
Format (JSON-like):

json
Copy
Edit
{
  "id": "sec-001",
  "title": "Add RBAC scaffold",
  "description": "Implement role-based access control placeholders",
  "phase_label": "2.1",
  "blocking": true,
  "subsystem": ["auth"],
  "security_flags": {"risk_level": "high", "required_by": "SecurityOpsArchitect"}
}
Step 4 — Route to SecurityOpsArchitect
If blocking or compliance-bound.

Step 5 — CVL Gate
Run through:

Assumptions Check: Are we targeting the right threat?

Failure Pathways: Could this still be bypassed?

Redundancy Check: Is it already covered elsewhere?

Goal Alignment: Matches build level & scope?

Execution Risk: Acceptable trade-offs?

Strategic Soundness: Simpler proven pattern available?

Outputs
security_scaffold_plan — all injected scaffolds, with metadata for routing.

phase_integration_map — links scaffold to the milestones they protect.

Cross-References
02_build_level_protocols.md

03_subsystem_map_reference.md

04_phase_protocols.md

09_security_milestone_templates.md