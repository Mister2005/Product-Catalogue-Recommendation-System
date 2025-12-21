# System Architecture

## Overview

The SHL Assessment Recommendation Engine is a full-stack application consisting of a FastAPI backend with multiple AI-powered recommendation engines, a Supabase database, Redis caching, and a Next.js frontend.

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           CLIENT LAYER                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌────────────────────────┐           ┌──────────────────────────────┐  │
│  │   Next.js Frontend     │           │   External API Clients       │  │
│  │   (frontend-nextjs/)   │           │   (cURL, Python, etc.)       │  │
│  │                        │           │                              │  │
│  │  - React Components    │           │  - Direct API integration    │  │
│  │  - Tailwind CSS        │           │  - Automated systems         │  │
│  │  - React Query         │           │  - Third-party applications  │  │
│  │  - AI Chatbot UI       │           │                              │  │
│  └───────────┬────────────┘           └──────────────┬───────────────┘  │
│              │                                        │                  │
└──────────────┼────────────────────────────────────────┼──────────────────┘
               │              HTTP/REST API             │
               │                                        │
┌──────────────┴────────────────────────────────────────┴──────────────────┐
│                         API LAYER (FastAPI)                               │
│                         backend/app/main.py                               │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  Endpoints:                                                               │
│  ┌──────────────────────────────────────────────────────────────────┐    │
│  │  POST   /api/v1/recommend      → Get AI-powered recommendations  │    │
│  │  POST   /api/v1/chat           → Interact with AI chatbot        │    │
│  │  GET    /api/v1/assessments    → List all assessments            │    │
│  │  GET    /api/v1/assessments/{id} → Get specific assessment       │    │
│  │  GET    /api/v1/metadata       → Get filter options              │    │
│  │  GET    /health                → Health check                    │    │
│  └──────────────────────────────────────────────────────────────────┘    │
│                                                                           │
│  Features:                                                                │
│  - Request Validation (Pydantic)                                          │
│  - Error Handling and Logging                                             │
│  - CORS Support                                                           │
│  - Rate Limiting                                                          │
│  - Auto-generated OpenAPI Documentation                                   │
│                                                                           │
└─────────────────────────────────────┬─────────────────────────────────────┘
                                      │
┌─────────────────────────────────────┴─────────────────────────────────────┐
│                    RECOMMENDATION ENGINE LAYER                             │
│                    backend/app/services/                                   │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                     Hybrid Recommender                               │  │
│  │                     (hybrid_recommender.py)                          │  │
│  │                                                                      │  │
│  │  Combines outputs from all engines with weighted scoring             │  │
│  └──────────────────────────────┬──────────────────────────────────────┘  │
│                                 │                                          │
│  ┌──────────────────────────────┴──────────────────────────────────────┐  │
│  │                                                                      │  │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐   │  │
│  │  │   Gemini    │ │    RAG      │ │    NLP      │ │ Clustering  │   │  │
│  │  │ Recommender │ │ Recommender │ │ Recommender │ │ Recommender │   │  │
│  │  │             │ │             │ │             │ │             │   │  │
│  │  │ Google AI   │ │ Embeddings  │ │ TF-IDF      │ │ K-Means     │   │  │
│  │  │ Gemini API  │ │ Semantic    │ │ Cosine Sim  │ │ Patterns    │   │  │
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘   │  │
│  │                                                                      │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
└─────────────────────────────────────┬──────────────────────────────────────┘
                                      │
┌─────────────────────────────────────┴──────────────────────────────────────┐
│                         DATA & CACHE LAYER                                  │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────────────────────┐    ┌──────────────────────────────────┐  │
│  │         Supabase             │    │           Redis Cache            │  │
│  │       (PostgreSQL)           │    │                                  │  │
│  │                              │    │  - Response caching              │  │
│  │  - Assessments table         │    │  - Session storage               │  │
│  │  - Vector embeddings         │    │  - Rate limiting                 │  │
│  │  - User data (future)        │    │  - Configurable TTL              │  │
│  └──────────────────────────────┘    └──────────────────────────────────┘  │
│                                                                             │
│  Configuration:                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  backend/app/core/                                                    │  │
│  │  - config.py      → Environment configuration                        │  │
│  │  - database.py    → Supabase connection                               │  │
│  │  - cache.py       → Redis connection                                  │  │
│  │  - logging.py     → Application logging                               │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Component Details

### Frontend (Next.js)

