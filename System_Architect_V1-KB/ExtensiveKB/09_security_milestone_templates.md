09_security_milestone_templates.md
Purpose: Provide ready-to-insert milestone templates for high-priority security tasks, tied to subsystems and build levels. These templates ensure consistency and reduce decision latency in the System Architect’s security injection process.

Core Principles
Pre-Built for Speed — Architect should not reinvent common security steps.

Level-Scoped — Higher build levels get additional depth (e.g., L5 includes compliance and continuous monitoring).

Phase-Linked — Templates are tagged with the phase(s) in which they should be injected.

SecurityOpsArchitect Ready — All blocking milestones pre-flagged for handoff.

Template Structure
json
Copy
Edit
{
  "id": "sec-###",
  "title": "Short, actionable title",
  "description": "Concise detail of the security measure to implement",
  "phase_label": "n.m",
  "blocking": true|false,
  "subsystem": ["auth", "queue", "vector", ...],
  "security_flags": {
    "risk_level": "low|medium|high|critical",
    "required_by": "SecurityOpsArchitect",
    "compliance": ["HIPAA", "PCI-DSS", "SOC2"]
  }
}
Template Categories & Examples
1. Authentication & Access Control
ID	Title	Description
sec-auth-001	Implement RBAC scaffold	Add role-based access placeholders with tenant-aware permissions.
sec-auth-002	MFA Integration placeholder	Scaffold logic for integrating MFA provider before production release.
sec-auth-003	Admin panel access restrictions	Block all non-admin traffic from accessing /admin routes.

2. Data Protection
ID	Title	Description
sec-data-001	Encrypt sensitive fields at rest	Enable field-level AES256 encryption for PII.
sec-data-002	TLS enforcement	Require TLS 1.2+ for all inbound/outbound connections.
sec-data-003	Data masking in logs	Mask sensitive values in logs (SSNs, tokens, card numbers).

3. Queue & Job Processing
ID	Title	Description
sec-queue-001	Job idempotency checks	Prevent duplicate job execution on retries.
sec-queue-002	Queue isolation by tenant	Separate queues for each tenant to prevent cross-data leakage.

4. Payments & Billing
ID	Title	Description
sec-pay-001	PCI-DSS placeholder	Scaffold card handling service to meet PCI-DSS guidelines.
sec-pay-002	Payment webhook signature validation	Verify webhook payloads with HMAC signatures.

5. Webhooks & External APIs
ID	Title	Description
sec-webhook-001	Webhook auth token validation	Require pre-shared token for inbound webhook calls.
sec-webhook-002	External API rate-limiting scaffold	Prevent abuse of outbound API calls by rogue scripts.

6. Compliance & Monitoring
ID	Title	Description
sec-comp-001	HIPAA audit log scaffold	Prepare structured audit log format for HIPAA compliance.
sec-comp-002	SOC2 logging requirements	Enable central logging with access audit trails.
sec-comp-003	Security event monitoring hook	Add hook to feed logs into SIEM platform.

Phase Hooks
Phase	Recommended Templates
Phase 2 — Infra & Planning	RBAC, MFA, TLS enforcement, PII encryption scaffolds.
Phase 3 — Timeline/DAG	Job idempotency, payment webhook validation, queue isolation.
Phase 4 — Task Routing	Data masking in logs, security event monitoring hooks.
Phase 5 — Monitoring	SIEM hooks, SOC2/HIPAA log verification.

Blocking vs Non-Blocking Defaults
Blocking — Authentication, PII encryption, compliance placeholders, admin access, payment security.

Non-Blocking — Job idempotency, data masking, API rate limiting, monitoring hooks.

Cross-References
02_build_level_protocols.md

03_subsystem_map_reference.md

08_security_scaffolding.md