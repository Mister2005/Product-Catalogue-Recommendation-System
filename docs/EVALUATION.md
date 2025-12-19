# Evaluation Framework Guide

## Overview

This document explains the comprehensive evaluation framework implemented for the SHL Assessment Recommendation System. The framework validates all three key evaluation criteria at multiple stages of the pipeline.

---

## Evaluation Criteria

### ✅ Criterion 1: Complete Scraping Pipeline
- **What**: Built a pipeline to scrape, parse, and store SHL product catalogue data
- **How**: Enhanced scraper with pagination handling, detail page extraction, and Supabase storage
- **Evaluation**: Scraping evaluator measures completeness and data quality

### ✅ Criterion 2: Modern LLM/RAG Techniques
- **What**: Used modern LLM and RAG techniques with justified framework choices
- **How**: Implemented hybrid recommendation with RAG, Gemini AI, NLP, and clustering
- **Evaluation**: Documented in `TECHNICAL_JUSTIFICATION.md`

### ✅ Criterion 3: Evaluation Methods
- **What**: Proper evaluation methods at key stages to measure accuracy and effectiveness
- **How**: Multi-stage evaluation framework with industry-standard metrics
- **Evaluation**: This framework itself demonstrates comprehensive evaluation

---

## Evaluation Stages

### Stage 1: Scraping Evaluation

**Purpose**: Validate completeness and quality of scraped data

**Metrics**:
- **Completeness Score**: Percentage of expected assessments scraped
  - Target: 520+ assessments (100%)
  - Threshold: >95% for PASS
  
- **Data Quality Score**: Percentage of fields properly populated
  - Required fields: id, name, type, test_types
  - Optional fields: description, job_levels, industries, languages
  - Threshold: >90% for PASS

- **Sample Validation**: Manual validation of random sample
  - Sample size: 10 assessments
  - Checks: Required fields, metadata completeness

**How to Run**:
```bash
python backend/app/evaluation/scraping_evaluator.py data/shl_products_complete.json
```

**Output**:
- Console report with scores and status
- JSON report saved to `data/shl_products_complete_evaluation_report.json`

---

### Stage 2: Retrieval Evaluation

**Purpose**: Measure quality of semantic search and retrieval

**Metrics**:
- **Precision@K**: Relevant results in top K
  - Formula: `relevant_in_top_k / k`
  - Target: P@10 > 0.8
  
- **Recall@K**: Coverage of relevant results
  - Formula: `relevant_in_top_k / total_relevant`
  - Target: R@10 > 0.7
  
- **Mean Reciprocal Rank (MRR)**: Position of first relevant result
  - Formula: `1 / rank_of_first_relevant`
  - Target: MRR > 0.85

**Test Dataset**: 10 queries with expected results
- Example: "Python programming assessment" → [python_programming, java_programming, ...]

**How to Run**:
```python
from app.evaluation.retrieval_evaluator import RetrievalEvaluator, TEST_QUERIES

def my_retrieval_function(query):
    # Your RAG/NLP retrieval implementation
    return retrieved_ids

evaluator = RetrievalEvaluator(TEST_QUERIES)
results = evaluator.evaluate_all(my_retrieval_function)
evaluator.print_report(results)
```

---

### Stage 3: Recommendation Evaluation

**Purpose**: Measure quality of final recommendations

**Metrics**:
- **NDCG@K**: Normalized Discounted Cumulative Gain
  - Measures ranking quality with position discount
  - Formula: `DCG@K / IDCG@K`
  - Target: NDCG@10 > 0.75
  
- **Mean Average Precision (MAP)**: Average precision across queries
  - Target: MAP > 0.70
  
- **Hit Rate@K**: Whether any relevant item is in top K
  - Target: HR@5 > 0.85

**Test Dataset**: 5 job scenarios with expected recommendations
- Example: Software Engineer → [python_programming (1.0), javascript (1.0), ...]

**How to Run**:
```python
from app.evaluation.recommendation_evaluator import RecommendationEvaluator, EVALUATION_CASES

def my_recommendation_function(request):
    # Your recommendation implementation
    return recommended_ids

evaluator = RecommendationEvaluator(EVALUATION_CASES)
results = evaluator.evaluate_all(my_recommendation_function)
evaluator.print_report(results)
```

