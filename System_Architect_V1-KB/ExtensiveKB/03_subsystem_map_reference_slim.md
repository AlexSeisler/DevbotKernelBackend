# 03_subsystem_map_reference.md — Lean

**Purpose**: fast detection rules, risk triggers, and default stacks per subsystem for tagging, scoped retrieval, and planning.

## Use
- Tag at **file level** from indicators.  
- Monorepo roots: `apps/`, `services/`, `libs/`, `packages/`. **Parent tags propagate** unless child overrides.  
- Resolution via `file_subsystem_map → semantic_nodes` with `/repo-ingestion/nodes`.  
- **Blocking** risk tags auto-mark `security_review_required=true` and enqueue scaffolds (`08/09`).  
- Scoring/thresholds are **backend-controlled**.

## Detection schema
- **Indicators**: `python_imports[] | js_imports[] | paths[] | filenames[] | keywords[]`  
- **Risk tags**: `(B)=blocking, (N)=non-blocking`  
- **Default**: **L3 defaults**, **L4+ upgrades** only where needed  
- **Query ops**: `__like`, `__contains`, `__in`, `__regex`, `=`  
- **Return**: `file_path, node_type, indicators_hit[], score, subsystem[]`

---

### auth
**IND** paths:`auth/|security/|policies/` files:`auth.py|rbac.py|jwt*` imports:`fastapi.security|jwt|clerk|supabase` keywords:`roles|scopes`  
**RISK** `external_login`(B), `jwt_issue_verify`(B), `password_storage`(B), `rbac_policy`(B), `rate_limit_needed`(B)  
**DEFAULT** L3 Supabase/Clerk + JWT + caps; L4+ org RBAC, SSO/SCIM, audit, RLS

### api_gateway
**IND** paths:`api/|routers/|gateway/|middleware/` files:`main.py|router.py|middleware.py|openapi.yaml` keywords:`CORS|x-trace-id|version`  
**RISK** `input_validation`(B), `cors_policy`(B), `rate_limit_needed`(B), `auth_propagation`(B), `api_versioning`(N)  
**DEFAULT** L3 FastAPI gateway + caps; L4+ Traefik/Nginx, JWT verify, trace headers, plan quotas

### frontend_ui
**IND** paths:`app/|pages/|components/|hooks/` files:`_app.tsx|layout.tsx|page.tsx|middleware.ts`  
**RISK** `csrf`(B), `unsafe_html`(B), `exposes_secrets`(B), `tenant_context_missing`(B)  
**DEFAULT** L3 Next.js + SDK auth; L4+ org switcher, route guards, usage dashboards

### database
**IND** paths:`models/|db/|migrations/|repositories/` files:`models.py|schema.sql|alembic.ini`  
**RISK** `rls_required`(B), `pii_storage`(B), `missing_index`(N), `unencrypted_at_rest`(B)  
**DEFAULT** L3 Postgres + indexes; L4+ RLS, disciplined migrations, backup/restore, lifecycle

### vector
**IND** paths:`vector/|memory/|embeddings/|rag/` files:`vector_store.py|embed.py|retriever.py`  
**RISK** `pii_in_embeddings`(B), `leaky_rag`(B), `stale_index`(N), `unbounded_cost`(N)  
**DEFAULT** L3 pgvector; L4+ batching/dedup or managed Qdrant/Weaviate + TTL

### queue
**IND** paths:`workers/|tasks/|queue/|schedulers/|cron/` files:`celery.py|tasks.py|worker.py`  
**RISK** `idempotency_missing`(B), `retry_policy_missing`(B), `dead_letter_absent`(B), `poison_message`(B)  
**DEFAULT** L3 Celery+Redis; L4+ DLQ, dedup keys, quotas; Temporal if workflows complex

### ai
**IND** paths:`agents/|prompts/|tools/|orchestrator/` files:`graph.py|planner.py|tool_registry.py|prompt_*.md`  
**RISK** `prompt_injection_surface`(B), `tool_abuse`(B), `cost_runaway`(N), `privacy_leak`(B)  
**DEFAULT** L3 LangGraph + tool schemas; L4+ model abstraction, per-tool quotas, tracing, red-team

### observability
**IND** paths:`logging/|metrics/|tracing/|monitoring/|audit/` files:`logging.py|tracing.py|metrics.py`  
**RISK** `no_trace_id`(B), `no_error_alerts`(B), `no_latency_metrics`(N), `no_audit_logs`(B)  
**DEFAULT** L3 JSON logs + trace id; L4+ Prometheus+Grafana, Sentry, OTel Collector

