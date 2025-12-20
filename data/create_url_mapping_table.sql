-- Create assessment_urls table for storing SHL catalog URLs
-- This table maps assessment IDs to their correct SHL product catalog URLs

CREATE TABLE IF NOT EXISTS assessment_urls (
    id TEXT PRIMARY KEY,                    -- Assessment ID (matches assessments.id)
    assessment_name TEXT NOT NULL,          -- Assessment name for reference
    url TEXT NOT NULL,                      -- Full SHL catalog URL
    url_slug TEXT,                          -- URL slug (e.g., "java-8-new")
    source TEXT DEFAULT 'generated',        -- Source: 'excel', 'scraped', or 'generated'
    verified BOOLEAN DEFAULT FALSE,         -- Whether URL has been verified to work
    scraped_at TIMESTAMP DEFAULT NOW(),     -- When URL was added
    last_verified_at TIMESTAMP,             -- Last verification timestamp
    CONSTRAINT fk_assessment
        FOREIGN KEY (id) 
        REFERENCES assessments(id) 
        ON DELETE CASCADE
);

-- Create indexes for faster lookups
CREATE INDEX IF NOT EXISTS idx_assessment_urls_slug ON assessment_urls(url_slug);
CREATE INDEX IF NOT EXISTS idx_assessment_urls_name ON assessment_urls(assessment_name);
CREATE INDEX IF NOT EXISTS idx_assessment_urls_source ON assessment_urls(source);

-- Add comments
COMMENT ON TABLE assessment_urls IS 'Maps assessment IDs to their SHL product catalog URLs';
COMMENT ON COLUMN assessment_urls.source IS 'Source of URL: excel (from training data), scraped (from SHL website), or generated (from name)';
COMMENT ON COLUMN assessment_urls.verified IS 'Whether the URL has been verified to return a valid page';
