-- Create a restricted application role
CREATE ROLE app_user WITH LOGIN PASSWORD 'app_password';

-- Grant permissions on the public schema
GRANT CONNECT ON DATABASE postgres TO app_user;
GRANT USAGE ON SCHEMA public TO app_user;
GRANT CREATE ON SCHEMA public TO app_user;

-- Grant specific permissions (not full DDL)
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user;

-- Create watermark table for idempotent processing
CREATE TABLE IF NOT EXISTS ingestion_watermarks (
    source TEXT PRIMARY KEY,
    last_seen TEXT,
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Grant permissions on watermark table
GRANT SELECT, INSERT, UPDATE ON ingestion_watermarks TO app_user;

-- Create applicants table if it doesn't exist
CREATE TABLE IF NOT EXISTS applicants (
    result_id SERIAL PRIMARY KEY,
    program TEXT,
    comments TEXT,
    date_added TEXT,
    url TEXT UNIQUE,
    status TEXT,
    term TEXT,
    us_or_international TEXT,
    gpa TEXT,
    gre TEXT,
    gre_v TEXT,
    gre_aw TEXT,
    degree TEXT,
    llm_generated_program TEXT,
    llm_generated_university TEXT
);

-- Grant permissions on applicants table
GRANT SELECT, INSERT, UPDATE ON applicants TO app_user;
GRANT USAGE ON SEQUENCE applicants_result_id_seq TO app_user;