# 02_build_level_protocols.md

## Purpose
Define L1–L5 build levels. Lock scale, security, SLAs, and routing defaults. Guide classification and planning.

> **Users = active tenants** by default; track MAU/DAU as secondary signals.

## Fast Map
| Level | Name                    | Tenants (guidance) | Goal                     | Primary Risks                    |
|------:|-------------------------|--------------------|--------------------------|----------------------------------|
| L1    | Concept Prototyper      | 1–10               | Prove idea               | None tracked                     |
| L2    | Orchestration Prototyper| ≤100               | Wire agents/APIs         | Cost leaks, brittle flows        |
| L3    | Agent Platform Builder  | ≤1,000             | User-ready platform      | Auth scope, queue failure        |
| L4    | SaaS Infra Architect    | ≤10,000            | Multi-tenant scale       | RLS leaks, quota abuse           |
| L5    | AI Product Architect    | >10,000            | Market-grade product     | Model drift, product churn       |

## API SLA by Level
| Level | Availability | p95 Latency | Error Budget |
|------:|--------------|-------------|--------------|
| L1    | none         | n/a         | n/a          |
| L2    | 95%          | ≤1500 ms    | n/a          |
| L3    | 97.5%        | ≤800 ms     | 2.5%         |
| L4    | 99.5%        | ≤400 ms     | 0.5%         |
| L5    | 99.9%        | ≤250 ms     | 0.1%         |

## Classification Rules
- Use stack, target tenants, and SLA to set level.
- If any L(n+1) requirement exists, classify as **L(n+1)**.
- If unknown, choose lower level and add a **confirm-scope** milestone.
- Default to **higher level on conflicting signals**.

## Security by Level
- **L1**: hygiene only. No secrets in repo. No public endpoints.
- **L2**: basic JWT, rate caps, input validation.
- **L3**: **scaffolds** on high-risk subsystems. See `08_security_scaffolding.md`, templates in `09_security_milestone_templates.md`.
- **L4**: **enforcement**. RLS, quotas, CI/CD gates, tracing, audit logs.
- **L5**: continuous reviews, playbooks, incident response.

---

## L1 — Concept Prototyper
**Scope**: local/single instance. Manual flows.  
**Infra**: single FastAPI/script. No queue. No observability.  
**Auth**: none or dev-only.  
**Data**: local Postgres preferred; SQLite allowed for throwaway spikes.  
**AI**: single model call. Hardcoded keys.  
**Observability**: print logs.  
**Exit → L2**: live demo need, external APIs, or user trials.

## L2 — Orchestration Prototyper
**Scope**: FastAPI + YAML tool routing. Supabase for data/auth.  
**Infra**: Render/Railway (Fly if needed). No autoscaling. No SLOs.  
**Auth**: Supabase JWT. Basic RBAC if trivial.  
**Data**: Postgres (Supabase). Optional vector trial (pgvector in Supabase; Chroma local if needed).  
**AI**: GPT tools/functions. Pre-LangGraph multi-agent flows.  
**Observability**: JSON logs stored.  
**Security**: token vault; basic input validation; **no admin routes**.  
**Exit → L3**: real users, async tasks, hybrid memory, basic UI.

## L3 — Agent Platform Builder
**Scope**: modular user-facing agent platform.  
**Infra**: LangGraph orchestration; Celery + Redis for async; Next.js UI; FastAPI gateway.  
**Auth**: Supabase or Clerk; JWT on every call; per-user/per-tool rate limits.  
**Data**: Postgres; **pgvector** required; S3-compatible storage (Supabase Storage OK).  
**AI**: tool policy control; role-scoped tools.  
**Observability**: central JSON logs with trace id; basic error/latency metrics.  
**Security**: **trigger scaffolds** for auth, queue, vector, external APIs/webhooks, payments, file uploads, secrets/config, admin console. Mark `security_review_required=true`.  
**Routing defaults**:  
- **≤2 files** → **DevBot** (file-scoped patches, integrations, safe restructures).  
- **≥3 files** or **pattern-wide** → **AI IDEs (Cursor, Claude Code)** (multi-file scaffolds/refactors).  
- If unclear, **clarify** before routing.  
**Exit → L4**: multi-tenant (RLS), billing, quotas, dashboards, stable queue.

## L4 — SaaS Infra Architect
**Scope**: production SaaS. Multi-tenant. Paid plans.  
**Infra**: Supabase **RLS** on all tables; FastAPI behind Traefik/Nginx (JWT verify + trace headers); robust queue (Celery retries; DLQ via Redis Streams or move to Temporal if required); feature flags; staging + prod.  
**Auth**: org roles (admin/editor/viewer); plan-based rate caps. SSO/SCIM optional; required when enterprise lands.  
**Data**: tuned Postgres (indexes, migrations); vector at scale (batch embeds, dedup).  
**AI**: model abstraction (swap GPT/Claude/Mistral).  
**Observability**: Prometheus + Grafana; Sentry; uptime checks; OTel tracing with Collector + Tempo/Jaeger.  
**Security**: enforcement; CI/CD gates; code scan; audit logging; signed webhooks; incident runbook.  
**Billing**: Stripe metered usage; quotas enforced at gateway.  
**Exit → L5**: multi-region, incident playbooks, product analytics, cost tracking.

