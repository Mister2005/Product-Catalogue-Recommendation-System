-- ================================================
-- Simplified SHL Recommendations Database Schema
-- Only Essential Tables for Recommendation System
-- ================================================

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- ================================================
-- MAIN TABLE: Assessments
-- ================================================
CREATE TABLE IF NOT EXISTS assessments (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(500) NOT NULL,
    type VARCHAR(100) NOT NULL,
    description TEXT,
    remote_testing BOOLEAN DEFAULT FALSE,
    adaptive BOOLEAN DEFAULT FALSE,
    job_family VARCHAR(200),
    job_level VARCHAR(100),
    duration INTEGER,
    test_types TEXT[],  -- Array field for test types
    industries TEXT[],  -- Array field for industries
    languages TEXT[],   -- Array field for languages
    skills TEXT[],      -- Array field for skills
    embedding VECTOR(384),  -- For semantic search
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ================================================
-- INDEXES for Performance
-- ================================================
CREATE INDEX IF NOT EXISTS idx_assessments_job_family ON assessments(job_family);
CREATE INDEX IF NOT EXISTS idx_assessments_type ON assessments(type);
CREATE INDEX IF NOT EXISTS idx_assessments_remote_testing ON assessments(remote_testing);

-- ================================================
-- RECOMMENDATION HISTORY TABLE
-- For tracking performance and analytics
-- ================================================
CREATE TABLE IF NOT EXISTS recommendation_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(255),
    query_text TEXT NOT NULL,
    query_parameters JSONB,
    recommended_assessments JSONB NOT NULL,
    recommendation_engine VARCHAR(50) NOT NULL,
    scores JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_recommendation_history_created ON recommendation_history(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_recommendation_history_user ON recommendation_history(user_id);
CREATE INDEX IF NOT EXISTS idx_recommendation_history_engine ON recommendation_history(recommendation_engine);

-- ================================================
-- UPDATE TRIGGER
-- ================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_assessments_updated_at ON assessments;
CREATE TRIGGER update_assessments_updated_at BEFORE UPDATE ON assessments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ================================================
-- SUCCESS MESSAGE
-- ================================================
DO $$
BEGIN
    RAISE NOTICE '✅ Simplified database schema created successfully!';
    RAISE NOTICE '📊 Tables created:';
    RAISE NOTICE '   - assessments (with array fields for test_types, skills, etc.)';
    RAISE NOTICE '   - recommendation_history (for performance tracking)';
    RAISE NOTICE '🔍 Indexes created for optimized queries';
    RAISE NOTICE '';
    RAISE NOTICE '🎯 Next step: Run migration script to populate data';
    RAISE NOTICE '   python data/migrate_to_supabase_simple.py';
END $$;
