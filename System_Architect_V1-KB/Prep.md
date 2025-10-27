%% =====================================================
%%  Precision + Personality Lab — Full Architecture Map
%%  Author: System Architect Reference (Internal)
%% =====================================================

graph TD

%% =====================================================
%%  USER & FRONTEND LAYER
%% =====================================================

    subgraph FRONTEND["🌐 FRONTEND — Next.js 15 + Tailwind + Zustand"]
        A1[User Browser]
        A2[Next.js App Router (SSR/SSG Runtime)]
        A3[React Components: Calibration Console / Experiment Studio / Metrics Dashboard]
        A4[Zustand State Stores (UI, Calibrations, Experiments, Metrics)]
        A5[Auth Context Provider (React Context)]
        A6[shadcn/UI Components + lucide-react Icons]
        A7[Framer Motion Animations / Transition Effects]
        A8[TailwindCSS Styling Layer]
        A9[Toast Notification Service]
        A10[Client-Side Supabase Client (Auth & Realtime)]

        %% Interconnections
        A1 -->|HTTP/S| A2
        A2 -->|Hydrates| A3
        A3 --> A4
        A3 --> A5
        A3 --> A9
        A3 --> A6
        A3 --> A7
        A3 --> A8
        A5 -->|Session Context| A10
    end

%% =====================================================
%%  MIDDLEWARE & API LAYER
%% =====================================================

    subgraph MIDDLEWARE["⚙️ MIDDLEWARE — Next.js API Routes / Server Actions"]
        M1[/api/generate — LLM Pipeline/]
        M2[/api/calibrations — Calibration CRUD/]
        M3[/api/experiments — Experiment CRUD/]
        M4[/api/audit — Audit Logging/]
        M5[Server-side Supabase Client (Service Key)]
        M6[Supabase Auth Session Verification]
        M7[Environment Config Validator (.env.local)]
        M8[Middleware.ts (Route Protection)]
    end

%% =====================================================
%%  BACKEND — SUPABASE SERVICES
%% =====================================================

    subgraph BACKEND["🗄️ BACKEND — Supabase Platform"]
        B1[(Supabase PostgreSQL Database)]
        B2[Auth Service (Email/Password, Session Tokens)]
        B3[RLS Policies Enforcer (auth.uid() Control)]
        B4[Realtime Engine (Postgres Changes → WebSocket)]
        B5[Storage Bucket (User Exports / Snapshots)]
        B6[Edge Functions (if any future expansion)]
    end

%% =====================================================
%%  DATABASE SCHEMA DETAIL
%% =====================================================

    subgraph SCHEMA["🧩 DATABASE SCHEMA — Core Tables"]
        T1[(auth.users)]
        T2[(calibrations)]
        T3[(experiments)]
        T4[(analytics_summaries)]
        T5[(audit_logs)]

        %% RELATIONSHIPS
        T2 -->|FK: user_id| T1
        T3 -->|FK: user_id| T1
        T3 -->|FK: calibration_id| T2
        T4 -->|FK: user_id| T1
        T5 -->|FK: user_id| T1
    end

%% =====================================================
%%  LLM INTEGRATION LAYER
%% =====================================================

    subgraph LLM_PIPELINE["🧠 LLM INTEGRATION — /api/generate Endpoint"]
        L1[LLM Request Builder (fetch params from latest calibration)]
        L2[OpenAI-Compatible REST API (Temperature, Top_p, Max Tokens)]
        L3[Response Parser (JSON Normalization)]
        L4[Quality Metrics Evaluator (Creativity, Coherence, Structure)]
        L5[Response Persistence → experiments.responses]
        L6[Audit Event: 'experiment_created']
    end