### infra
**IND** files:`Dockerfile|docker-compose.yml|fly.toml|render.yaml|nginx.conf|traefik.yml|terraform/*.tf|helm/**` paths:`deploy/|infra/|k8s/`  
**RISK** `no_health_checks`(B), `no_rollback`(B), `secret_in_image`(B), `missing_resource_limits`(B), `no_feature_flags`(N)  
**DEFAULT** L3 Docker + PaaS; L4+ Traefik/Nginx, Terraform (Helm if k8s), blue/green or canary

### testing
**IND** paths:`tests/|__tests__/|e2e/` files:`test_*.py|*.spec.ts|*.e2e.ts`  
**RISK** `no_auth_tests`(B), `no_api_contract_tests`(B), `no_security_tests`(B), `no_load_tests`(N), `auth_e2e_missing`(B)  
**DEFAULT** L3 unit+integration+smoke; L4+ contract, multi-tenant e2e, load with p95 SLOs

### storage
**IND** paths:`storage/|uploads/|media/` files:`s3_client.py|storage_service.py`  
**RISK** `public_bucket`(B), `unscoped_paths`(B), `pii_in_public`(B), `no_av_scan`(B)  
**DEFAULT** L3 Supabase Storage/S3; L4+ signed URLs, tenant prefixes, AV scan

### payments
**IND** paths:`billing/|payments/|webhooks/stripe/` files:`stripe_webhook.py|billing_service.py`  
**RISK** `webhook_unauthenticated`(B), `quota_bypass`(B), `plan_quota_missing`(B), `inaccurate_metering`(B)  
**DEFAULT** L4+ Stripe subs + metered usage; signed verify; quotas at gateway

### email_notifications
**IND** paths:`emails/|notifications/|templates/` files:`mailer.py|email_service.py|notify_worker.py`  
**RISK** `template_injection`(B), `secrets_in_templates`(B), `pii_leak_email`(B), `spammable_route`(N)  
**DEFAULT** L3 provider SDK + caps; L4+ status webhooks, bounce handling, per-tenant templates

### analytics_product
**IND** paths:`analytics/|events/` files:`analytics_client.ts|event_bus.py`  
**RISK** `pii_in_events`(B), `missing_consent`(B), `event_spam`(N)  
**DEFAULT** L3 client events + server relay; L4+ event schemas, consent gating, retention dashboards

### feature_flags
**IND** paths:`flags/|feature_flags/` files:`flags.ts|feature_gate.py`  
**RISK** `no_kill_switch`(B), `flag_sprawl`(N)  
**DEFAULT** L4+ OpenFeature + Unleash; LaunchDarkly optional

### webhooks_integrations
**IND** paths:`integrations/|webhooks/` files:`webhook_handler.py|integration_service.py` keywords:`signature|secret|retry`  
**RISK** `webhook_unauthenticated`(B), `no_replay_protection`(B), `quota_bypass`(B)  
**DEFAULT** L3 basic handlers; L4+ signed verify, replay protection, retries, quotas

### search_indexing
**IND** paths:`search/|indexer/` files:`search_service.py|index_tasks.py`  
**RISK** `pii_indexed`(B), `unbounded_index_growth`(N)  
**DEFAULT** L3 Postgres trigram/full-text; L4+ managed search or dedicated service with lifecycle

### admin_console
**IND** paths:`admin/|console/|ops/` files:`admin.py|admin_panel.tsx` keywords:`superuser|staff_only`  
**RISK** `privilege_escalation`(B), `no_audit_logs`(B), `exposes_secrets`(B)  
**DEFAULT** L3 guarded routes + basic audit; L4+ full audit logs, approvals, break-glass

---

## Security trigger matrix (subset)
- **auth**: `external_login`, `jwt_issue_verify`, `rbac_policy` → STRIDE + rate limits (**B**)  
- **api_gateway**: `input_validation`, `cors_policy` → schema validation + strict CORS (**B**)  
- **queue**: `idempotency_missing`, `retry_policy_missing` → DLQ + retries (**B**)  
- **vector**: `pii_in_embeddings`, `leaky_rag` → redact/segment, TTL (**B**)  
- **observability**: `no_trace_id`, `no_error_alerts` → tracing + alerts (**N**, L4 required)  
- **payments**: `webhook_unauthenticated`, `quota_bypass` → signed verify + quotas (**B**)  
- **admin_console**: `privilege_escalation`, `no_audit_logs` → role gates + audit (**B**)

**Blocking tags set `security_review_required=true`.**

## Query examples
```json
{"table":"file_subsystem_map","filters":"{\"repo_id\":\"<owner/repo>\",\"subsystem\":\"queue\"}","limit":200}
json
Copy
Edit
{"table":"semantic_nodes","filters":"{\"repo_id\":\"<owner/repo>\",\"file_path__like\":\"%/auth/%\"}","limit":500}
Cross-refs
08_security_scaffolding.md · 09_security_milestone_templates.md · 06_task_queue_emission.md · 04_phase_protocols.md