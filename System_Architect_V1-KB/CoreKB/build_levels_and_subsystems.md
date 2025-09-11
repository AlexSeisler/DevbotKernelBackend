# build_levels_and_subsystems.md (v1.1)

## Purpose
Define build Levels (L1–L5) and what each subsystem contributes per phase. **Backend handles detection**; this file explains **what** and **when**. Security here = **scaffold** (flag & schedule), not enforcement.

---

## Levels ↔ Stages (pillars inline)

| Level | Stage name | Primary goal | Auth (pillar) | Memory (DB + Vector/RAG) | Infra (gateway, queue, deploy) | Observability |
|---|---|---|---|---|---|---|
| **L1** | Concept Prototyper | Local demo, fast iteration | None / dev-only | SQLite or local PG; no vector | Single FastAPI/script; local run | Console prints |
| **L2** | Orchestration Prototyper | Single-user cloud demo | Supabase JWT (basic) | Supabase PG; optional pgvector trial | FastAPI on PaaS; no queue required | JSON logs |
| **L3** | Agent Platform Builder | User-ready agent platform | Supabase/Clerk + rate limits | Postgres + **pgvector**; basic RAG | FastAPI gateway; **Celery+Redis**; Next.js UI | JSON logs + **trace_id** |
| **L4** | SaaS Infra Architect | Multi-tenant, quotas, billing | Org RBAC; SSO optional; **RLS** | Tuned PG + vector at scale; retention | Gateway behind Traefik/Nginx; quotas; **Stripe**; feature flags; webhooks | **Prometheus + Grafana + Sentry + OTel** |
| **L5** | AI Product Architect | Market-ready, multi-region | Enterprise SSO/SCIM | Data lifecycle & exports; vertical RAG | Multi-region deploy; rollout policies | Product analytics + incident playbooks |

**Notes**
- **Classify higher on conflict**; level escalation needs user approval.
- **L4 scaffolds allowed at L3** to reduce rework — mark `level_scaffold:true` (e.g., RLS design note, payments spec).
- **Always-emit set at L3+** (see below) ensures correctness, recovery, analytics.

---

## Always-emit set (ensure these appear in plans at L3+)
- **Correctness:** `idempotency_keys` on **write** endpoints (gateway).
- **Data hygiene:** `resume_normalization_gate` (or equivalent ingress validator) before persistence.
- **State model:** `app_state_machine` (finite states + API enforcement).
- **Resilience:** `db_backups` (daily + restore drill).
- **Acquisition:** `source_adapters` (≥2 sources, throttle/robots policy).
- **Analytics:** `product_analytics` events for the **North Star KPI**.
- **Versioning:** `gateway_versioning` (version path + error envelope).

DAG wiring hints (apply at P3):
- `ui_e2e →` **gateway_validation**, **db_schema**, **storage_uploads**, **vector_pipeline**, **ai_matching**.
- `product_analytics → observability`
- `db_backups → observability` and `db_backups → infra`
- `app_state_machine → api_gateway` and `app_state_machine → frontend_ui`

---

## Subsystems — purpose & phase hooks (P1–P5)

Format: **Purpose • Inputs • Phase hooks • Outputs • Required gates/edges**

### auth
- **Purpose:** identity, RBAC, session/JWT.
- **Inputs:** provider, roles, tenancy.
- **Hooks:** **P1** confirm provider/roles → **P2** RBAC, guards, rate caps (L3+) → **P3** before public endpoints → **P4** guards/middleware → **P5** audit/auth KPIs.
- **Outputs:** auth plan, RBAC matrix, guard tasks.
- **Required:** set `security_review_required:true` for guards/token/SSO.

### api_gateway
- **Purpose:** public API surface, routing, versioning.
- **Inputs:** surfaces, quotas, version policy.
- **Hooks:** **P1** enumerate → **P2** validation, **idempotency_keys** (L3), rate limits, versioning → **P3** before consumers → **P4** schema checks/headers → **P5** latency/error actions.
- **Outputs:** gateway policy, validation/idempotency/versioning tasks.
- **Required:** `security_review_required:true` on write paths; DAG edges from `app_state_machine`.

### frontend_ui
- **Purpose:** UX shell, org switching, dashboards.
- **Inputs:** routes, roles, views.
- **Hooks:** **P1** scope → **P2** shell/guards → **P3** per deps → **P4** pages/components/guards → **P5** UX issue feed.
- **Outputs:** UI shell plan, guarded routes.
- **Required edges:** depend on gateway/db/storage/vector/ai (see wiring hints).

### database
- **Purpose:** relational schema, migrations, access layer.
- **Inputs:** entities, retention, tenancy, PII.
- **Hooks:** **P1** entities/sensitivity → **P2** schema/migrations (RLS at L4; **ok as `level_scaffold` at L3**) → **P3** indexes → **P4** DDL/DML tasks → **P5** slow-query/growth actions.
- **Outputs:** schema plan, migrations, index plan.
- **Required:** `db_backups` (daily + drill); mark data-access changes as `security_review_required:true`.

### vector
- **Purpose:** embeddings, similarity, RAG.
- **Inputs:** collections, chunking, TTL.
- **Hooks:** **P1** need/scope → **P2** pgvector + retriever → **P3** batch/index windows → **P4** embedder/retriever tasks → **P5** staleness/TTL checks.
- **Outputs:** RAG plan, embed jobs.

