-- Initial database setup for Docker PostgreSQL
-- This runs automatically when the container is first created

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE skillbridge_ai TO skillbridge_user;
GRANT ALL PRIVILEGES ON SCHEMA public TO skillbridge_user;
