-- =============================================================
-- Create a read-only role for the OpenClaw agent.
--
-- Run this as the database owner or a superuser, AFTER schema.sql
-- has been applied and data has been loaded.
--
-- The OpenClaw PostgreSQL skill should use READONLY_DB_URL from .env,
-- which points to this user. Even if the LLM generates a write query,
-- the DB will reject it at the permission level (defense-in-depth).
-- =============================================================

-- Password is set separately by the ETL pipeline using READONLY_DB_PASSWORD from .env
CREATE ROLE olist_reader WITH LOGIN CONNECTION LIMIT 5;

GRANT CONNECT ON DATABASE olist_ecommerce TO olist_reader;

GRANT USAGE ON SCHEMA public TO olist_reader;

GRANT SELECT ON ALL TABLES IN SCHEMA public TO olist_reader;

ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO olist_reader;

REVOKE INSERT, UPDATE, DELETE, TRUNCATE ON ALL TABLES IN SCHEMA public FROM olist_reader;