---

## Comprehensive Evaluation

**Purpose**: Run all stages and generate complete report

**How to Run**:
```bash
# Run all stages
python scripts/run_evaluation.py --stage all

# Run specific stage
python scripts/run_evaluation.py --stage scraping --data-path data/shl_products_complete.json

# Custom output path
python scripts/run_evaluation.py --output my_evaluation_report.json
```

**Output**:
- Console summary with overall status and scores
- JSON report with detailed results from all stages
- Evaluation criteria checklist

---

## Metrics Explained

### Precision@K
**What it measures**: Accuracy of top K results

**Example**:
- Query: "Python programming"
- Top 5 results: [python, java, javascript, excel, word]
- Relevant: [python, java, javascript]
- Precision@5 = 3/5 = 0.60

**Interpretation**:
- 1.0 = Perfect (all top K are relevant)
- 0.5 = Half of top K are relevant
- 0.0 = None of top K are relevant

### Recall@K
**What it measures**: Coverage of relevant results

**Example**:
- Query: "Python programming"
- Top 5 results: [python, java, javascript, excel, word]
- All relevant: [python, java, javascript, sql, dotnet]
- Recall@5 = 3/5 = 0.60

**Interpretation**:
- 1.0 = All relevant items retrieved
- 0.5 = Half of relevant items retrieved
- 0.0 = No relevant items retrieved

### NDCG@K
**What it measures**: Ranking quality with position discount

**Why it matters**: Position matters! Getting the best result first is better than getting it last.

**Example**:
- Perfect ranking: [1.0, 0.9, 0.8, 0.7, 0.6] → NDCG = 1.0
- Good ranking: [0.9, 1.0, 0.7, 0.8, 0.6] → NDCG = 0.98
- Poor ranking: [0.6, 0.7, 0.8, 0.9, 1.0] → NDCG = 0.85

**Interpretation**:
- 1.0 = Perfect ranking
- 0.8+ = Good ranking
- 0.6- = Poor ranking

---

## Interpreting Results

### Overall Status

| Status | Meaning | Action |
|--------|---------|--------|
| ✅ PASSED | All metrics meet thresholds | System ready for production |
| ⚠️ WARNING | Some metrics below target | Review and improve specific areas |
| ❌ FAILED | Critical metrics failed | Major improvements needed |

### Score Thresholds

| Metric | PASSED | WARNING | FAILED |
|--------|--------|---------|--------|
| Scraping Completeness | >95% | 80-95% | <80% |
| Data Quality | >90% | 75-90% | <75% |
| Precision@10 | >0.80 | 0.60-0.80 | <0.60 |
| Recall@10 | >0.70 | 0.50-0.70 | <0.50 |
| MRR | >0.85 | 0.70-0.85 | <0.70 |
| NDCG@10 | >0.75 | 0.60-0.75 | <0.60 |
| MAP | >0.70 | 0.55-0.70 | <0.55 |

---

## Continuous Improvement

### 1. Monitor Metrics
- Run evaluations regularly (weekly/monthly)
- Track trends over time
- Identify degradation early

### 2. Expand Test Cases
- Add more diverse queries
- Include edge cases
- Update expected results based on new assessments

### 3. A/B Testing
- Test different recommendation strategies
- Compare engine weights
- Optimize parameters

### 4. User Feedback
- Collect real user ratings
- Incorporate into evaluation
- Retrain models based on feedback

---

## Troubleshooting

### Low Scraping Completeness
- Check for website changes
- Verify pagination logic
- Review error logs

### Low Retrieval Precision
- Improve query preprocessing
- Tune embedding model
- Add query expansion

### Low Recommendation NDCG
- Adjust engine weights
- Improve re-ranking logic
- Add business rules

---

## References

- [Information Retrieval Metrics](https://en.wikipedia.org/wiki/Evaluation_measures_(information_retrieval))
- [NDCG Explained](https://en.wikipedia.org/wiki/Discounted_cumulative_gain)
- [Recommendation System Evaluation](https://medium.com/@m_n_malaeb/recall-and-precision-at-k-for-recommender-systems-618483226c54)
