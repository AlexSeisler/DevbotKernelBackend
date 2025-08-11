# 03_subsystem_map_reference.md

**Purpose**: detection rules, risk triggers, and default stacks per subsystem. Used for file-level tagging, scoped retrieval, and planning.

## How to use
- Tag at **file level** using the indicators below.  
- In monorepos (`apps/`, `services/`, `libs/`, `packages/`), **directory-level tags propagate to children** unless a child’s indicators override.  
- `/nodes?repo_id=&subsystem=…` resolves via `file_subsystem_map → semantic_nodes`.  
- When **risk_tags** hit, enqueue scaffolds (see `08_security_scaffolding.md`, `09_security_milestone_templates.md`).  
- Detection thresholds and scoring are **backend-controlled**.

## Detection schema (per subsystem)
- **Indicators**: `python_imports[]`, `js_imports[]`, `paths[]`, `filenames[]`, `keywords[]`
- **Risk tags**: drive security milestones; mark `security_review_required=true` for blocking tags
- **Default stack**: **L3 defaults**, **L4+ upgrades** (keep complexity level-appropriate)
- **Example filters**: stringified JSON for `/query`
- **Notes**: edge cases

## Canonical query ops and return fields
- Filter ops: `__like`, `__contains`, `__in`, `__regex`, equality  
- Return: `file_path, node_type, indicators_hit[], score, subsystem[]`

---

