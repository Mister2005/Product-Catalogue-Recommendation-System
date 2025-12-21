-- ============================================================================
-- Supabase RPC Function for Vector Similarity Search
-- ============================================================================
-- This function performs vector similarity search with optional metadata filters
-- Run this AFTER running setup_supabase_vectors.sql
-- ============================================================================

CREATE OR REPLACE FUNCTION match_assessments(
    query_embedding vector(384),
    match_count INT DEFAULT 10,
    filter_job_level TEXT DEFAULT NULL,
    filter_max_duration INT DEFAULT NULL,
    filter_remote TEXT DEFAULT NULL,
    filter_adaptive TEXT DEFAULT NULL
)
RETURNS TABLE (
    id TEXT,
    name TEXT,
    url TEXT,
    description TEXT,
    duration INT,
    adaptive_support TEXT,
    remote_support TEXT,
    test_type TEXT,
    job_level TEXT,
    full_text TEXT,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        ae.id,
        ae.name,
        ae.url,
        ae.description,
        ae.duration,
        ae.adaptive_support,
        ae.remote_support,
        ae.test_type,
        ae.job_level,
        ae.full_text,
        1 - (ae.embedding <=> query_embedding) AS similarity
    FROM assessment_embeddings ae
    WHERE
        -- Apply job level filter if specified
        (filter_job_level IS NULL OR ae.job_level = filter_job_level)
        -- Apply duration filter if specified
        AND (filter_max_duration IS NULL OR ae.duration <= filter_max_duration)
        -- Apply remote support filter if specified
        AND (filter_remote IS NULL OR ae.remote_support = filter_remote)
        -- Apply adaptive support filter if specified
        AND (filter_adaptive IS NULL OR ae.adaptive_support = filter_adaptive)
    ORDER BY ae.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- ============================================================================
-- Alternative: Simpler search function without filters
-- ============================================================================

CREATE OR REPLACE FUNCTION search_assessments(
    query_embedding vector(384),
    match_count INT DEFAULT 10
)
RETURNS TABLE (
    id TEXT,
    name TEXT,
    url TEXT,
    description TEXT,
    duration INT,
    adaptive_support TEXT,
    remote_support TEXT,
    test_type TEXT,
    job_level TEXT,
    full_text TEXT,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        ae.id,
        ae.name,
        ae.url,
        ae.description,
        ae.duration,
        ae.adaptive_support,
        ae.remote_support,
        ae.test_type,
        ae.job_level,
        ae.full_text,
        1 - (ae.embedding <=> query_embedding) AS similarity
    FROM assessment_embeddings ae
    ORDER BY ae.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- ============================================================================
-- Full-Text Search Function (BM25-style)
-- ============================================================================

CREATE OR REPLACE FUNCTION search_assessments_fulltext(
    search_query TEXT,
    match_count INT DEFAULT 10
)
RETURNS TABLE (
    id TEXT,
    name TEXT,
    url TEXT,
    description TEXT,
    duration INT,
    adaptive_support TEXT,
    remote_support TEXT,
    test_type TEXT,
    job_level TEXT,
    full_text TEXT,
    rank FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        ae.id,
        ae.name,
        ae.url,
        ae.description,
        ae.duration,
        ae.adaptive_support,
        ae.remote_support,
        ae.test_type,
        ae.job_level,
        ae.full_text,
        ts_rank(to_tsvector('english', ae.full_text), to_tsquery('english', search_query)) AS rank
    FROM assessment_embeddings ae
    WHERE to_tsvector('english', ae.full_text) @@ to_tsquery('english', search_query)
    ORDER BY rank DESC
    LIMIT match_count;
END;
$$;

-- ============================================================================
-- Test the functions
-- ============================================================================

-- Test 1: Check if functions exist
SELECT 
    proname as "Function Name",
    pg_get_function_arguments(oid) as "Arguments"
FROM pg_proc
WHERE proname IN ('match_assessments', 'search_assessments', 'search_assessments_fulltext')
ORDER BY proname;

-- Test 2: Simple search (will work after data migration)
-- SELECT * FROM search_assessments('[0.1, 0.2, ...]'::vector(384), 5);

-- Test 3: Search with filters (will work after data migration)
-- SELECT * FROM match_assessments('[0.1, 0.2, ...]'::vector(384), 5, 'Entry_Level', 60, 'Yes', NULL);

-- ============================================================================
-- Done! Functions are ready for use
-- ============================================================================
