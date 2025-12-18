-- Initialize SHL Recommendations Database
-- This script creates the initial database schema

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "vector";

-- Create assessments table
CREATE TABLE IF NOT EXISTS assessments (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(500) NOT NULL,
    type VARCHAR(100) NOT NULL,
    remote_testing BOOLEAN DEFAULT FALSE,
    adaptive BOOLEAN DEFAULT FALSE,
    job_family VARCHAR(200),
    job_level VARCHAR(100),
    description TEXT,
    duration INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    embedding VECTOR(384)  -- For RAG system
);

-- Create test_types table (many-to-many relationship)
CREATE TABLE IF NOT EXISTS test_types (
    id SERIAL PRIMARY KEY,
    assessment_id VARCHAR(255) REFERENCES assessments(id) ON DELETE CASCADE,
    test_type VARCHAR(50) NOT NULL,
    UNIQUE(assessment_id, test_type)
);

-- Create industries table
CREATE TABLE IF NOT EXISTS industries (
    id SERIAL PRIMARY KEY,
    assessment_id VARCHAR(255) REFERENCES assessments(id) ON DELETE CASCADE,
    industry VARCHAR(200) NOT NULL,
    UNIQUE(assessment_id, industry)
);

-- Create languages table
CREATE TABLE IF NOT EXISTS languages (
    id SERIAL PRIMARY KEY,
    assessment_id VARCHAR(255) REFERENCES assessments(id) ON DELETE CASCADE,
    language VARCHAR(100) NOT NULL,
    UNIQUE(assessment_id, language)
);

-- Create skills table
CREATE TABLE IF NOT EXISTS skills (
    id SERIAL PRIMARY KEY,
    assessment_id VARCHAR(255) REFERENCES assessments(id) ON DELETE CASCADE,
    skill VARCHAR(200) NOT NULL,
    UNIQUE(assessment_id, skill)
);

-- Create recommendation_history table
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

-- Create user_feedback table
CREATE TABLE IF NOT EXISTS user_feedback (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    recommendation_id UUID REFERENCES recommendation_history(id) ON DELETE CASCADE,
    assessment_id VARCHAR(255) REFERENCES assessments(id) ON DELETE CASCADE,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    feedback_text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better query performance
CREATE INDEX idx_assessments_job_family ON assessments(job_family);
CREATE INDEX idx_assessments_job_level ON assessments(job_level);
CREATE INDEX idx_assessments_type ON assessments(type);
CREATE INDEX idx_assessments_remote_testing ON assessments(remote_testing);
CREATE INDEX idx_assessments_name_trgm ON assessments USING gin (name gin_trgm_ops);
CREATE INDEX idx_assessments_description_trgm ON assessments USING gin (description gin_trgm_ops);
CREATE INDEX idx_test_types_assessment ON test_types(assessment_id);
CREATE INDEX idx_industries_assessment ON industries(assessment_id);
CREATE INDEX idx_skills_assessment ON skills(assessment_id);
CREATE INDEX idx_recommendation_history_created ON recommendation_history(created_at DESC);
CREATE INDEX idx_recommendation_history_user ON recommendation_history(user_id);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for assessments table
CREATE TRIGGER update_assessments_updated_at BEFORE UPDATE ON assessments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create view for full assessment details
CREATE OR REPLACE VIEW assessment_details AS
SELECT 
    a.*,
    COALESCE(array_agg(DISTINCT tt.test_type) FILTER (WHERE tt.test_type IS NOT NULL), ARRAY[]::VARCHAR[]) as test_types_array,
    COALESCE(array_agg(DISTINCT i.industry) FILTER (WHERE i.industry IS NOT NULL), ARRAY[]::VARCHAR[]) as industries_array,
    COALESCE(array_agg(DISTINCT l.language) FILTER (WHERE l.language IS NOT NULL), ARRAY[]::VARCHAR[]) as languages_array,
    COALESCE(array_agg(DISTINCT s.skill) FILTER (WHERE s.skill IS NOT NULL), ARRAY[]::VARCHAR[]) as skills_array
FROM assessments a
LEFT JOIN test_types tt ON a.id = tt.assessment_id
LEFT JOIN industries i ON a.id = i.assessment_id
LEFT JOIN languages l ON a.id = l.assessment_id
LEFT JOIN skills s ON a.id = s.assessment_id
GROUP BY a.id;

-- Grant necessary permissions
GRANT ALL PRIVILEGES ON DATABASE shl_recommendations TO shl_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO shl_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO shl_user;
