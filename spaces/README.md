---
title: MiniLM Embedding API
emoji: 🔢
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
---
# MiniLM Embedding API
Fast embedding service using sentence-transformers/all-MiniLM-L6-v2
## Usage
```bash
curl -X POST "https://YOUR-USERNAME-minilm-embedding-api.hf.space/embed" \
  -H "Content-Type: application/json" \
  -d '{"texts": "Hello world"}'