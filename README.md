# SHL Assessment Recommendation Engine

A production-ready AI-powered recommendation system for SHL assessments, featuring multiple intelligent recommendation engines, comprehensive evaluation framework, and modern web interface.

## 🌟 Overview

This application provides intelligent assessment recommendations based on job requirements, skills, and organizational needs. It leverages multiple AI-powered recommendation engines to deliver accurate and relevant assessment suggestions for talent evaluation.

**Live Demo**: [Backend API](https://shl-recommendation-api-30oz.onrender.com) | [Frontend](https://product-catalogue-recommendation-sy.vercel.app/)

### Key Achievements

✅ **518 Assessments** scraped from SHL website and stored in Supabase  
✅ **5 Recommendation Engines** with hybrid approach (RAG, Gemini AI, NLP, Clustering)  
✅ **Complete Evaluation Framework** with industry-standard metrics  
✅ **Production-Ready** deployment on Render with optimized performance  
✅ **Comprehensive Documentation** with technical justifications

---

## 📋 Table of Contents

- [Features](#features)
- [Technology Stack](#technology-stack)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Deployment](#deployment)
- [API Reference](#api-reference)
- [Evaluation Framework](#evaluation-framework)
- [Documentation](#documentation)
- [Project Structure](#project-structure)
- [Contributing](#contributing)

---

## ✨ Features

### Recommendation Engines

- **🤖 Hybrid Recommender** (Default): Combines all engines with weighted scoring
  - RAG (40%): Semantic search with embeddings
  - Gemini AI (30%): LLM-powered intelligent recommendations
  - NLP (20%): TF-IDF text matching
  - Clustering (10%): K-Means pattern discovery

- **🧠 Gemini AI**: Google's latest Gemini 2.0 Flash model for contextual understanding
- **🔍 RAG (Retrieval-Augmented Generation)**: Semantic search using HuggingFace embeddings
- **📊 NLP**: Traditional text matching with TF-IDF and cosine similarity
- **🎯 Clustering**: Pattern-based recommendations using K-Means

### Additional Features

- **💬 AI Chatbot**: Interactive assistant for assessment queries
- **📈 Real-time Database**: Supabase PostgreSQL with vector search (pgvector)
- **⚡ High-Performance Caching**: Redis for optimized response times
- **🎨 Modern Web Interface**: Next.js 14 with TypeScript and Tailwind CSS
- **📚 Auto-Generated API Docs**: OpenAPI/Swagger documentation
- **🔒 Production-Ready**: Health checks, error handling, rate limiting

---

## 🛠️ Technology Stack

### Backend

| Component | Technology | Purpose |
|-----------|------------|---------|
| Framework | FastAPI | High-performance async web framework |
| Database | Supabase (PostgreSQL) | Managed database with vector search |
| Vector DB | pgvector | Semantic search capabilities |
| Cache | Redis (Upstash) | Response caching and rate limiting |
| Embeddings | HuggingFace API | Sentence transformers via API |
| LLM | Google Gemini 2.0 Flash | AI-powered recommendations |
| ML | scikit-learn | Clustering and NLP algorithms |
| Deployment | Render | Cloud platform (free tier) |

### Frontend

| Component | Technology | Purpose |
|-----------|------------|---------|
| Framework | Next.js 14 | React framework with App Router |
| Language | TypeScript | Type-safe development |
| Styling | Tailwind CSS | Utility-first CSS framework |
| State | React Query | Server state management |
| Animations | Framer Motion | Smooth UI animations |
| Deployment | Vercel | Serverless deployment |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                             │
│  Next.js Frontend (Vercel) + External API Clients               │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP/REST API
┌────────────────────────────┴────────────────────────────────────┐
│                     API LAYER (FastAPI)                         │
│  Render Deployment: https://shl-recommendation-api-30oz.onrender.com│
│  - /api/v1/recommend  - /api/v1/chat  - /health                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────┴────────────────────────────────────┐
│              RECOMMENDATION ENGINE LAYER                        │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Hybrid Recommender (Weighted Ensemble)                  │   │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐             │   │
│  │  │ Gemini │ │  RAG   │ │  NLP   │ │Cluster │             │   │
│  │  │  30%   │ │  40%   │ │  20%   │ │  10%   │             │   │
│  │  └────────┘ └────────┘ └────────┘ └────────┘             │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────┴────────────────────────────────────┐
│                   DATA & CACHE LAYER                            │
│  ┌─────────────────────┐        ┌──────────────────────────┐    │
│  │  Supabase (Cloud)   │        │  Redis (Upstash)         │    │
│  │  - 517 Assessments  │        │  - Response caching      │    │
│  │  - Vector embeddings│        │  - Rate limiting         │    │
│  └─────────────────────┘        └──────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

See [ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed architecture documentation.

---

## 📦 Prerequisites

- **Python 3.11+** for backend development
- **Node.js 20+** for frontend development
- **Supabase Account** (free tier) - [supabase.com](https://supabase.com)
- **Google Gemini API Key** - [ai.google.dev](https://ai.google.dev)
- **HuggingFace API Token** - [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)
- **Redis** (optional, recommended) - [upstash.com](https://upstash.com) for free tier

---

## 🚀 Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/shl-recommendation-system.git
cd shl-recommendation-system
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
# Edit .env with your credentials
```

### 3. Configure Environment Variables

Create `backend/.env`:

```env
# Supabase (Required)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key

# API Keys (Required)
GEMINI_API_KEY=your_gemini_api_key
HUGGINGFACE_API_KEY=your_huggingface_token

# Redis (Optional but recommended)
REDIS_URL=redis://default:password@your-redis-url:port

# Application
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO
SECRET_KEY=your-secret-key-here
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000

# Models
GEMINI_MODEL=gemini-2.0-flash
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
DEFAULT_RECOMMENDATION_ENGINE=hybrid
MAX_RECOMMENDATIONS=10
```

### 4. Run Backend

```bash
# Test integration
python test_integration.py

# Start server
uvicorn app.main:app --reload --port 8000
```

Visit:
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

### 5. Frontend Setup (Optional)

```bash
cd frontend-nextjs
npm install

# Create .env.local
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# Start development server
npm run dev
```

Visit: http://localhost:3000

---

## 🌐 Deployment

### Deploy Backend to Render

**Quick Deploy**:
1. Push code to GitHub
2. Go to [dashboard.render.com](https://dashboard.render.com)
3. New + → Web Service
4. Connect repository
5. Render auto-detects `render.yaml`
6. Set environment variables
7. Deploy!

**Environment Variables** (set in Render dashboard):
- `SUPABASE_URL`
- `SUPABASE_KEY`
- `GEMINI_API_KEY`
- `HUGGINGFACE_API_KEY`
- `ALLOWED_ORIGINS` (your frontend URL)
- `REDIS_URL` (optional)

### Deploy Frontend to Vercel

```bash
cd frontend-nextjs
vercel

# Set environment variable
vercel env add NEXT_PUBLIC_API_URL
# Enter your Render backend URL: https://shl-recommendation-api-30oz.onrender.com
```

---

## 📡 API Reference

### Get Recommendations

```bash
POST /api/v1/recommend
Content-Type: application/json

{
  "job_title": "Software Engineer",
  "required_skills": ["Python", "JavaScript"],
  "job_family": "Technology",
  "job_level": "Intermediate",
  "engine": "hybrid",
  "num_recommendations": 5
}
```

**Response**:
```json
{
  "recommendations": [
    {
      "id": "python_programming",
      "name": "Python Programming",
      "score": 0.95,
      "match_reason": "Strong match for Python skills",
      "type": "Individual Test Solution",
      "test_types": ["K"],
      "duration": 30
    }
  ],
  "engine_used": "hybrid",
  "total_results": 5
}
```

### Available Engines

- `hybrid` (default): Weighted combination of all engines
- `gemini`: Google Gemini AI
- `rag`: Semantic search with embeddings
- `nlp`: TF-IDF text matching
- `clustering`: K-Means clustering

See [API.md](docs/API.md) for complete API documentation.

---

## 📊 Evaluation Framework

The system includes a comprehensive evaluation framework measuring:

### Stage 1: Scraping Evaluation
- **Completeness**: 518/518 assessments (100%)
- **Data Quality**: 100% required fields complete
- **Verification**: Automated quality checks

### Stage 2: Retrieval Evaluation
- **Metrics**: Precision@K, Recall@K, MRR
- **Test Cases**: 10 diverse queries
- **Thresholds**: P@10 >0.8, R@10 >0.7, MRR >0.85

### Stage 3: Recommendation Evaluation
- **Metrics**: NDCG@K, MAP, Hit Rate
- **Test Cases**: 5 job scenarios
- **Thresholds**: NDCG@10 >0.75, MAP >0.70

**Run Evaluation**:
```bash
python scripts/run_comprehensive_evaluation.py --stage all
```

See [EVALUATION.md](docs/EVALUATION.md) for detailed evaluation documentation.

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | System architecture and data flow |
| [API.md](docs/API.md) | Complete API reference |
| [DEPLOYMENT.md](docs/DEPLOYMENT.md) | Deployment guide for all platforms |
| [EVALUATION.md](docs/EVALUATION.md) | Evaluation framework and metrics |
| [TECHNICAL_JUSTIFICATION.md](docs/TECHNICAL_JUSTIFICATION.md) | Technical choices and justifications |
| [USAGE.md](docs/USAGE.md) | Usage examples and tutorials |
| [RENDER_DEPLOYMENT.md](RENDER_DEPLOYMENT.md) | Quick Render deployment guide |

---

## 📁 Project Structure

```
.
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── core/              # Configuration, database, cache
│   │   ├── models/            # Pydantic models
│   │   ├── services/          # Recommendation engines
│   │   ├── evaluation/        # Evaluation framework
│   │   └── main.py            # FastAPI application
│   ├── requirements.txt       # Python dependencies
│   ├── Dockerfile             # Docker configuration
│   └── test_integration.py    # Integration tests
├── frontend-nextjs/           # Next.js frontend
│   ├── src/
│   │   ├── app/              # Next.js pages
│   │   ├── components/       # React components
│   │   └── lib/              # Utilities
│   └── package.json          # Node dependencies
├── data/                      # Data and scripts
│   ├── shl_products_complete.json  # 518 assessments
│   ├── scrape_full_catalogue.py    # Web scraper
│   └── migrate_to_supabase_simple.py  # Data migration
├── docs/                      # Documentation
│   ├── ARCHITECTURE.md
│   ├── API.md
│   ├── DEPLOYMENT.md
│   ├── EVALUATION.md
│   ├── TECHNICAL_JUSTIFICATION.md
│   └── USAGE.md
├── scripts/                   # Utility scripts
│   ├── run_comprehensive_evaluation.py
│   └── verify_supabase_migration.py
├── render.yaml               # Render deployment config
├── RENDER_DEPLOYMENT.md      # Deployment guide
└── README.md                 # This file
```

---

## 🧪 Testing

### Integration Tests

```bash
cd backend
python test_integration.py
```

Tests:
- ✅ Supabase connection
- ✅ Embedding service (HuggingFace API)
- ✅ All recommendation engines
- ✅ Environment variables

### Evaluation Tests

```bash
python scripts/run_comprehensive_evaluation.py --stage all
```

Generates comprehensive evaluation report with metrics for all stages.

---

## 🔧 Development

### Backend Development

```bash
cd backend

# Run with auto-reload
uvicorn app.main:app --reload

# Format code
black app/
isort app/

# Type checking
mypy app/

# Linting
flake8 app/
```

### Frontend Development

```bash
cd frontend-nextjs

# Development server
npm run dev

# Build for production
npm run build

# Lint
npm run lint
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is proprietary. All rights reserved.

---

## 🙏 Acknowledgments

- **SHL** for the assessment catalogue
- **Google** for Gemini AI API
- **HuggingFace** for embedding models
- **Supabase** for managed PostgreSQL with vector search
- **Render** for deployment platform

---

## 📞 Support

For questions or issues:
- Open an issue on GitHub
- Check [documentation](docs/)
- Review [evaluation framework](docs/EVALUATION.md)

---

**Version**: 2.0.0  
**Last Updated**: December 2025  
**Status**: ✅ Production Ready
