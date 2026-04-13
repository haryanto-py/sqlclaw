"""
Unit tests for utils/clean_data.py.

Each test targets a specific cleaning behaviour so that a regression in one
function doesn't mask bugs in another.  All tests use minimal in-memory
DataFrames — no files, no database, no network.
"""

import pandas as pd
import pytest

from utils.clean_data import (
    clean_category_translation,
    clean_customers,
    clean_geolocation,
    clean_order_items,
    clean_order_payments,
    clean_order_reviews,
    clean_orders,
    clean_products,
    clean_sellers,
)

# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def sample_translation():
    return pd.DataFrame(
        {
            "product_category_name": [
                "beleza_saude",
                "home_confort",
                "home_appliances_2",
                "home_confort",
            ],
            "product_category_name_english": [
                "health_beauty",
                "home_confort",
                "home_appliances_2",
                "home_confort",
            ],
        }
    )


@pytest.fixture
def clean_translation(sample_translation):
    return clean_category_translation(sample_translation)


@pytest.fixture
def sample_products(clean_translation):
    return pd.DataFrame(
        {
            "product_id": ["p1", "p2", "p3"],
            "product_category_name": ["beleza_saude", "pc_gamer", None],
            "product_name_lenght": [10, 20, 30],  # intentional typo
            "product_description_lenght": [100, 200, 300],  # intentional typo
            "product_photos_qty": [1, 2, None],
            "product_weight_g": [500, None, 300],
            "product_length_cm": [10, 20, 30],
            "product_height_cm": [5, 10, 15],
            "product_width_cm": [8, None, 12],
        }
    )


@pytest.fixture
def sample_customers():
    return pd.DataFrame(
        {
            "customer_id": ["c1", "c2", "c1"],  # c1 is a duplicate
            "customer_unique_id": ["u1", "u2", "u1"],
            "customer_zip_code_prefix": [1001, 20040, 1001],  # int, leading zero will be lost
            "customer_city": ["SAO PAULO", "rio de janeiro", "SAO PAULO"],
            "customer_state": ["sp", "rj", "sp"],
        }
    )


@pytest.fixture
def sample_orders():
    return pd.DataFrame(
        {
            "order_id": ["o1", "o2", "o3"],
            "customer_id": ["c1", "c2", None],  # o3 has null customer
            "order_status": ["delivered", "canceled", "delivered"],
            "order_purchase_timestamp": ["2017-01-01 10:00:00", "2017-06-15 12:00:00", None],
            "order_approved_at": ["2017-01-01 11:00:00", None, None],
            "order_delivered_carrier_date": [None, None, None],
            "order_delivered_customer_date": [None, None, None],
            "order_estimated_delivery_date": ["2017-01-15", "2017-07-01", None],
        }
    )


# ── category_translation ──────────────────────────────────────────────────────


def test_translation_typo_home_confort_fixed(clean_translation):
    assert "home_comfort" in clean_translation["product_category_name_english"].values


def test_translation_typo_home_appliances_2_fixed(clean_translation):
    assert "home_appliances" in clean_translation["product_category_name_english"].values


def test_translation_duplicate_pk_dropped(clean_translation):
    assert clean_translation["product_category_name"].duplicated().sum() == 0


# ── products ──────────────────────────────────────────────────────────────────


def test_products_column_typo_renamed(sample_products, clean_translation):
    result = clean_products(sample_products, clean_translation)
    assert "product_name_length" in result.columns
    assert "product_description_length" in result.columns
    assert "product_name_lenght" not in result.columns


def test_products_unmapped_category_nulled(sample_products, clean_translation):
    # "pc_gamer" is not in the translation table → should become NULL
    result = clean_products(sample_products, clean_translation)
    pc_gamer_rows = result[result["product_id"] == "p2"]
    assert pc_gamer_rows["product_category_name"].isna().all()


def test_products_null_dimensions_filled(sample_products, clean_translation):
    result = clean_products(sample_products, clean_translation)
    assert result["product_weight_g"].isna().sum() == 0
    assert result["product_width_cm"].isna().sum() == 0
    assert result["product_photos_qty"].isna().sum() == 0


def test_products_all_rows_kept(sample_products, clean_translation):
    # Rows with null category are kept (FK is nullable)
    result = clean_products(sample_products, clean_translation)
    assert len(result) == len(sample_products)


# ── customers ─────────────────────────────────────────────────────────────────


