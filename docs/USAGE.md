# Usage Guide

## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <repository-url>
cd product-catalogue-recommendation-system

# Backend setup
cd backend
python -m venv venv

# Activate virtual environment
# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Start the Backend Server

```bash
cd backend

# Activate virtual environment (if not already activated)
# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate

# Start the server
python -m uvicorn app.main:app --reload --port 8000
```

The API will start at `http://localhost:8000`

### 3. Start the Frontend

```bash
cd frontend-nextjs
npm install
npm run dev
```

The frontend will start at `http://localhost:3000`

### 4. Access the Application

| Service | URL |
|---------|-----|
| Frontend Application | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Documentation (Swagger) | http://localhost:8000/docs |
| API Documentation (ReDoc) | http://localhost:8000/redoc |

---

## Using the Web Interface

1. **Fill Out Requirements Form:**
   - Enter job title (e.g., "Software Developer")
   - Select job family and level
   - Add required skills
   - Select preferred test types
   - Check "Remote Testing Required" if needed

2. **Get Recommendations:**
   - Click "Get Recommendations"
   - View matched assessments with scores
   - See detailed match reasons for each recommendation

3. **Use the AI Chatbot:**
   - Click the chat icon in the bottom-right corner
   - Ask questions about assessments
   - Get conversational recommendations

4. **Review Results:**
   - Assessments are sorted by match score
   - Higher scores indicate better matches
   - Each card shows test types, duration, and why it was recommended

---

## Using the API Directly

### Example: Get Recommendations with cURL

```bash
curl -X POST "http://localhost:8000/api/v1/recommend" \
  -H "Content-Type: application/json" \
  -d '{
    "job_title": "Software Developer",
    "job_family": "Technology",
    "required_skills": ["Programming", ".NET"],
    "test_types": ["K"],
    "remote_testing_required": true,
    "num_recommendations": 3,
    "engine": "hybrid"
  }'
```

### Example: Python Requests

```python
import requests

url = "http://localhost:8000/api/v1/recommend"
data = {
    "job_title": "Account Manager",
    "job_family": "Sales",
    "job_level": "Intermediate",
    "required_skills": ["Communication", "Relationship Management"],
    "test_types": ["P", "B"],
    "num_recommendations": 5,
    "engine": "hybrid"
}

response = requests.post(url, json=data)
recommendations = response.json()

for rec in recommendations["recommendations"]:
    print(f"{rec['assessment']['name']}: {rec['score']:.2f}")
```

### Example: Chat with AI Assistant

```python
import requests

url = "http://localhost:8000/api/v1/chat"
data = {
    "message": "What assessments are best for hiring software engineers?",
    "conversation_history": []
}

response = requests.post(url, json=data)
result = response.json()
print(result["response"])
```

### Example: JavaScript Fetch

```javascript
const url = 'http://localhost:8000/api/v1/recommend';
const data = {
  job_title: 'Administrative Assistant',
  job_family: 'Administrative',
  job_level: 'Entry Level',
  required_skills: ['Organization', 'Microsoft Office'],
  num_recommendations: 3,
  engine: 'hybrid'
};

fetch(url, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(data)
})
  .then(res => res.json())
  .then(data => console.log(data.recommendations));
```

---

## Common Use Cases

### 1. Finding Assessments for a Specific Role

```python
request = {
    "job_title": "Branch Manager",
    "job_family": "Management",
    "job_level": "Manager",
    "industry": "Banking",
    "num_recommendations": 5,
    "engine": "hybrid"
}
```

### 2. Finding Technical Skill Assessments

```python
request = {
    "job_family": "Technology",
    "required_skills": [".NET", "C#", "MVC"],
    "test_types": ["K"],  # Knowledge tests
    "num_recommendations": 3,
    "engine": "gemini"
}
```

### 3. Finding Entry-Level Assessments

```python
request = {
    "job_level": "Entry Level",
    "industry": "Retail",
    "remote_testing_required": True,
    "max_duration": 45,  # Maximum 45 minutes
    "num_recommendations": 5,
    "engine": "hybrid"
}
```

### 4. Finding Personality and Behavioral Tests

```python
request = {
    "job_title": "Sales Representative",
    "test_types": ["P", "B"],  # Personality and Behavioral
    "num_recommendations": 3,
    "engine": "rag"
}
```

---

## Recommendation Engines

| Engine | Best For | Description |
|--------|----------|-------------|
| `hybrid` | General use (recommended) | Combines all methods for optimal results |
| `gemini` | Complex queries | Uses Google Gemini AI for intelligent recommendations |
| `rag` | Semantic matching | Retrieval-Augmented Generation with embeddings |
| `nlp` | Text-based matching | TF-IDF based text similarity |
| `clustering` | Pattern discovery | K-Means pattern recognition |

---

## Understanding Recommendation Scores

| Score Range | Match Quality | Recommendation |
|-------------|---------------|----------------|
| 0.8 - 1.0 | Excellent | Highly recommended |
| 0.6 - 0.8 | Good | Suitable for most needs |
| 0.4 - 0.6 | Fair | Consider if specific requirements met |
| 0.0 - 0.4 | Weak | May not be ideal |

Scores are calculated using:
- AI/ML similarity algorithms (varies by engine)
- Exact match bonuses (job level, family, skills)
- Test type preferences
- Hard filters (remote testing, duration, language)

---

## Advanced Features

### Adding New Assessments

New assessments should be added via the Supabase database. The SQL setup script is located at `data/SUPABASE_SQL_SETUP.sql`.

### Customizing the Recommendation Algorithm

Edit the services in `backend/app/services/`:
- `hybrid_recommender.py` - Combined recommendation logic
- `gemini_recommender.py` - Gemini AI recommendations
- `rag_recommender.py` - RAG-based recommendations
- `nlp_recommender.py` - NLP/TF-IDF recommendations
- `clustering_recommender.py` - Clustering-based recommendations

---

## Troubleshooting

### API Won't Start

```bash
# Check if port 8000 is in use
# Windows
netstat -ano | findstr :8000
# Linux/macOS
lsof -i :8000

# Use a different port
python -m uvicorn app.main:app --port 8001
```

### No Recommendations Returned

- Check your filters aren't too restrictive
- Try removing some criteria
- Check database connection is working
- Verify Redis is running for caching

### Frontend Can't Connect to API

- Ensure API is running on port 8000
- Check browser console for CORS errors
- Verify `NEXT_PUBLIC_API_URL` in `.env.local`

### Database Connection Issues

- Verify Supabase project is active
- Check `SUPABASE_URL` and `SUPABASE_KEY` in `.env`
- Ensure IP allowlist settings permit your connection

---

## Production Deployment

### Environment Variables

Ensure all environment variables are set for production:

```bash
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=your-secure-production-secret
ALLOWED_ORIGINS=https://your-domain.com
```

### Using Docker (Optional)

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Security Considerations

- Enable authentication (JWT, OAuth)
- Configure rate limiting via `RATE_LIMIT_PER_MINUTE`
- Restrict CORS origins in `ALLOWED_ORIGINS`
- Use HTTPS in production
- Rotate API keys regularly
- Enable database connection pooling