## auth
**What**: authentication, authorization, RBAC, session/JWT handling.  
**Indicators**
- `python_imports`: `fastapi.security`, `authlib`, `jwt`, `pyjwt`, `passlib`, `bcrypt`, `supabase`
- `js_imports`: `next-auth`, `@clerk/nextjs`, `jsonwebtoken`, `oauth`, `bcryptjs`
- `paths`: `auth/`, `routes/auth/`, `security/`, `policies/`
- `filenames`: `auth.py`, `rbac.py`, `permissions.py`, `oauth.py`, `jwt_utils.py`
- `keywords`: `RBAC`, `scopes`, `roles`, `login`, `refresh_token`
**Risk tags**: `external_login` (B), `jwt_issue_verify` (B), `password_storage` (B), `rbac_policy` (B), `rate_limit_needed` (B), `oauth_callback` (B), `session_fixation` (B)  
**Default stack**: L3 Supabase/Clerk + JWT + gateway rate limits; L4+ org RBAC, SSO/SCIM, audit logs, RLS everywhere  
**Example filter**
```json
{"repo_id":"<owner/repo>","subsystem":"auth"}
Notes: token helpers often live in utils/—scan filenames outside /auth.

api_gateway
What: public API surface, routing, middleware, versioning.
Indicators

python_imports: fastapi, starlette.middleware, pydantic

js_imports: next/server, express, hono

paths: routers/, api/, gateway/, middleware/

filenames: main.py, app.py, router.py, middleware.py, openapi.yaml

keywords: @app.get, @router, CORS, version, x-trace-id
Risk tags: rate_limit_needed (B), cors_policy (B), input_validation (B), auth_propagation (B), api_versioning (N)
Default stack: L3 FastAPI gateway + simple caps; L4+ behind Traefik/Nginx, JWT verify, trace headers, plan quotas
Example filter

json
Copy
Edit
{"repo_id":"<owner/repo>","paths_like":["api/","routers/","gateway/"]}
frontend_ui
What: Next.js/React UI, dashboards, agent UIs.
Indicators

js_imports: next, react, @tanstack/react-query, next-auth, shadcn/ui, tailwindcss

paths: app/, pages/, components/, hooks/

filenames: _app.tsx, layout.tsx, page.tsx, middleware.ts
Risk tags: csrf (B), unsafe_html (B), exposes_secrets (B), tenant_context_missing (B)
Default stack: L3 Next.js + SDK-based auth; L4+ org switcher, role-guarded routes, usage dashboards
Example filter

json
Copy
Edit
{"repo_id":"<owner/repo>","paths_like":["app/","pages/","components/"]}
database
What: relational models, migrations, access layer.
Indicators

python_imports: sqlalchemy, psycopg, alembic, supabase

js_imports: drizzle-orm, prisma

paths: models/, db/, migrations/, repositories/

filenames: models.py, schema.sql, alembic.ini, repository.py
Risk tags: rls_required (B), pii_storage (B), missing_index (N), unencrypted_at_rest (B)
Default stack: L3 Postgres + basic indexing; L4+ RLS, disciplined migrations, backup/restore, lifecycle policies
Example filter

json
Copy
Edit
{"repo_id":"<owner/repo>","paths_like":["models/","db/","migrations/"]}
Notes: detect ALTER POLICY/USING(...) for RLS presence.

vector
What: embeddings, similarity search, RAG plumbing.
Indicators

python_imports: pgvector, chromadb, qdrant_client, weaviate, faiss, langchain.vectorstores

js_imports: @qdrant/js-client-rest, weaviate-ts-client

paths: vector/, memory/, embeddings/, rag/

filenames: vector_store.py, embed.py, retriever.py
Risk tags: pii_in_embeddings (B), leaky_rag (B), stale_index (N), unbounded_cost (N)
Default stack: L3 pgvector; L4+ pgvector batching/dedup or managed Qdrant/Weaviate, TTL maintenance
Example filter

json
Copy
Edit
{"repo_id":"<owner/repo>","paths_like":["vector/","memory/","embeddings/"]}
queue
What: async tasks, workers, retries, DLQ, schedulers.
Indicators

python_imports: celery, kombu, rq, redis

js_imports: bullmq, bull

paths: workers/, tasks/, queue/, schedulers/, cron/

filenames: celery.py, tasks.py, worker.py
Risk tags: idempotency_missing (B), retry_policy_missing (B), dead_letter_absent (B), poison_message (B)
Default stack: L3 Celery + Redis; L4+ DLQ, dedup keys, quotas; consider Temporal when workflows complex
Example filter

json
Copy
Edit
{"repo_id":"<owner/repo>","paths_like":["workers/","tasks/","queue/"]}
ai
What: LLM orchestration, tool policies, prompts, graphs.
Indicators

python_imports: langgraph, langchain, openai, anthropic, mistralai, transformers

js_imports: langchain, openai, @anthropic-ai/sdk

paths: agents/, prompts/, tools/, orchestrator/

filenames: graph.py, planner.py, tool_registry.py, prompt_*.md
Risk tags: prompt_injection_surface (B), tool_abuse (B), cost_runaway (N), privacy_leak (B)
Default stack: L3 LangGraph + tool schemas (OpenAI/Anthropic); L4+ model abstraction, per-tool quotas, tracing, red-team harness
Example filter

json
Copy
Edit
{"repo_id":"<owner/repo>","paths_like":["agents/","prompts/","orchestrator/"]}
observability
What: logs, metrics, tracing, error reporting, auditing.
Indicators

python_imports: loguru, structlog, sentry_sdk, prometheus_client, opentelemetry

js_imports: @sentry/nextjs, prom-client, @opentelemetry/api

paths: logging/, metrics/, tracing/, monitoring/, audit/

filenames: logging.py, tracing.py, metrics.py
Risk tags: no_trace_id (B), no_error_alerts (B), no_latency_metrics (N), no_audit_logs (B)
Default stack: L3 JSON logs + trace id; L4+ Prometheus+Grafana, Sentry, OTel Collector
Example filter

json
Copy
Edit
{"repo_id":"<owner/repo>","paths_like":["logging/","metrics/","tracing/"]}
infra
What: deployment, containers, gateways, IaC.
Indicators

Files: Dockerfile, docker-compose.yml, Procfile, fly.toml, render.yaml, nginx.conf, traefik.yml, terraform/*.tf, helm*/

paths: deploy/, infra/, k8s/

keywords: autoscaling, healthcheck, reverse_proxy
Risk tags: no_health_checks (B), no_rollback (B), secret_in_image (B), missing_resource_limits (B), no_feature_flags (N)
Default stack: L3 Docker + PaaS (Render/Railway/Fly); L4+ Traefik/Nginx, Terraform (Helm if k8s), blue/green or canary
Example filter

json
Copy
Edit
{"repo_id":"<owner/repo>","filenames":["Dockerfile","fly.toml","traefik.yml","render.yaml"]}
testing
What: unit/integration, e2e, load/security tests.
Indicators

python_imports: pytest, unittest, locust

js_imports: jest, vitest, playwright, cypress, k6

paths: tests/, __tests__/, e2e/

filenames: test_*.py, *.spec.ts, *.e2e.ts
Risk tags: no_auth_tests (B), no_api_contract_tests (B), no_load_tests (N), no_security_tests (B), auth_e2e_missing (B)
Default stack: L3 unit + integration + smoke e2e; L4+ API contract, multi-tenant e2e, load tests with p95 SLOs
Example filter

json
Copy
Edit
{"repo_id":"<owner/repo>","paths_like":["tests/","__tests__/","e2e/"]}
storage
What: file/object storage, uploads, media, dataset blobs.
Indicators

python_imports: boto3, supabase.storage

js_imports: @aws-sdk/client-s3, @supabase/storage-js

paths: storage/, uploads/, media/

filenames: s3_client.py, storage_service.py
Risk tags: public_bucket (B), unscoped_paths (B), pii_in_public (B), no_av_scan (B)
Default stack: L3 Supabase Storage/S3-compatible; L4+ signed URLs, per-tenant prefixes, AV scan
Example filter

json
Copy
Edit
{"repo_id":"<owner/repo>","paths_like":["storage/","uploads/","media/"]}
payments
What: billing, subscriptions, metering.
Indicators

python_imports: stripe

js_imports: @stripe/stripe-js, stripe

paths: billing/, payments/, webhooks/stripe/

filenames: stripe_webhook.py, billing_service.py
Risk tags: webhook_unauthenticated (B), plan_quota_missing (B), inaccurate_metering (B), pci_scope_confusion (N), quota_bypass (B)
Default stack: L4+ Stripe subs + metered usage; signed webhook verify; quotas at gateway
Example filter

json
Copy
Edit
{"repo_id":"<owner/repo>","paths_like":["billing/","payments/","webhooks/stripe/"]}
email_notifications
What: transactional emails, notifications, templates.
Indicators

python_imports: smtplib, boto3 (SES), sendgrid

js_imports: @sendgrid/mail, resend, postmark

paths: emails/, notifications/, templates/

filenames: mailer.py, email_service.py, notify_worker.py
Risk tags: template_injection (B), spammable_route (N), secrets_in_templates (B), pii_leak_email (B)
Default stack: L3 provider SDK + rate caps; L4+ signed webhook status, bounce handling, per-tenant templates

analytics_product
What: product analytics, events, funnels, retention.
Indicators

js_imports: @segment/analytics-next, posthog-js

python_imports: server-side Segment/PostHog clients

paths: analytics/, events/

filenames: analytics_client.ts, event_bus.py
Risk tags: pii_in_events (B), missing_consent (B), event_spam (N)
Default stack: L3 client events + server relay; L4+ event schemas, consent gating, retention dashboards

feature_flags
What: runtime flags, kill switches, staged rollouts.
Indicators

python_imports: openfeature

js_imports: @openfeature/web-sdk, unleash-client

paths: flags/, feature_flags/

filenames: flags.ts, feature_gate.py
Risk tags: no_kill_switch (B), flag_sprawl (N)
Default stack: L4+ OpenFeature + Unleash; LaunchDarkly optional

webhooks_integrations
What: inbound/outbound webhooks, partner integrations.
Indicators

paths: integrations/, webhooks/

filenames: webhook_handler.py, integration_service.py

keywords: signature, secret, retry
Risk tags: webhook_unauthenticated (B), no_replay_protection (B), quota_bypass (B)
Default stack: L3 basic handlers; L4+ signed verify, replay protection, retries, quotas

search_indexing
What: text search, indexing pipelines.
Indicators

python_imports: pg_trgm, elasticsearch, whoosh

js_imports: @elastic/elasticsearch

paths: search/, indexer/

filenames: search_service.py, index_tasks.py
Risk tags: pii_indexed (B), unbounded_index_growth (N)
Default stack: L3 Postgres trigram/full-text; L4+ managed search or dedicated service with lifecycle controls

admin_console
What: admin-only surfaces, ops tools.
Indicators

paths: admin/, console/, ops/

filenames: admin.py, admin_panel.tsx

keywords: superuser, staff_only
Risk tags: privilege_escalation (B), no_audit_logs (B), exposes_secrets (B)
Default stack: L3 guarded routes + basic audit; L4+ full audit logs, approvals, break-glass flow

Security trigger matrix (subset)
auth: external_login, jwt_issue_verify, rbac_policy → STRIDE + rate limits (blocking)

api_gateway: input_validation, cors_policy → schema validation + strict CORS (blocking)

queue: idempotency_missing, retry_policy_missing → add DLQ + retries (blocking)

vector: pii_in_embeddings, leaky_rag → redact/segment, TTL (blocking)

observability: no_trace_id, no_error_alerts → tracing + alerts (non-blocking, required by L4)

payments: webhook_unauthenticated, quota_bypass → signed verify + quotas (blocking)

admin_console: privilege_escalation, no_audit_logs → role gates + audit (blocking)

Blocking tags auto-mark security_review_required=true.

Example /query payloads (stringified JSON)
json
Copy
Edit
{"table":"file_subsystem_map","filters":"{\"repo_id\":\"<owner/repo>\",\"subsystem\":\"queue\"}","limit":200}
json
Copy
Edit
{"table":"semantic_nodes","filters":"{\"repo_id\":\"<owner/repo>\",\"file_path__like\":\"%/auth/%\"}","l
Cross-references
Security scaffolding: 08_security_scaffolding.md, 09_security_milestone_templates.md

Task emission: 06_task_queue_emission.md

Phase protocols: 04_phase_protocols.md