def test_customers_zip_zero_padded():
    result = clean_customers(
        pd.DataFrame(
            {
                "customer_id": ["c1"],
                "customer_unique_id": ["u1"],
                "customer_zip_code_prefix": [1001],
                "customer_city": ["Sao Paulo"],
                "customer_state": ["SP"],
            }
        )
    )
    assert result["customer_zip_code_prefix"].iloc[0] == "01001"


def test_customers_city_title_cased(sample_customers):
    result = clean_customers(sample_customers)
    assert result["customer_city"].iloc[0] == "Sao Paulo"
    assert result["customer_city"].iloc[1] == "Rio De Janeiro"


def test_customers_state_uppercased(sample_customers):
    result = clean_customers(sample_customers)
    assert result["customer_state"].iloc[0] == "SP"


def test_customers_duplicates_dropped(sample_customers):
    result = clean_customers(sample_customers)
    assert len(result) == 2  # c1 duplicate removed


# ── sellers ───────────────────────────────────────────────────────────────────


def test_sellers_zip_zero_padded():
    result = clean_sellers(
        pd.DataFrame(
            {
                "seller_id": ["s1"],
                "seller_zip_code_prefix": [4538],
                "seller_city": ["curitiba"],
                "seller_state": ["pr"],
            }
        )
    )
    assert result["seller_zip_code_prefix"].iloc[0] == "04538"
    assert result["seller_city"].iloc[0] == "Curitiba"
    assert result["seller_state"].iloc[0] == "PR"


# ── orders ────────────────────────────────────────────────────────────────────


def test_orders_timestamps_parsed(sample_orders):
    result = clean_orders(sample_orders)
    assert pd.api.types.is_datetime64_any_dtype(result["order_purchase_timestamp"])
    assert pd.api.types.is_datetime64_any_dtype(result["order_approved_at"])


def test_orders_null_required_cols_dropped(sample_orders):
    # o3 has null order_purchase_timestamp AND null order_estimated_delivery_date → dropped
    result = clean_orders(sample_orders)
    assert "o3" not in result["order_id"].values


def test_orders_legitimate_null_delivery_kept(sample_orders):
    # Null delivery dates are valid (order not yet delivered) — must NOT be dropped
    result = clean_orders(sample_orders)
    assert result["order_delivered_carrier_date"].isna().sum() > 0


def test_orders_duplicates_dropped():
    df = pd.DataFrame(
        {
            "order_id": ["o1", "o1"],
            "customer_id": ["c1", "c1"],
            "order_status": ["delivered", "delivered"],
            "order_purchase_timestamp": ["2017-01-01", "2017-01-01"],
            "order_approved_at": [None, None],
            "order_delivered_carrier_date": [None, None],
            "order_delivered_customer_date": [None, None],
            "order_estimated_delivery_date": ["2017-01-15", "2017-01-15"],
        }
    )
    result = clean_orders(df)
    assert len(result) == 1


# ── order_items ───────────────────────────────────────────────────────────────


def test_order_items_orphan_orders_dropped():
    df = pd.DataFrame(
        {
            "order_id": ["o1", "o_orphan"],
            "order_item_id": [1, 1],
            "product_id": ["p1", "p1"],
            "seller_id": ["s1", "s1"],
            "shipping_limit_date": ["2017-01-10", "2017-01-10"],
            "price": [99.99, 49.99],
            "freight_value": [10.00, 5.00],
        }
    )
    result = clean_order_items(
        df,
        valid_order_ids={"o1"},
        valid_product_ids={"p1"},
        valid_seller_ids={"s1"},
    )
    assert "o_orphan" not in result["order_id"].values
    assert len(result) == 1


def test_order_items_price_rounded():
    df = pd.DataFrame(
        {
            "order_id": ["o1"],
            "order_item_id": [1],
            "product_id": ["p1"],
            "seller_id": ["s1"],
            "shipping_limit_date": ["2017-01-10"],
            "price": [99.999],
            "freight_value": [10.001],
        }
    )
    result = clean_order_items(df, {"o1"}, {"p1"}, {"s1"})
    assert result["price"].iloc[0] == pytest.approx(100.00, abs=0.001)
    assert result["freight_value"].iloc[0] == pytest.approx(10.00, abs=0.001)


# ── order_payments ────────────────────────────────────────────────────────────


def test_order_payments_orphans_dropped():
    df = pd.DataFrame(
        {
            "order_id": ["o1", "o_orphan"],
            "payment_sequential": [1, 1],
            "payment_type": ["credit_card", "boleto"],
            "payment_installments": [1, 1],
            "payment_value": [100.0, 50.0],
        }
    )
    result = clean_order_payments(df, valid_order_ids={"o1"})
    assert len(result) == 1


