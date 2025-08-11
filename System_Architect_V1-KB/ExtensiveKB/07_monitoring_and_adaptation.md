07_monitoring_and_adaptation.md
Purpose: Define the continuous observation, drift detection, and adaptive re-planning protocols for the System Architect. Ensures in-flight execution stays aligned with project goals, security standards, and performance targets.

Core Principles
Continuous Awareness — Monitor all active work streams for status, drift, or bottlenecks.

Reactive & Proactive Adaptation — Re-plan in response to both observed failures and anticipated risks.

Minimal Overhead — Tracking and adaptation must be lightweight to avoid slowing the execution loop.

CVL Gate at Phase Boundaries — Every adaptation passes through the Critical Validation Loop before changes are finalized.

Inputs
Task Queue State: From /task-queue/query or direct DB access.

Execution Summaries:

DevBot: branch diffs, status logs, errors.

AI IDE: PRs, scaffold outputs.

SecurityOpsArchitect: milestone validation results.

Repo State:

GET /repo-ingestion/node-summary

GET /repo-ingestion/nodes

User Signals:

Change requests, scope adjustments, new requirements.

Monitoring Scope
1. Progress Tracking
Maintain live status per task (in_progress, blocked, done, failed).

Track time-in-state for each task to spot stalled work.

Visualize dependencies to identify critical path delays.

2. Drift Detection
Repo Drift: Changes to planned files outside queued tasks.

Goal Drift: User goals evolving mid-phase without re-alignment.

Security Drift: New vulnerabilities introduced during execution.

3. Error & Failure Monitoring
Capture execution errors from all agents.

Log failures with:

Task ID

Error type

Suggested mitigation

Impacted dependencies

Trigger Conditions for Adaptation
Trigger Type	Example	Required Action
Repo Change	Direct commit modifies planned subsystem	Re-ingest repo & re-score impacted milestones
Dependency Block	Task can’t proceed until another completes	Re-order or split tasks
Error Burst	≥3 failures in the same subsystem within 24h	Add diagnostic milestone; gate dependents
Scope Change	User adds multi-tenant support mid-phase	Level escalation + new infra milestones
Security Event	New OWASP Top 10 vulnerability detected	Insert blocking security milestone before dependents
SLA Breach	p95 latency or error rate exceeds threshold from 02_build_level_protocols.md	Prioritize optimization milestone

Adaptive Re-Planning Process
Step 1 — Identify Trigger
Use logs, user signals, and monitoring metrics.

Classify as deterministic (no user choice) or discretionary (requires user confirmation).

Step 2 — Scope Impact
Identify milestones and tasks affected.

Determine if changes are local (subsystem) or global (cross-phase).

Step 3 — Adjust Plan
Modify milestone dependencies, priorities, or routes.

Split overly broad tasks into smaller atomic units if bottlenecked.

Step 4 — Execute CVL Gate
Assumptions Check: New assumptions valid?

Failure Pathways: Risk introduced?

Redundancy Check: Are we duplicating effort?

Goal Alignment: Still aligned with user’s mission?

Execution Risk: Tradeoffs acceptable?

Strategic Soundness: Simpler approach available?

Step 5 — Emit Changes
Update affected milestones in planning memory.

Re-emit impacted tasks via POST /task-queue/insert.

Security Injection Points
Any security drift or new risk triggers:

Immediate insertion of blocking security milestone.

Handoff to SecurityOpsArchitect for mitigation.

Output Structure
status_report (chat or API response):
json
Copy
Edit
{
  "phase": 4,
  "milestones_completed": 12,
  "milestones_blocked": 2,
  "drift_events": [
    {"type": "repo_change", "impact": "vector subsystem", "action": "re-ingest"}
  ],
  "next_actions": [
    "Re-score milestones in queue subsystem",
    "Emit blocking security task for new webhook endpoint"
  ]
}
Re-Planning Triggers Summary
Repo drift touching planned files.

New dependencies discovered mid-phase.

Security scope expansion (PII, payment data).

SLA breaches or capacity constraints.

Cross-References
02_build_level_protocols.md

04_phase_protocols.md

05_input_processing.md

06_task_queue_emission.md

08_security_scaffolding.md

09_security_milestone_templates.md