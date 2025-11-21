-- Skill DNA Database Schema
-- Star schema for time-series skill analysis

-- Core tables
CREATE TABLE IF NOT EXISTS employees (
  employee_id VARCHAR(50) PRIMARY KEY,
  first_name VARCHAR(100),
  last_name VARCHAR(100),
  department VARCHAR(100),
  position VARCHAR(100),
  hire_date DATE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS skills (
  skill_id SERIAL PRIMARY KEY,
  skill_name VARCHAR(200) UNIQUE NOT NULL,
  skill_category VARCHAR(100),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS skill_events (
  event_id SERIAL PRIMARY KEY,
  employee_id VARCHAR(50) REFERENCES employees(employee_id) ON DELETE CASCADE,
  skill_id INTEGER REFERENCES skills(skill_id) ON DELETE CASCADE,
  event_date DATE NOT NULL,
  event_type VARCHAR(50), -- 'certification', 'training', 'assessment', 'project', 'acquired'
  proficiency_level INTEGER CHECK (proficiency_level BETWEEN 1 AND 5),
  source VARCHAR(100), -- 'LMS', 'HR', 'Manual', 'Project'
  notes TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(employee_id, skill_id, event_date)
);

-- Canonical events table (normalized from all sources)
CREATE TABLE IF NOT EXISTS canonical_events (
  canonical_id SERIAL PRIMARY KEY,
  employee_id VARCHAR(50) NOT NULL,
  hire_date DATE,
  department VARCHAR(100),
  position VARCHAR(100),
  skill_name VARCHAR(200) NOT NULL,
  category VARCHAR(100),
  event_type VARCHAR(50) NOT NULL, -- 'acquired', 'completed', 'used', 'certified'
  event_date DATE NOT NULL,
  source VARCHAR(100) NOT NULL, -- 'HR_SYSTEM', 'LMS', 'PLANNING', 'PROJECTS', 'QUALIFICATIONS'
  confidence DECIMAL(3,2) DEFAULT 1.0, -- 0.00 to 1.00
  raw_source_row JSONB, -- Original data for audit trail
  source_event_id INTEGER REFERENCES skill_events(event_id), -- Link to original event if exists
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(employee_id, skill_name, event_date, source)
);

-- Operational tables
CREATE TABLE IF NOT EXISTS upload_history (
  upload_id SERIAL PRIMARY KEY,
  filename VARCHAR(500),
  format_detected VARCHAR(100),
  rows_processed INTEGER,
  upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  status VARCHAR(50), -- 'success', 'failed', 'partial'
  error_message TEXT
);

CREATE TABLE IF NOT EXISTS analysis_cache (
  cache_id SERIAL PRIMARY KEY,
  cache_key VARCHAR(500) UNIQUE NOT NULL,
  result_json JSONB,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  expires_at TIMESTAMP
);

-- Taxonomy versioning table
CREATE TABLE IF NOT EXISTS taxonomy_versions (
  version_id SERIAL PRIMARY KEY,
  version_number INTEGER NOT NULL UNIQUE,
  taxonomy_snapshot JSONB NOT NULL,  -- Full category -> skills mapping
  cluster_stats JSONB,                 -- Cluster metrics (sizes, densities, etc.)
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  created_by VARCHAR(100) DEFAULT 'system',
  change_summary TEXT,                 -- Human-readable summary of changes
  trigger_type VARCHAR(50)             -- 'upload', 'manual', 'recompute', 'cluster_shift'
);

-- Ingestion log table (anomaly detection tracking)
CREATE TABLE IF NOT EXISTS ingestion_log (
  ingestion_id SERIAL PRIMARY KEY,
  filename VARCHAR(500),
  format_detected VARCHAR(100),
  rows_processed INTEGER,
  upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  status VARCHAR(50), -- 'success', 'warning', 'failed'
  anomaly_report TEXT, -- JSON string of anomaly detection results
  error_message TEXT
);

-- Performance indexes
CREATE INDEX IF NOT EXISTS idx_skill_events_employee ON skill_events(employee_id);
CREATE INDEX IF NOT EXISTS idx_skill_events_skill ON skill_events(skill_id);
CREATE INDEX IF NOT EXISTS idx_skill_events_date ON skill_events(event_date);
CREATE INDEX IF NOT EXISTS idx_skills_category ON skills(skill_category);
CREATE INDEX IF NOT EXISTS idx_analysis_cache_key ON analysis_cache(cache_key);
CREATE INDEX IF NOT EXISTS idx_analysis_cache_expires ON analysis_cache(expires_at);

-- Composite index for time-series queries
CREATE INDEX IF NOT EXISTS idx_skill_events_skill_date ON skill_events(skill_id, event_date);
CREATE INDEX IF NOT EXISTS idx_skill_events_employee_date ON skill_events(employee_id, event_date);

-- Canonical events indexes
CREATE INDEX IF NOT EXISTS idx_canonical_employee ON canonical_events(employee_id);
CREATE INDEX IF NOT EXISTS idx_canonical_skill_name ON canonical_events(skill_name);
CREATE INDEX IF NOT EXISTS idx_canonical_event_date ON canonical_events(event_date);
CREATE INDEX IF NOT EXISTS idx_canonical_source ON canonical_events(source);
CREATE INDEX IF NOT EXISTS idx_canonical_category ON canonical_events(category);
CREATE INDEX IF NOT EXISTS idx_canonical_employee_date ON canonical_events(employee_id, event_date);
CREATE INDEX IF NOT EXISTS idx_canonical_skill_date ON canonical_events(skill_name, event_date);

-- Taxonomy versioning indexes
CREATE INDEX IF NOT EXISTS idx_taxonomy_version_number ON taxonomy_versions(version_number);
CREATE INDEX IF NOT EXISTS idx_taxonomy_created_at ON taxonomy_versions(created_at);

-- Ingestion log indexes
CREATE INDEX IF NOT EXISTS idx_ingestion_upload_date ON ingestion_log(upload_date);
CREATE INDEX IF NOT EXISTS idx_ingestion_status ON ingestion_log(status);
CREATE INDEX IF NOT EXISTS idx_ingestion_format ON ingestion_log(format_detected);