%% =====================================================
%%  ANALYTICS & REALTIME SUBSYSTEM
%% =====================================================

    subgraph ANALYTICS["📊 ANALYTICS + REALTIME — Live Metrics Engine"]
        R1[Realtime Hooks Layer (/lib/realtime/hooks.ts)]
        R2[Supabase Channel Subscriptions (INSERT/UPDATE/DELETE)]
        R3[Zustand Store Synchronization]
        R4[Metrics Computation Engine (/store/metrics-store.ts)]
        R5[Cached Summary Writer (analytics_summaries)]
        R6[Realtime Toast Feedback]
        R7[Audit Event: 'realtime_connected', 'data_synced']
    end

%% =====================================================
%%  AUDIT & SECURITY SYSTEM
%% =====================================================

    subgraph SECURITY["🔒 SECURITY + AUDIT SYSTEM"]
        S1[RLS Policy Enforcement (auth.uid() = user_id)]
        S2[Audit Logging API (/lib/api/audit-logs.ts)]
        S3[Event Types: auth, calibration, experiment, analytics, realtime]
        S4[GDPR-Compliant Delete / Self-Ownership]
        S5[Session Refresh Tokens / Persistent Auth]
        S6[Secure HTTPS-only Connections]
        S7[Auth Lifecycle (sign_in → sign_out → restore)]
    end

%% =====================================================
%%  DEPLOYMENT INFRASTRUCTURE
%% =====================================================

    subgraph INFRASTRUCTURE["🚀 DEPLOYMENT & RUNTIME INFRASTRUCTURE"]
        D1[Vercel Hosting (Next.js SSR Runtime)]
        D2[Supabase Cloud (Database + Auth + Realtime)]
        D3[OpenAI-Compatible API Endpoint (External)]
        D4[Environment Config (.env.local / .env.production)]
        D5[GitHub Repository (CI/CD Trigger)]
        D6[Automatic Build Hooks (vercel.json)]
        D7[Production Logs & Metrics (Vercel Dashboard)]
        D8[Docker (Local Dev Container)]
    end

%% =====================================================
%%  DATA FLOW MAPPING
%% =====================================================

    %% USER AUTHENTICATION FLOW
    A1 -->|Sign up/Login| A5
    A5 -->|Email Verification| B2
    B2 -->|Create Session| A10
    A10 -->|Store Session Locally| A5
    A5 -->|Provide Auth UID| M2
    M2 -->|Verify Session| M6
    M6 -->|Authorized Access| B1

    %% CALIBRATION FLOW
    A3 -->|Start Calibration| M2
    M2 -->|Insert Calibration| T2
    T2 -->|RLS Enforced| B3
    T2 -->|Realtime Broadcast| R2
    R2 -->|Trigger Store Update| R3
    R3 -->|Recompute Metrics| R4
    R4 -->|Persist Summary| T4
    T4 -->|Audit Log| T5

    %% EXPERIMENT FLOW
    A3 -->|Run Experiment| M3
    M3 -->|Fetch Calibration Params| T2
    M3 -->|Call LLM| L2
    L2 -->|Return Responses| L3
    L3 -->|Evaluate Metrics| L4
    L4 -->|Store Response JSON| T3
    T3 -->|Emit Realtime Event| R2
    R2 -->|UI Sync| A4
    M3 -->|Log Event| T5

    %% ANALYTICS FLOW
    T3 -->|Trigger Recompute| R4
    R4 -->|Calculate Aggregates| R5
    R5 -->|Upsert Cache| T4
    R4 -->|Broadcast Update| A4
    A4 -->|Refresh Dashboard| A3

    %% AUDIT FLOW
    Any -->|Action Event| S2
    S2 -->|Insert Log| T5
    T5 -->|RLS Policy| S1
    T5 -->|Realtime Stream| R2
    R2 -->|UI Audit View| A3

    %% DEPLOYMENT FLOW
    D5 -->|Push Commit| D6
    D6 -->|Trigger Build| D1
    D1 -->|Deploy App| A2
    D1 -->|Connect to Supabase| D2
    D1 -->|Read ENV Secrets| D4
    D2 -->|Persist Data| B1
    D1 -->|Log Metrics| D7
    D8 -->|Local Development| D1