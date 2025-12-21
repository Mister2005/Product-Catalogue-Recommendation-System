-- ============================================================================
-- Supabase Vector Database Setup for SHL Assessment Recommendations
-- ============================================================================
-- This script sets up pgvector extension and creates the necessary tables
-- and indexes for storing and searching assessment embeddings.
--
-- Run this in Supabase SQL Editor:
-- 1. Go to your Supabase project dashboard
-- 2. Click "SQL Editor" in the left sidebar
-- 3. Click "New Query"
-- 4. Paste this entire script
-- 5. Click "Run" or press Ctrl+Enter
-- ============================================================================

-- Enable pgvector extension for vector similarity search
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================================
-- Main Embeddings Table
-- ============================================================================
-- Stores assessment metadata and vector embeddings for semantic search
CREATE TABLE IF NOT EXISTS assessment_embeddings (
    -- Primary identifier
    id TEXT PRIMARY KEY,
    
    -- Assessment details
    name TEXT NOT NULL,
    url TEXT NOT NULL,
    description TEXT,
    
    -- Metadata filters
    duration INTEGER DEFAULT 0,
    adaptive_support TEXT DEFAULT 'No',
    remote_support TEXT DEFAULT 'No',
    test_type TEXT DEFAULT 'General',
    job_level TEXT DEFAULT 'General',  -- Entry_Level, Manager_Senior, General
    
    -- Full text for search and BM25
    full_text TEXT NOT NULL,
    
    -- Vector embedding (384 dimensions for BAAI/bge-small-en-v1.5)
    embedding vector(384),
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- Indexes for Performance
-- ============================================================================

-- Vector similarity search index (IVFFlat for fast approximate nearest neighbor)
-- Using cosine distance for similarity
CREATE INDEX IF NOT EXISTS assessment_embeddings_embedding_idx 
ON assessment_embeddings 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Note: IVFFlat index requires at least 1000 rows for optimal performance
-- With 517 assessments, we're using a smaller lists value (100)
-- For production with more data, increase lists to ~sqrt(total_rows)

-- Metadata filtering indexes for hybrid search
CREATE INDEX IF NOT EXISTS assessment_embeddings_job_level_idx 
ON assessment_embeddings(job_level);

CREATE INDEX IF NOT EXISTS assessment_embeddings_duration_idx 
ON assessment_embeddings(duration);

CREATE INDEX IF NOT EXISTS assessment_embeddings_remote_idx 
ON assessment_embeddings(remote_support);

CREATE INDEX IF NOT EXISTS assessment_embeddings_adaptive_idx 
ON assessment_embeddings(adaptive_support);

CREATE INDEX IF NOT EXISTS assessment_embeddings_test_type_idx 
ON assessment_embeddings(test_type);

-- Full-text search index for BM25-style keyword search
-- Using PostgreSQL's built-in text search capabilities
CREATE INDEX IF NOT EXISTS assessment_embeddings_full_text_idx 
ON assessment_embeddings 
USING GIN(to_tsvector('english', full_text));

-- URL index for quick lookups
CREATE INDEX IF NOT EXISTS assessment_embeddings_url_idx 
ON assessment_embeddings(url);

-- ============================================================================
-- Helper Functions
-- ============================================================================

-- Function to update the updated_at timestamp automatically
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-update updated_at on row updates
DROP TRIGGER IF EXISTS update_assessment_embeddings_updated_at ON assessment_embeddings;
CREATE TRIGGER update_assessment_embeddings_updated_at
    BEFORE UPDATE ON assessment_embeddings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- Verification Queries
-- ============================================================================

-- Check if pgvector extension is enabled
SELECT 
    extname as "Extension Name",
    extversion as "Version"
FROM pg_extension 
WHERE extname = 'vector';

-- Check table structure
SELECT 
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'assessment_embeddings'
ORDER BY ordinal_position;

-- Check indexes
SELECT 
    indexname as "Index Name",
    indexdef as "Index Definition"
FROM pg_indexes
WHERE tablename = 'assessment_embeddings'
ORDER BY indexname;

-- Count rows (should be 0 initially)
SELECT COUNT(*) as "Total Assessments" FROM assessment_embeddings;

-- ============================================================================
-- Example Queries for Testing (Run after data migration)
-- ============================================================================

-- Example 1: Vector similarity search (cosine distance)
-- Find top 10 assessments similar to a query embedding
/*
SELECT 
    name,
    url,
    job_level,
    duration,
    1 - (embedding <=> '[0.1, 0.2, ... 384 dimensions]'::vector) as similarity
FROM assessment_embeddings
ORDER BY embedding <=> '[0.1, 0.2, ... 384 dimensions]'::vector
LIMIT 10;
*/

-- Example 2: Hybrid search with metadata filtering
/*
SELECT 
    name,
    url,
    job_level,
    duration,
    1 - (embedding <=> '[...]'::vector) as similarity
FROM assessment_embeddings
WHERE 
    job_level = 'Entry_Level'
    AND duration <= 60
    AND remote_support = 'Yes'
ORDER BY embedding <=> '[...]'::vector
LIMIT 10;
*/

-- Example 3: Full-text search (BM25-style)
/*
SELECT 
    name,
    url,
    ts_rank(to_tsvector('english', full_text), query) as rank
FROM assessment_embeddings,
    to_tsquery('english', 'python & programming') query
WHERE to_tsvector('english', full_text) @@ query
ORDER BY rank DESC
LIMIT 10;
*/

-- ============================================================================
-- Setup Complete!
-- ============================================================================
-- Next steps:
-- 1. Run migration script to populate data: python backend/scripts/migrate_chromadb_to_supabase.py
-- 2. Verify data: SELECT COUNT(*) FROM assessment_embeddings;
-- 3. Update backend to use Supabase: Set VECTOR_DB_TYPE=supabase in .env
-- ============================================================================