### queue
- **Purpose:** async work, retries, idempotency.
- **Inputs:** job types, SLAs, priorities.
- **Hooks:** **P1** long jobs → **P2** workers/retry/DLQ → **P3** before producers → **P4** task defs/policies → **P5** backlog/saturation actions.
- **Outputs:** worker plan, policies.

### ai
- **Purpose:** LLM orchestration, tools, policies.
- **Inputs:** models, tools, cost caps.
- **Hooks:** **P1** provider/tools → **P2** graphs/guardrails → **P3** after context ready → **P4** tool registry/graph nodes → **P5** cost/quality reviews.
- **Outputs:** graph plan, tool tasks.

### observability
- **Purpose:** logs, metrics, tracing, alerts.
- **Inputs:** KPIs, SLOs.
- **Hooks:** **P1** signals/targets → **P2** logs + **trace_id** (L3) and metrics+alerts (L4) → **P3** before scale tests → **P4** exporters/dashboards → **P5** alert tuning.
- **Outputs:** obs plan, dashboards.
- **Required edges:** `product_analytics → observability`, `db_backups → observability`.

### infra
- **Purpose:** deploy, gateways, rollout, IaC.
- **Inputs:** hosting, regions, rollout strategy.
- **Hooks:** **P1** platform/regions → **P2** gateway/deploy/IaC (L4+) → **P3** stage/canary → **P4** Docker/gateway/IaC tasks → **P5** capacity/rollback.
- **Outputs:** deploy plan, gateway config.
- **Required edges:** `db_backups → infra`.

### testing
- **Purpose:** unit/integration/e2e/load/contract.
- **Inputs:** critical paths, SLAs, contracts.
- **Hooks:** **P1** lanes → **P2** suites → **P3** contract/load pre-GA → **P4** tests + CI → **P5** regression/load.
- **Outputs:** test plan, suites.

### storage
- **Purpose:** object/file storage, uploads.
- **Inputs:** buckets, prefixes, signing rules.
- **Hooks:** **P1** provider/scope → **P2** signed URLs/prefixes → **P3** scan cadence → **P4** handlers/policies → **P5** leakage checks.
- **Outputs:** storage policy, handlers.
- **Required:** mark upload ingress as `security_review_required:true`.

### payments (L4+)
- **Purpose:** subscriptions, metering, quotas.
- **Inputs:** plans, units, webhooks.
- **Hooks:** **P1** pricing → **P2** Stripe + quotas → **P3** before premium features → **P4** webhook verify + quota checks → **P5** revenue/abuse review.
- **Outputs:** billing plan, enforcement tasks.
- **Required:** `security_review_required:true`; at L3 mark spec as `level_scaffold:true`.

### email_notifications
- **Purpose:** transactional emails, alerts.
- **Inputs:** providers, templates, rates.
- **Hooks:** **P1** events → **P2** provider/templates → **P3** throttle windows → **P4** senders/templates/caps → **P5** bounce/complaint actions.
- **Outputs:** notification plan, templates.

### analytics_product (L5)
- **Purpose:** product analytics, funnels.
- **Inputs:** taxonomy, masking rules.
- **Hooks:** **P1** events → **P2** SDK + masking → **P3** dashboards staging → **P4** dashboards/alerts → **P5** adoption/retention actions.
- **Outputs:** analytics plan, dashboards.
- **Required edges:** depend on **observability**.

### feature_flags (L4+)
- **Purpose:** safe rollouts, experiments.
- **Inputs:** flags, owners, defaults.
- **Hooks:** **P1** risky changes → **P2** flag milestones → **P3** gating order → **P4** wrap changes → **P5** cleanup.
- **Outputs:** flag plan, wrappers.

### webhooks_integrations (L4+)
- **Purpose:** inbound/outbound partner hooks.
- **Inputs:** partners, schemas, retries.
- **Hooks:** **P1** contracts → **P2** signatures/idempotency → **P3** before partner tests → **P4** verify/retry tasks → **P5** failure/latency actions.
- **Outputs:** integration plan, verify tasks.
- **Required:** `security_review_required:true`.

### search_indexing (L5)
- **Purpose:** app search/full-text.
- **Inputs:** fields, refresh rules.
- **Hooks:** **P1** scope → **P2** FTS/engine → **P3** refresh cadence → **P4** indexers/queries → **P5** quality/latency actions.
- **Outputs:** search plan, index jobs.

### admin_console (L4+)
- **Purpose:** privileged admin tools/routes.
- **Inputs:** roles, audit needs.
- **Hooks:** **P1** capabilities → **P2** RBAC + audit log milestones → **P3** before ops → **P4** admin routes/audit trails → **P5** audit reviews.
- **Outputs:** admin plan, audit tasks.
- **Required:** `security_review_required:true`.

---

## Phase references
- **P1** confirm subsystem scope & risks; set level.
- **P2** create/upgrade milestones per subsystem aligned to level (**include always-emit set**).
- **P3** order; place security scaffolds before exposure; apply wiring hints.
- **P4** emit atomic tasks and route by granularity; include required task fields.
- **P5** observe KPIs and adjust plan.

**Cross-refs:** `mission_and_role.md`, `phase_execution.md`, `routing_and_security.md`.
