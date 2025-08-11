11_tooling_reference.md
Purpose: Provide the System Architect with a quick, build-level-aligned reference for recommended tooling, libraries, and services. Optimized for precision selection without vendor lock-in.

Core Principles
Level-Gated — Only suggest tools appropriate for the current build level (L1–L5).

Subsystem-Aligned — Group by architectural subsystem for clarity.

Vendor-Agnostic Defaults — Recommend open-source or broadly supported options first.

Security & Observability Included — Every recommendation assumes baseline security/monitoring.

Tooling by Subsystem & Build Level
1. Authentication & RBAC
Level	Tools / Services	Notes
L1–L2	Supabase Auth, Firebase Auth	Simple, managed, no custom RBAC logic.
L3	Keycloak, Auth0	Full RBAC, social logins, enterprise SSO readiness.
L4–L5	Ory Hydra/Kratos, AWS Cognito	Multi-tenant, SSO, fine-grained permissions with audit logging.

2. Database & Storage
Level	Tools / Services	Notes
L1–L2	Supabase Postgres, SQLite	Basic schema, low scale.
L3	Postgres + pgvector, MySQL	Vector indexing for AI, RLS supported.
L4–L5	AWS RDS/Aurora, CockroachDB	Multi-region, failover, high concurrency.

3. Vector Stores (AI Subsystems)
Level	Tools / Services	Notes
L2–L3	pgvector, Weaviate	In-DB vector support or simple API vector DB.
L4–L5	Pinecone, Milvus	Dedicated scaling vector services, hybrid search.

4. Queue & Job Scheduling
Level	Tools / Services	Notes
L1–L2	Redis Queue (RQ), Celery (basic)	Simple task queues, in-process workers.
L3	RabbitMQ, Kafka (small cluster)	Durable, pub/sub workflows.
L4–L5	AWS SQS, Google Pub/Sub, Kafka (enterprise)	High throughput, global distribution.

5. Observability & Monitoring
Level	Tools / Services	Notes
L1–L2	Sentry, UptimeRobot	Basic error tracking and uptime checks.
L3	Prometheus + Grafana	Metrics, dashboards.
L4–L5	Datadog, New Relic, AWS CloudWatch	Full APM, logs, metrics, tracing at scale.

6. API & Integration Layer
Level	Tools / Services	Notes
L1–L2	FastAPI, Flask	Simple REST APIs.
L3	FastAPI + Pydantic + Async Workers	Async scaling, type validation.
L4–L5	GraphQL (Apollo Federation), gRPC	High-scale service mesh, federated schema.

7. Security & Compliance
Level	Tools / Services	Notes
L1–L2	OWASP ZAP (manual), dotenv for secrets	Simple local scanning & env protection.
L3	Open Policy Agent (OPA), Trivy	Automated IaC & container scanning.
L4–L5	AWS Macie, Prisma Cloud, Vault	Enterprise secrets mgmt, PII detection, compliance reporting.

8. CI/CD & DevOps
Level	Tools / Services	Notes
L1–L2	GitHub Actions (basic), Railway.app	Lightweight pipelines.
L3	GitHub Actions + Docker build pipeline	Parallel jobs, containerized builds.
L4–L5	ArgoCD, GitLab CI, AWS CodePipeline	Multi-env deploys, GitOps patterns.

9. Frontend / UI
Level	Tools / Services	Notes
L1–L2	Next.js + TailwindCSS	Simple SSR apps.
L3	Next.js + SWR/React Query + Component Libs	Data sync, design systems.
L4–L5	Micro-frontend frameworks, CDN edge caching	High concurrency & global performance.

Usage Rules
Match Tool to Level — Don’t over-engineer at L1–L2.

Security First — Always pair subsystem tools with baseline security measures.

Upgrade Milestones — Level jumps should trigger matching tool upgrades.

Vendor Independence — Prefer tools with migration paths.

Cross-References
02_build_level_protocols.md

03_subsystem_map_reference.md

08_security_scaffolding.md