| Component | Location | Description |
|-----------|----------|-------------|
| Pages | `frontend-nextjs/src/app/` | Next.js 14 App Router pages |
| Components | `frontend-nextjs/src/components/` | Reusable React components |
| Utilities | `frontend-nextjs/src/lib/` | Helper functions and API clients |
| Styling | `frontend-nextjs/tailwind.config.js` | Tailwind CSS configuration |

### Backend (FastAPI)

| Component | Location | Description |
|-----------|----------|-------------|
| Main Application | `backend/app/main.py` | FastAPI app with routes and middleware |
| Configuration | `backend/app/core/config.py` | Environment and settings |
| Database | `backend/app/core/database.py` | Supabase connection and queries |
| Cache | `backend/app/core/cache.py` | Redis caching layer |
| Models | `backend/app/models/` | Pydantic data models |
| Services | `backend/app/services/` | Recommendation engines |

### Recommendation Engines

| Engine | File | Algorithm |
|--------|------|-----------|
| Hybrid | `hybrid_recommender.py` | Weighted combination of all engines |
| Gemini | `gemini_recommender.py` | Google Gemini AI API |
| RAG | `rag_recommender_v2.py` | Sentence Transformers + Vector Search (Weighted Embeddings + Exact Name Match) |
| NLP | `nlp_recommender.py` | TF-IDF + Cosine Similarity |
| Clustering | `clustering_recommender.py` | K-Means Clustering |

---

## Data Flow

```
User Request
     │
     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 1. INPUT PROCESSING                                              │
│    - Parse request JSON                                          │
│    - Validate with Pydantic                                      │
│    - Check cache for existing result                             │
└─────────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. ENGINE SELECTION                                              │
│    - Route to specified engine (default: hybrid)                 │
│    - Initialize engine with database connection                  │
└─────────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. RECOMMENDATION GENERATION                                     │
│                                                                  │
│    Hybrid Engine:                                                │
│    ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐             │
│    │ Gemini  │ │   RAG   │ │   NLP   │ │Cluster  │             │
│    └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘             │
│         │           │           │           │                    │
│         └───────────┴───────────┴───────────┘                    │
│                       │                                          │
│                       ▼                                          │
│              Weighted Score Combination                          │
└─────────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. POST-PROCESSING                                               │
│    - Apply filters (duration, remote testing, language)         │
│    - Rank by final score                                         │
│    - Generate match reasons                                      │
│    - Cache result                                                │
└─────────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. RESPONSE                                                      │
│    - Format as JSON                                              │
│    - Include metadata                                            │
│    - Return to client                                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## Technology Stack

### Backend Technologies

| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.11+ | Runtime |
| FastAPI | Latest | Web framework |
| Uvicorn | Latest | ASGI server |
| Pydantic | v2 | Data validation |
| SQLAlchemy | Latest | ORM |
| Supabase | Cloud | Database |
| Redis | 7+ | Caching |
| Sentence Transformers | Latest | Embeddings |
| scikit-learn | Latest | ML algorithms |
| Google Generative AI | Latest | Gemini API |

### Frontend Technologies

| Technology | Version | Purpose |
|------------|---------|---------|
| Next.js | 14 | React framework |
| TypeScript | 5+ | Type safety |
| Tailwind CSS | 3 | Styling |
| React Query | 5 | Server state |
| Framer Motion | Latest | Animations |

---

## Database Schema

```sql
-- Assessments Table
CREATE TABLE assessments (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT,
    test_types TEXT[],
    remote_testing BOOLEAN DEFAULT true,
    adaptive BOOLEAN DEFAULT false,
    job_family TEXT,
    job_level TEXT,
    industries TEXT[],
    languages TEXT[],
    skills TEXT[],
    description TEXT,
    duration INTEGER,
    url TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Vector embeddings for RAG (if using pgvector)
CREATE EXTENSION IF NOT EXISTS vector;

ALTER TABLE assessments 
ADD COLUMN embedding vector(384);
```

---

## Security Considerations

| Layer | Security Measure |
|-------|------------------|
| API | Rate limiting, CORS configuration |
| Authentication | JWT/OAuth ready (not implemented by default) |
| Database | Connection pooling, parameterized queries |
| Environment | Secrets in environment variables |
| Network | HTTPS in production |

---

## Scalability

| Component | Scaling Strategy |
|-----------|------------------|
| Backend | Horizontal scaling with load balancer |
| Database | Supabase managed scaling |
| Cache | Redis cluster or managed Redis |
| Frontend | CDN deployment (Vercel recommended) |

---

## Monitoring and Logging

- Application logs via Python `logging` module
- Structured logging in `backend/app/core/logging.py`
- Log levels configurable via `LOG_LEVEL` environment variable
- Health check endpoint at `/health` for monitoring
