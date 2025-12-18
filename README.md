# SHL Assessment Recommendation Engine

A production-ready AI-powered recommendation system for SHL assessments, featuring multiple intelligent recommendation engines and a modern web interface.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Technology Stack](#technology-stack)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Reference](#api-reference)
- [Project Structure](#project-structure)
- [Development](#development)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## Overview

This application provides intelligent assessment recommendations based on job requirements, skills, and organizational needs. It leverages multiple AI-powered recommendation engines to deliver accurate and relevant assessment suggestions for talent evaluation.

## Features

- **Multiple Recommendation Engines**: Hybrid, Gemini AI, RAG, NLP, and Clustering-based approaches
- **AI-Powered Chatbot**: Interactive assistant for assessment queries and recommendations
- **Real-time Database**: Supabase (PostgreSQL) with vector search capabilities
- **High-Performance Caching**: Redis for optimized response times
- **Modern Web Interface**: Next.js frontend with responsive design
- **RESTful API**: Well-documented FastAPI backend with OpenAPI specification

## Technology Stack

### Backend
| Component | Technology |
|-----------|------------|
| Framework | FastAPI |
| Database | Supabase (PostgreSQL) |
| Cache | Redis |
| AI/ML | Google Gemini, Sentence Transformers, scikit-learn |
| ORM | SQLAlchemy |

### Frontend
| Component | Technology |
|-----------|------------|
| Framework | Next.js 14 |
| Language | TypeScript |
| Styling | Tailwind CSS |
| State Management | React Query |
| Animations | Framer Motion |

## Prerequisites

- Python 3.11 or higher
- Node.js 20 or higher
- Redis 7 or higher (local or cloud-hosted)
- Supabase account (free tier available)
- Google Gemini API key

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd product-catalogue-recommendation-system
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Frontend Setup

```bash
cd frontend-nextjs

# Install dependencies
npm install
```

### 4. Database Setup

1. Create a Supabase project at [supabase.com](https://supabase.com)
2. Navigate to Settings > Database to obtain connection credentials
3. Execute the SQL setup script located at `data/SUPABASE_SQL_SETUP.sql` in the Supabase SQL Editor

## Configuration

### Environment Variables

Create a `.env` file in the project root directory using `.env.example` as a template:

```env
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key
SUPABASE_DB_PASSWORD=your_database_password

# Redis Configuration
REDIS_URL=redis://localhost:6379/0
REDIS_CACHE_TTL=3600

# API Keys
GEMINI_API_KEY=your_gemini_api_key

# Application Configuration
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO
SECRET_KEY=your_secret_key_here

# CORS Settings
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000

# RAG Configuration
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
VECTOR_DIMENSION=384
TOP_K_RESULTS=10

# Recommendation Configuration
DEFAULT_RECOMMENDATION_ENGINE=hybrid
MAX_RECOMMENDATIONS=10

# Next.js Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000

# Model Configuration
GEMINI_MODEL=gemini-2.5-flash
GEMINI_TEMPERATURE=0.7
GEMINI_MAX_TOKENS=2048

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
```

> **Note**: Never commit sensitive credentials to version control. The `.env` file is excluded via `.gitignore`.

## Usage

### Starting the Application

**Terminal 1 - Backend Server:**

```bash
cd backend

# Activate virtual environment
# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate

# Start the server
python -m uvicorn app.main:app --reload --port 8000
```

**Terminal 2 - Frontend Development Server:**

```bash
cd frontend-nextjs
npm run dev
```

### Accessing the Application

| Service | URL |
|---------|-----|
| Frontend Application | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Documentation (Swagger) | http://localhost:8000/docs |
| API Documentation (ReDoc) | http://localhost:8000/redoc |

## API Reference

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/recommend` | Get assessment recommendations |
| POST | `/api/v1/chat` | Interact with AI chatbot |
| GET | `/api/v1/assessments` | List all assessments |
| GET | `/api/v1/metadata` | Retrieve system metadata |
| GET | `/health` | Health check endpoint |

### Example Request

```python
import requests

response = requests.post(
    'http://localhost:8000/api/v1/recommend',
    json={
        "job_title": "Software Engineer",
        "job_family": "Technology",
        "required_skills": ["Python", "JavaScript"],
        "num_recommendations": 5,
        "engine": "hybrid"
    }
)

recommendations = response.json()
```

### Recommendation Engines

| Engine | Description |
|--------|-------------|
| `hybrid` | Combines all methods for optimal results (recommended) |
| `gemini` | Google Gemini AI for intelligent recommendations |
| `rag` | Retrieval-Augmented Generation with semantic search |
| `nlp` | TF-IDF based text matching |
| `clustering` | K-Means pattern recognition |

## Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── core/              # Configuration, database, cache, logging
│   │   ├── models/            # Data models and schemas
│   │   ├── services/          # Recommendation engines and business logic
│   │   └── main.py            # FastAPI application entry point
│   ├── database/
│   │   └── init.sql           # Database initialization schema
│   ├── scripts/               # Utility and maintenance scripts
│   └── requirements.txt       # Python dependencies
├── frontend-nextjs/
│   ├── src/
│   │   ├── app/               # Next.js pages and routing
│   │   ├── components/        # React components
│   │   └── lib/               # Utilities and helpers
│   ├── package.json           # Node.js dependencies
│   └── tailwind.config.js     # Tailwind CSS configuration
├── data/
│   ├── shl_products.json      # Assessment data source
│   └── SUPABASE_SQL_SETUP.sql # Database setup script
├── docs/
│   ├── API.md                 # API documentation
│   ├── ARCHITECTURE.md        # System architecture
│   ├── DEPLOYMENT.md          # Deployment guide
│   └── USAGE.md               # Usage guide
├── .env.example               # Environment variables template
├── .gitignore                 # Git ignore rules
├── requirements.txt           # Root-level Python dependencies
└── README.md                  # This file
```

## Development

### Backend Development

```bash
cd backend

# Activate virtual environment
# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate

# Run tests
pytest

# Code formatting
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

# Run development server
npm run dev

# Run tests
npm test

# Build for production
npm run build

# Lint code
npm run lint
```

### Code Quality Standards

- Follow PEP 8 guidelines for Python code
- Use TypeScript strict mode for frontend development
- Maintain comprehensive type hints and documentation
- Write unit tests for critical functionality

## Troubleshooting

### Database Connection Issues

- Verify Supabase project is active and accessible
- Confirm `DATABASE_URL` or `SUPABASE_URL` is correctly configured
- Check IP allowlist settings in Supabase dashboard
- Use Connection Pooling URL for production deployments

### Redis Connection Issues

- Ensure Redis server is running locally or accessible remotely
- Verify `REDIS_URL` configuration is correct
- Check firewall settings for port 6379

### Import Errors

- Confirm virtual environment is activated
- Run `pip install -r requirements.txt` to install dependencies
- Verify Python version compatibility (3.11+)

### Frontend Issues

- Ensure backend server is running before starting frontend
- Verify `NEXT_PUBLIC_API_URL` points to correct backend address
- Clear `.next` cache directory and reinstall dependencies if needed

## License

Proprietary - All rights reserved.

---

**Version**: 2.0.0  
**Last Updated**: December 2024