def test_order_payments_zero_value_kept():
    # Zero-value voucher payments are valid and must not be dropped
    df = pd.DataFrame(
        {
            "order_id": ["o1"],
            "payment_sequential": [1],
            "payment_type": ["voucher"],
            "payment_installments": [1],
            "payment_value": [0.0],
        }
    )
    result = clean_order_payments(df, valid_order_ids={"o1"})
    assert len(result) == 1


# ── order_reviews ─────────────────────────────────────────────────────────────


def test_order_reviews_invalid_score_dropped():
    df = pd.DataFrame(
        {
            "review_id": ["r1", "r2"],
            "order_id": ["o1", "o1"],
            "review_score": [5, 6],  # score 6 is invalid
            "review_comment_title": [None, None],
            "review_comment_message": [None, None],
            "review_creation_date": ["2017-02-01", "2017-02-01"],
            "review_answer_timestamp": ["2017-02-02", "2017-02-02"],
        }
    )
    result = clean_order_reviews(df, valid_order_ids={"o1"})
    assert 6 not in result["review_score"].values


def test_order_reviews_true_duplicates_dropped():
    df = pd.DataFrame(
        {
            "review_id": ["r1", "r1"],
            "order_id": ["o1", "o1"],  # same composite PK
            "review_score": [4, 4],
            "review_comment_title": [None, None],
            "review_comment_message": [None, None],
            "review_creation_date": ["2017-02-01", "2017-02-01"],
            "review_answer_timestamp": ["2017-02-02", "2017-02-02"],
        }
    )
    result = clean_order_reviews(df, valid_order_ids={"o1"})
    assert len(result) == 1


def test_order_reviews_null_comments_kept():
    # Star-only reviews (null comment) are valid
    df = pd.DataFrame(
        {
            "review_id": ["r1"],
            "order_id": ["o1"],
            "review_score": [3],
            "review_comment_title": [None],
            "review_comment_message": [None],
            "review_creation_date": ["2017-02-01"],
            "review_answer_timestamp": ["2017-02-02"],
        }
    )
    result = clean_order_reviews(df, valid_order_ids={"o1"})
    assert len(result) == 1
    assert result["review_comment_message"].isna().all()


# ── geolocation ───────────────────────────────────────────────────────────────


def test_geolocation_deduplicated_to_one_row_per_zip():
    df = pd.DataFrame(
        {
            "geolocation_zip_code_prefix": ["01001", "01001", "01001"],
            "geolocation_lat": [-23.5, -23.6, -23.4],
            "geolocation_lng": [-46.6, -46.7, -46.5],
            "geolocation_city": ["Sao Paulo", "Sao Paulo", "São Paulo"],
            "geolocation_state": ["SP", "SP", "SP"],
        }
    )
    result = clean_geolocation(df)
    assert len(result) == 1


def test_geolocation_out_of_bounds_removed():
    df = pd.DataFrame(
        {
            "geolocation_zip_code_prefix": ["01001", "99999"],
            "geolocation_lat": [-23.5, 90.0],  # 90.0 is outside Brazil
            "geolocation_lng": [-46.6, -46.6],
            "geolocation_city": ["Sao Paulo", "Invalid"],
            "geolocation_state": ["SP", "XX"],
        }
    )
    result = clean_geolocation(df)
    assert len(result) == 1
    assert "99999" not in result["geolocation_zip_code_prefix"].values


def test_geolocation_zip_zero_padded():
    df = pd.DataFrame(
        {
            "geolocation_zip_code_prefix": [1001],
            "geolocation_lat": [-23.5],
            "geolocation_lng": [-46.6],
            "geolocation_city": ["sao paulo"],
            "geolocation_state": ["sp"],
        }
    )
    result = clean_geolocation(df)
    assert result["geolocation_zip_code_prefix"].iloc[0] == "01001"


def test_geolocation_lat_lng_averaged():
    df = pd.DataFrame(
        {
            "geolocation_zip_code_prefix": ["01001", "01001"],
            "geolocation_lat": [-23.0, -24.0],
            "geolocation_lng": [-46.0, -47.0],
            "geolocation_city": ["Sao Paulo", "Sao Paulo"],
            "geolocation_state": ["SP", "SP"],
        }
    )
    result = clean_geolocation(df)
    assert result["geolocation_lat"].iloc[0] == pytest.approx(-23.5)
    assert result["geolocation_lng"].iloc[0] == pytest.approx(-46.5)
