-- =============================================================
-- Olist Brazilian E-Commerce — PostgreSQL Schema
-- Database: olist_ecommerce
--
-- Run as the database owner or a superuser.
-- Tables are created in FK-dependency order.
-- =============================================================

BEGIN;

-- -------------------------------------------------------------
-- 1. Product Category Translation
--    No FK dependencies — load first.
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS product_category_translation (
    product_category_name          VARCHAR(100) PRIMARY KEY,
    product_category_name_english  VARCHAR(100) NOT NULL
);

-- -------------------------------------------------------------
-- 2. Customers
--    No FK dependencies.
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS customers (
    customer_id              VARCHAR(32) PRIMARY KEY,
    customer_unique_id       VARCHAR(32) NOT NULL,
    customer_zip_code_prefix VARCHAR(5)  NOT NULL,
    customer_city            VARCHAR(100) NOT NULL,
    customer_state           CHAR(2)      NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_customers_unique_id ON customers (customer_unique_id);
CREATE INDEX IF NOT EXISTS idx_customers_state     ON customers (customer_state);
CREATE INDEX IF NOT EXISTS idx_customers_zip       ON customers (customer_zip_code_prefix);

-- -------------------------------------------------------------
-- 3. Sellers
--    No FK dependencies.
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sellers (
    seller_id              VARCHAR(32) PRIMARY KEY,
    seller_zip_code_prefix VARCHAR(5)   NOT NULL,
    seller_city            VARCHAR(100) NOT NULL,
    seller_state           CHAR(2)      NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_sellers_state ON sellers (seller_state);
CREATE INDEX IF NOT EXISTS idx_sellers_zip   ON sellers (seller_zip_code_prefix);

-- -------------------------------------------------------------
-- 4. Geolocation
--    Not FK-constrained — zip codes don't reliably match
--    customers/sellers 1-to-1 in the raw data.
--    Unique index enforced AFTER deduplication during cleaning.
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS geolocation (
    geolocation_zip_code_prefix VARCHAR(5)        NOT NULL,
    geolocation_lat             DOUBLE PRECISION  NOT NULL,
    geolocation_lng             DOUBLE PRECISION  NOT NULL,
    geolocation_city            VARCHAR(100)      NOT NULL,
    geolocation_state           CHAR(2)           NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_geolocation_zip
    ON geolocation (geolocation_zip_code_prefix);

-- -------------------------------------------------------------
-- 5. Products
--    FK → product_category_translation (nullable: some products
--    have no category in the raw data).
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS products (
    product_id                  VARCHAR(32) PRIMARY KEY,
    product_category_name       VARCHAR(100),
    product_name_length         SMALLINT,
    product_description_length  SMALLINT,
    product_photos_qty          SMALLINT,
    product_weight_g            INTEGER,
    product_length_cm           SMALLINT,
    product_height_cm           SMALLINT,
    product_width_cm            SMALLINT,

    CONSTRAINT fk_product_category
        FOREIGN KEY (product_category_name)
        REFERENCES product_category_translation (product_category_name)
        ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_products_category ON products (product_category_name);

-- -------------------------------------------------------------
-- 6. Orders  (core fact table)
--    FK → customers
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS orders (
    order_id                      VARCHAR(32) PRIMARY KEY,
    customer_id                   VARCHAR(32) NOT NULL,
    order_status                  VARCHAR(20) NOT NULL,
    order_purchase_timestamp      TIMESTAMP   NOT NULL,
    order_approved_at             TIMESTAMP,
    order_delivered_carrier_date  TIMESTAMP,
    order_delivered_customer_date TIMESTAMP,
    order_estimated_delivery_date TIMESTAMP   NOT NULL,

    CONSTRAINT fk_order_customer
        FOREIGN KEY (customer_id)
        REFERENCES customers (customer_id)
);

CREATE INDEX IF NOT EXISTS idx_orders_customer    ON orders (customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_status      ON orders (order_status);
CREATE INDEX IF NOT EXISTS idx_orders_purchase_ts ON orders (order_purchase_timestamp);

-- -------------------------------------------------------------
-- 7. Order Items  (fact detail)
--    FK → orders, products, sellers
--    Composite PK: one order can have multiple line items.
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS order_items (
    order_id             VARCHAR(32)    NOT NULL,
    order_item_id        SMALLINT       NOT NULL,
    product_id           VARCHAR(32)    NOT NULL,
    seller_id            VARCHAR(32)    NOT NULL,
    shipping_limit_date  TIMESTAMP      NOT NULL,
    price                NUMERIC(10, 2) NOT NULL,
    freight_value        NUMERIC(10, 2) NOT NULL,

    PRIMARY KEY (order_id, order_item_id),

    CONSTRAINT fk_oi_order
        FOREIGN KEY (order_id)   REFERENCES orders   (order_id),
    CONSTRAINT fk_oi_product
        FOREIGN KEY (product_id) REFERENCES products (product_id),
    CONSTRAINT fk_oi_seller
        FOREIGN KEY (seller_id)  REFERENCES sellers  (seller_id)
);

CREATE INDEX IF NOT EXISTS idx_order_items_product ON order_items (product_id);
CREATE INDEX IF NOT EXISTS idx_order_items_seller  ON order_items (seller_id);

-- -------------------------------------------------------------
-- 8. Order Payments
--    FK → orders
--    Composite PK: one order can be paid with multiple methods.
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS order_payments (
    order_id              VARCHAR(32)    NOT NULL,
    payment_sequential    SMALLINT       NOT NULL,
    payment_type          VARCHAR(20)    NOT NULL,
    payment_installments  SMALLINT       NOT NULL,
    payment_value         NUMERIC(10, 2) NOT NULL,

    PRIMARY KEY (order_id, payment_sequential),

    CONSTRAINT fk_op_order
        FOREIGN KEY (order_id) REFERENCES orders (order_id)
);

CREATE INDEX IF NOT EXISTS idx_payments_type ON order_payments (payment_type);

-- -------------------------------------------------------------
-- 9. Order Reviews
--    FK → orders
--    Composite PK (review_id, order_id): raw data has duplicate
--    review_id values across different orders.
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS order_reviews (
    review_id                VARCHAR(32) NOT NULL,
    order_id                 VARCHAR(32) NOT NULL,
    review_score             SMALLINT    NOT NULL CHECK (review_score BETWEEN 1 AND 5),
    review_comment_title     TEXT,
    review_comment_message   TEXT,
    review_creation_date     TIMESTAMP   NOT NULL,
    review_answer_timestamp  TIMESTAMP   NOT NULL,

    PRIMARY KEY (review_id, order_id),

    CONSTRAINT fk_or_order
        FOREIGN KEY (order_id) REFERENCES orders (order_id)
);

CREATE INDEX IF NOT EXISTS idx_reviews_score    ON order_reviews (review_score);
CREATE INDEX IF NOT EXISTS idx_reviews_order_id ON order_reviews (order_id);

COMMIT;
