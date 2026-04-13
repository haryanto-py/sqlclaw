-- =============================================================
-- Tear-down script — drops all Olist tables and the read-only role.
--
-- USE WITH CAUTION. Run this only when you want a clean slate
-- before re-running the full ETL pipeline from scratch.
--
-- Run as the database owner or a superuser.
-- =============================================================

BEGIN;

-- Drop tables in reverse FK-dependency order
DROP TABLE IF EXISTS order_reviews              CASCADE;
DROP TABLE IF EXISTS order_payments             CASCADE;
DROP TABLE IF EXISTS order_items                CASCADE;
DROP TABLE IF EXISTS orders                     CASCADE;
DROP TABLE IF EXISTS products                   CASCADE;
DROP TABLE IF EXISTS geolocation                CASCADE;
DROP TABLE IF EXISTS sellers                    CASCADE;
DROP TABLE IF EXISTS customers                  CASCADE;
DROP TABLE IF EXISTS product_category_translation CASCADE;

COMMIT;

-- Drop the read-only role (outside transaction — DDL on roles cannot be transactional)
DROP ROLE IF EXISTS olist_reader;