## L5 — AI Product Architect
**Scope**: market-grade product; differentiated UX; defensible IP.  
**Infra**: multi-region (start `us-east-1`, `eu-west-1`); autoscaling workers.  
**Auth**: enterprise features as needed (SSO, SCIM, audit export).  
**Data**: lifecycle policies; retention/PII controls; tenant export/deletion.  
**AI**: tuned agents where ROI exists (fine-tunes, LoRA via vLLM if on-prem).  
**Observability**: product analytics (activation/retention); cost per task/tenant.  
**Security**: continuous reviews; pen-test schedule; playbooks.  
**GTM**: clear ICP; usage pricing + roles; public demos/docs.  
**Exit**: top level; future growth = product lines.

---

## Hard Gates (Level Boundaries)
- **L2 → L3**: async queue live; vector enabled; Next.js UI shipped; per-user rate limits on.  
- **L3 → L4**: multi-tenant with **RLS** + billing + quotas + observability dashboards.  
- **L4 → L5**: multi-region + incident playbooks + product analytics + cost tracking.

## Upgrade Triggers (numeric)
- **Queue saturation**: p95 queue wait `>1500 ms` for **≥10 min** (L3); `>1000 ms` for **≥10 min** (L4+).  
- **API cost spike**: `>30%` over budget **3 consecutive days** or `>20%` **7 days**.  
- **Auth scope creep**: SSO/SCIM request ⇒ **bump to L4**.  
- **Concurrent tenants** thresholds: L2 ≤100, L3 ≤1k, L4 ≤10k, L5 >10k.  
- Any security escalation ⇒ enqueue **SecurityOpsArchitect** milestone (`security_review_required=true`).

## Routing Exceptions
- **DevBot on ≥3 files** allowed only for **trivial same-module diffs** (renames/import fixes). **Document exception**.  
- **AI IDE on 1–2 files** allowed for **new scaffold/pattern refactor**. **Document exception**.  
- Overrides require **explicit user approval**.

## Planner Usage Rules
- Classify level **at start** of planning.  
- If mixed signals, pick **higher level** and add a **scope-reduction** task.  
- Attach **mandatory milestones** for missing items per level.  
- Before emitting tasks, run CVL and follow `06_task_queue_emission.md`.

## Data Governance
- **PII in production ⇒ minimum L4** posture (RLS, audit logs, quotas). Dev/staging must use masked data.  
- **RPO/RTO**: L2 `24h/24h`; L3 `12h/4h`; L4 `1h/1h`; L5 `15m/15–30m`.  
- **Retention defaults**: dev logs 7d, staging 30d, prod 90d; user data 365d (configurable).

## Rate Limits & Quotas
- **L3 defaults**: per-user **60 req/min**; per-tool **30 req/min**; burst **2× for 10 s**.  
- **L4 plans (example)**: Free **50 tasks/mo**, Pro **500**, Team **5k**, overage **$0.005/task**. Enforce at gateway.

## Observability & Monitoring
- Prefer **events over polling**. Sources: queue events, deploy webhooks, Stripe webhooks, vector indexing events, CI/CD status.  
- Alerts: error rate `>2%` for 5 min (L3); `>1%` for 5 min (L4/L5); p95 over SLA for 10 min; cost spikes per rules above.  
- See `07_monitoring_and_adaptation.md` for adaptation flow.

## Billing & Packaging (L4+)
- Plans: **Free** and **Paid** by default.  
- Metering unit: **task** (primary). Track **tokens** for analysis.  
- Quota breach grace: **48h** read-only or reduced throughput; daily notify.

## Tenancy Model
- Row-level multi-tenant with **org-scoped workspaces**.  
- Cross-tenant checks: API layer (org_id from JWT), DB **RLS on every table**, storage paths scoped per org.

## Migration & Compatibility
- **L2→L3 DB**: Alembic migrations; zero-downtime phased deploy.  
- **Vector swap**: abstract via **vector DAO**; tolerate pgvector ⇄ Qdrant/Chroma.  
- **Queue swap**: adapter interface; Celery ⇄ Temporal feasible with stable job contract.

## Routing Context (Downstream)
- **DevBot**: file-scoped patches, ≤2-file diffs.  
- **AI IDEs (Cursor, Claude Code)**: multi-file scaffolds, ≥3-file diffs, pattern refactors.  
- If unclear, **clarify** before routing.

## Cross References
- Phases: `04_phase_protocols.md`  
- Inputs: `05_input_processing.md`  
- Task emission rules/schema: `06_task_queue_emission.md`  
- Monitoring/adaptation: `07_monitoring_and_adaptation.md`  
- Security triggers/templates: `08_security_scaffolding.md`, `09_security_milestone_templates.md`
