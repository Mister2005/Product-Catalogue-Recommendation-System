---
title: BGE Embedding API
emoji: 🔍
colorFrom: blue
colorTo: purple
sdk: docker
pinned: false
---

# BGE Embedding API

High-performance embedding service using **BAAI/bge-small-en-v1.5** - optimized for semantic search and retrieval tasks.

## Features

- **Superior Retrieval Performance**: BGE models are specifically trained for retrieval tasks
- **Asymmetric Encoding**: Supports different encoding for queries vs documents
- **Query Prefix Support**: Automatic instruction prefix for search queries
- **384-dimensional embeddings**: Same size as MiniLM but much better quality
- **Under 1GB**: Fits within HuggingFace Spaces free tier limits

## Usage

### Basic Embedding
```bash
curl -X POST "https://YOUR-USERNAME-bge-embedding-api.hf.space/embed" \
  -H "Content-Type: application/json" \
  -d '{"texts": "Hello world", "normalize": true}'
```

### Query Embedding (with prefix)
```bash
curl -X POST "https://YOUR-USERNAME-bge-embedding-api.hf.space/embed" \
  -H "Content-Type: application/json" \
  -d '{"texts": "search query", "normalize": true, "is_query": true}'
```

### Batch Embedding
```bash
curl -X POST "https://YOUR-USERNAME-bge-embedding-api.hf.space/embed" \
  -H "Content-Type: application/json" \
  -d '{"texts": ["text 1", "text 2", "text 3"], "normalize": true}'
```

## API Reference

### POST /embed

**Request Body:**
- `texts` (string | string[]): Single text or array of texts to embed
- `normalize` (boolean, default: true): Whether to L2-normalize embeddings
- `is_query` (boolean, default: false): Set to true for search queries, false for documents

**Response:**
```json
{
  "embeddings": [[0.1, 0.2, ...], ...],
  "model": "BAAI/bge-small-en-v1.5",
  "dimension": 384
}
```

## Model Information

- **Model**: [BAAI/bge-small-en-v1.5](https://huggingface.co/BAAI/bge-small-en-v1.5)
- **Dimension**: 384
- **Size**: ~130MB
- **Performance**: Top-tier on MTEB retrieval benchmarks
- **License**: MIT

## Why BGE over MiniLM?

BGE (BAAI General Embedding) models significantly outperform MiniLM on retrieval tasks:
- 40-50% better performance on semantic search benchmarks
- Trained specifically for retrieval (vs general-purpose)
- Supports asymmetric query-document encoding
- Better handling of domain-specific terminology