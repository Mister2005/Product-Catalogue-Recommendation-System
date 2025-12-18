# API Documentation

## Overview

The SHL Assessment Recommendation Engine provides a RESTful API for getting intelligent assessment recommendations based on job requirements.

## Base URL

```
http://localhost:8000
```

## Authentication

Currently, the API does not require authentication. This can be added in production environments.

---

## Endpoints

### 1. Get Recommendations

Get personalized assessment recommendations based on requirements.

**Endpoint:** `POST /api/v1/recommend`

**Request Body:**
```json
{
  "job_title": "Software Developer",
  "job_family": "Technology",
  "job_level": "Intermediate",
  "industry": "Technology",
  "required_skills": ["Programming", "Problem Solving"],
  "test_types": ["K", "C"],
  "remote_testing_required": true,
  "language": "English",
  "max_duration": 60,
  "num_recommendations": 5,
  "engine": "hybrid"
}
```

**Request Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `job_title` | string | No | Target job title |
| `job_family` | string | No | Job family category |
| `job_level` | string | No | Organizational level (Entry Level, Intermediate, Senior, Manager, Executive) |
| `industry` | string | No | Industry sector |
| `required_skills` | array | No | List of skills to assess |
| `test_types` | array | No | Test type codes (C, P, A, B, K, S, E, D) |
| `remote_testing_required` | boolean | No | Remote testing required |
| `language` | string | No | Assessment language (default: "English") |
| `max_duration` | integer | No | Maximum duration in minutes |
| `num_recommendations` | integer | No | Number of recommendations (default: 5) |
| `engine` | string | No | Recommendation engine to use (hybrid, gemini, rag, nlp, clustering) |

**Response:**
```json
{
  "recommendations": [
    {
      "assessment": {
        "id": "dotnet_framework",
        "name": ".NET Framework 4.5",
        "type": "Individual Test Solution",
        "test_types": ["K"],
        "remote_testing": true,
        "adaptive": false,
        "job_family": "Technology",
        "job_level": "Intermediate",
        "industries": ["Technology", "Finance"],
        "languages": ["English"],
        "skills": [".NET Framework", "C#"],
        "duration": 45
      },
      "score": 0.856,
      "match_reasons": [
        "Matches job family: Technology",
        "Includes requested test types: KNOWLEDGE",
        "Evaluates: Programming"
      ]
    }
  ],
  "total_assessments_considered": 10,
  "query_summary": {
    "job_title": "Software Developer",
    "job_family": "Technology"
  }
}
```

---

### 2. Chat with AI Assistant

Interact with the AI-powered chatbot for assessment queries.

**Endpoint:** `POST /api/v1/chat`

**Request Body:**
```json
{
  "message": "What assessments are good for hiring software engineers?",
  "conversation_history": []
}
```

**Response:**
```json
{
  "response": "For hiring software engineers, I recommend...",
  "recommendations": [...],
  "conversation_id": "abc123"
}
```

---

### 3. List Assessments

Get all available assessments with optional filtering.

**Endpoint:** `GET /api/v1/assessments`

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `job_family` | string | Filter by job family |
| `industry` | string | Filter by industry |
| `test_type` | string | Filter by test type code |
| `remote_testing` | boolean | Filter by remote testing capability |

**Example:**
```
GET /api/v1/assessments?job_family=Technology&remote_testing=true
```

**Response:**
```json
[
  {
    "id": "dotnet_framework",
    "name": ".NET Framework 4.5",
    "type": "Individual Test Solution",
    "test_types": ["K"],
    "remote_testing": true,
    "job_family": "Technology",
    "duration": 45
  }
]
```

---

### 4. Get Assessment Details

Get detailed information about a specific assessment.

**Endpoint:** `GET /api/v1/assessments/{assessment_id}`

**Example:**
```
GET /api/v1/assessments/account_manager_solution
```

**Response:**
```json
{
  "id": "account_manager_solution",
  "name": "Account Manager Solution",
  "type": "Pre-packaged Job Solution",
  "test_types": ["C", "P", "A", "B"],
  "remote_testing": true,
  "adaptive": false,
  "job_family": "Sales",
  "job_level": "Intermediate",
  "industries": ["Technology", "Finance"],
  "languages": ["English", "Spanish"],
  "skills": ["Relationship Management", "Communication"],
  "description": "Comprehensive assessment for account management",
  "duration": 90
}
```

---

### 5. Get Metadata

Get available options for job families, industries, skills, etc.

**Endpoint:** `GET /api/v1/metadata`

**Response:**
```json
{
  "job_families": ["Technology", "Sales", "Finance", "Administrative"],
  "industries": ["Technology", "Finance", "Healthcare", "Retail"],
  "skills": ["Leadership", "Communication", "Programming"],
  "job_levels": ["Entry Level", "Intermediate", "Senior"],
  "test_types": [
    {"code": "C", "name": "COGNITIVE"},
    {"code": "P", "name": "PERSONALITY"}
  ],
  "total_assessments": 10
}
```

---

### 6. Health Check

Check API health status.

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "healthy",
  "assessments_loaded": 10,
  "version": "2.0.0"
}
```

---

## Recommendation Engines

| Engine | Description |
|--------|-------------|
| `hybrid` | Combines all methods for optimal results (recommended) |
| `gemini` | Google Gemini AI for intelligent recommendations |
| `rag` | Retrieval-Augmented Generation with semantic search |
| `nlp` | TF-IDF based text matching |
| `clustering` | K-Means pattern recognition |

---

## Test Type Codes

| Code | Name | Description |
|------|------|-------------|
| C | Cognitive | Cognitive ability tests |
| P | Personality | Personality assessments |
| A | Ability | General ability tests |
| B | Behavioral | Behavioral assessments |
| K | Knowledge | Knowledge/skills tests |
| S | Simulation | Job simulations |
| E | Emotional Intelligence | EI assessments |
| D | Development | Development assessments |

---

## Error Responses

**400 Bad Request:**
```json
{
  "detail": "Invalid request parameters"
}
```

**404 Not Found:**
```json
{
  "detail": "Assessment with ID 'xyz' not found"
}
```

**500 Internal Server Error:**
```json
{
  "detail": "Error generating recommendations: [error message]"
}
```

---

## Rate Limiting

Rate limiting is configured via the `RATE_LIMIT_PER_MINUTE` environment variable (default: 60 requests per minute).

## CORS

CORS is configured via the `ALLOWED_ORIGINS` environment variable. Restrict origins in production environments.
