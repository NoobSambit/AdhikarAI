# System Context Diagram

High-level system context showing AdhikarAI's components and their relationships.

---

## System Architecture

```mermaid
flowchart TB
    subgraph Users
        B[👤 Beneficiary<br/>Low-end Android, 2G/3G]
        Op[👤 Operator<br/>NGO/CSC worker]
        Admin[👤 Admin<br/>Super admin]
    end

    subgraph Frontend["Frontend (Vercel)"]
        PWA[Next.js 15 PWA<br/>Voice-first UI]
        Dashboard[Dashboard<br/>Operator/Admin]
    end

    subgraph Backend["Backend (Render)"]
        API[FastAPI<br/>71 routes]
        Agent[LangGraph Agent<br/>10-node graph]
        VP[Voice Pipeline<br/>ASR → Translate → TTS]
        EE[Eligibility Engine<br/>Experta + FAISS]
        RL[Rate Limiter<br/>Daily counters]
        Scheduler[APScheduler<br/>Expiry + Quality]
    end

    subgraph Storage
        DB[(PostgreSQL<br/>Neon / local)]
        Redis[(Redis<br/>Upstash / memory)]
        FAISS[(FAISS Index<br/>Local files)]
    end

    subgraph Providers["External Providers"]
        LLM[LLM<br/>Ollama / Groq]
        ASR[ASR<br/>Whisper.cpp / Groq]
        TR[Translation<br/>IndicTrans2 / AI4Bharat / Google]
        TTS[TTS<br/>IndicTTS / Google]
        OTP[OTP SMS<br/>MSG91 / mock]
    end

    B --> PWA
    Op --> Dashboard
    Admin --> Dashboard

    PWA -->|REST + WS| API
    Dashboard -->|REST| API

    API --> Agent
    API --> VP
    API --> EE
    API --> RL

    Agent --> LLM
    Agent --> DB
    Agent --> Redis

    VP --> ASR
    VP --> TR
    VP --> TTS
    VP --> Redis

    EE --> DB
    EE --> FAISS

    RL --> Redis
    Scheduler --> DB

    API --> DB
    API --> OTP
```

---

## Component Architecture

```mermaid
flowchart LR
    subgraph FE["Frontend (Next.js 15)"]
        direction TB
        AppRouter[App Router]
        BenefUI[Beneficiary PWA<br/>Voice + Text]
        DashUI[Dashboard UI<br/>Operator + Admin]
        OfflineDB[IndexedDB<br/>Offline cache]
        ServiceWorker[Service Worker<br/>Cache + offline]
    end

    subgraph BE["Backend (FastAPI)"]
        direction TB
        Routes[API Routes<br/>18 router files]
        Core[Core<br/>Config, Security, Errors]
        Services[Services<br/>Eligibility, Profiles, Schemes]
        AgentMod[Agent Module<br/>LangGraph graph]
        VoiceMod[Voice Module<br/>Pipeline + providers]
        TransMod[Translation Module<br/>Client + providers]
        TTSMod[TTS Module<br/>Client + providers]
        DashMod[Dashboard Module<br/>RBAC + beneficiaries]
        AdminMod[Admin Panel<br/>Drafts + quality]
        RateMod[Rate Limit<br/>Redis counters]
        CLI[CLI Module<br/>Seed + E2E helpers]
    end

    subgraph Data["Data Layer"]
        direction TB
        ORM[SQLAlchemy Models<br/>45 model classes]
        Migrations[Alembic<br/>5 migration files]
        Schemas[Pydantic Schemas<br/>15 schema files]
    end

    FE --> Routes
    Routes --> Core
    Routes --> Services
    Routes --> AgentMod
    Routes --> VoiceMod
    Routes --> DashMod
    Routes --> AdminMod
    Services --> ORM
    AgentMod --> Services
    VoiceMod --> TransMod
    VoiceMod --> TTSMod
```

---

## Deployment Topology

```mermaid
flowchart LR
    subgraph Internet
        User[User Browser]
    end

    subgraph Vercel
        NextJS[Next.js PWA<br/>Static + SSR]
    end

    subgraph Render
        FastAPI[FastAPI Backend<br/>uvicorn]
    end

    subgraph Neon
        PG[(PostgreSQL)]
    end

    subgraph Upstash
        RedisDB[(Redis)]
    end

    subgraph Groq
        GLLM[LLM API]
        GASR[Whisper API]
    end

    User -->|HTTPS| NextJS
    NextJS -->|HTTPS + WSS| FastAPI
    FastAPI -->|asyncpg| PG
    FastAPI -->|rediss://| RedisDB
    FastAPI -->|HTTPS| GLLM
    FastAPI -->|HTTPS| GASR
```
