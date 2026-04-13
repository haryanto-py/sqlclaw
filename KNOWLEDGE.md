# Olist E-Commerce Knowledge Base

This document contains business context, metric definitions, and analytical patterns
for the Olist Brazilian E-Commerce dataset. It is used as a RAG knowledge source by
the SQLClaw analytics agent.

---

## section: About Olist

Olist is a Brazilian e-commerce platform that acts as a marketplace aggregator.
Sellers list their products on Olist, which then publishes them across major
Brazilian marketplaces (Americanas, Ponto Frio, Submarino, etc.) under a single
contract. Olist handles logistics coordination, payment processing, and customer
service on behalf of sellers.

The dataset covers approximately 100,000 orders placed between October 2016 and
August 2018. It represents real transactions, anonymized for privacy. The data
includes the full order lifecycle: purchase, approval, carrier handoff, delivery,
and customer review.

---

## section: Brazilian E-Commerce Context

Brazil is one of Latin America's largest e-commerce markets. Key facts relevant to
this dataset:

- Currency is Brazilian Real (BRL, R$). All monetary values in this dataset are in BRL.
- The dataset spans a period of rapid e-commerce growth in Brazil (2016-2018).
- Delivery times in Brazil are typically longer than in Europe/US due to continental
  size and complex logistics. The average delivery in this dataset is around 12 days.
- São Paulo (SP) dominates in both customer and seller counts, being Brazil's
  economic center and most populous state.
- The North and Northeast regions (AM, PA, MA, BA) tend to have the longest
  delivery times due to geographic remoteness from distribution centers.
- Brazilian consumers frequently use installment payments (parcelamento). Credit card
  installments are extremely common — many purchases split into 2-12 installments.

---

## section: Key Business Metrics

**GMV (Gross Merchandise Value)**
Total value of all orders placed on the platform before deductions. Calculated as
the sum of `price + freight_value` across all order items. GMV is the top-line
revenue metric for a marketplace like Olist.
SQL hint: SUM(oi.price + oi.freight_value) FROM order_items oi JOIN orders o ON ...

**AOV (Average Order Value)**
GMV divided by the number of orders. Measures how much customers spend per
transaction on average. A rising AOV suggests upselling success or category mix shift.
SQL hint: SUM(price + freight_value) / COUNT(DISTINCT order_id) FROM order_items

**Order Volume**
Total count of orders in a period. Distinct from GMV — volume can grow while AOV
falls (more small orders) or vice versa.

**Conversion Rate**
Not directly measurable from this dataset (no browse/cart data), but order status
distribution gives a proxy: orders that reached "delivered" vs total orders created.

**On-Time Delivery Rate**
Percentage of delivered orders where actual delivery date ≤ estimated delivery date.
SQL hint: COUNT(*) FILTER (WHERE order_delivered_customer_date <= order_estimated_delivery_date)
/ COUNT(*) FILTER (WHERE order_status = 'delivered')

**Late Delivery Rate**
Inverse of on-time rate. High late delivery rate correlates strongly with low review scores.

**Average Review Score (NPS proxy)**
Mean of review_score (1-5 scale). Scores 4-5 are promoters, 3 is neutral, 1-2 are detractors.
SQL hint: AVG(review_score) FROM order_reviews

**Seller Performance**
Measured by: total revenue, order count, average review score, late delivery rate.
A seller with high revenue but low review scores is a risk.

**Category Revenue Share**
Which product categories drive the most GMV. Calculated by joining order_items →
products → product_category_translation.

**Freight-to-Revenue Ratio**
freight_value / price. High ratio means logistics cost is eating into product value.
Heavy or bulky categories (furniture, appliances) have high freight ratios.

**Repeat Customer Rate**
Percentage of customers with more than one order. Low in this dataset (~3%) because
it covers only 2 years and Brazilian e-commerce was still maturing.

---

## section: Order Lifecycle and Statuses

Orders in this dataset go through the following states:

- **created** — Order placed by customer, not yet approved
- **approved** — Payment approved by Olist
- **invoiced** — Invoice issued to seller
- **processing** — Seller is preparing the order
- **shipped** — Handed to carrier
- **delivered** — Customer confirmed receipt
- **canceled** — Order canceled (before or after payment)
- **unavailable** — Item became unavailable

The typical happy path: created → approved → invoiced → processing → shipped → delivered.
The most common terminal state is "delivered" (~97% of orders with a known status).

---

## section: Payment Methods

The dataset captures four payment types:

- **credit_card** — Most common (~74% of orders). Brazilian consumers frequently
  split into installments (payment_installments column). Average installments: ~3.
- **boleto** — Bank slip payment. Popular for unbanked consumers. Single payment,
  often requires 1-3 business days to clear. ~19% of orders.
- **voucher** — Store credit/gift card. Small share (~5%). Often combined with
  another payment method.
- **debit_card** — Rare (~1.5%). Single payment, instant clearance.

Multiple payment methods can be used for a single order (split payments), which is
why order_payments has a payment_sequential column and composite PK.

---

## section: Product Categories

Top revenue-generating categories in this dataset:

1. health_beauty — personal care, cosmetics
2. watches_gifts — watches, accessories, gift items
3. bed_bath_table — home linens, kitchen items
4. sports_leisure — fitness equipment, outdoor
5. computers_accessories — peripherals, cables
6. furniture_decor — home furniture, decoration
7. housewares — kitchen appliances, utensils
8. telephony — mobile phones, accessories
9. auto — car accessories and parts
10. toys — children's toys and games

Categories with highest freight-to-price ratio: furniture, office_furniture,
housewares, garden_tools (large/heavy items).

Categories with best review scores: books (4.4 avg), fashion (4.3 avg).
Categories with worst review scores: security_and_services (2.5), office_furniture (3.7).

---

## section: Geographic Insights

**Customer distribution:**
- São Paulo (SP): ~42% of all customers
- Rio de Janeiro (RJ): ~13%
- Minas Gerais (MG): ~12%
- These three states make up ~67% of all customers.

**Seller distribution:**
- São Paulo (SP): ~60% of all sellers
- Minas Gerais (MG): ~12%
- Paraná (PR): ~6%

**Delivery time by region (approximate averages):**
- Southeast (SP, RJ, MG, ES): 8-10 days
- South (PR, SC, RS): 10-12 days
- Center-West (GO, MT, MS, DF): 12-15 days
- Northeast (BA, PE, CE, MA, etc.): 15-20 days
- North (AM, PA, AC, etc.): 20-25 days

**Longest delivery routes:** Orders shipped to Amazonas (AM) or Roraima (RR)
from São Paulo sellers can take 25+ days.

---

## section: Data Limitations and Caveats

- **No customer identity**: customer_unique_id is anonymized. You cannot link a
  customer to their real-world identity, only track repeat orders.
- **No product prices over time**: price reflects the price at time of purchase.
  There is no historical price table.
- **Geolocation is approximate**: lat/lng coordinates are at zip code centroid level,
  not precise addresses. Multiple entries per zip code were deduplicated by averaging.
- **Review dates vs order dates**: Some reviews were left months after delivery.
  order_reviews.review_creation_date may significantly lag order_delivered_customer_date.
- **Canceled orders**: ~600 canceled orders are in the dataset. They have no delivery
  dates and may have null payment data. Exclude them with WHERE order_status = 'delivered'
  for delivery analysis.
- **Data ends August 2018**: Do not extrapolate trends beyond this date. The dataset
  does not represent current Olist performance.
- **product_category_name**: Two categories (pc_gamer, portateis_cozinha_e_preparadores_de_alimentos)
  had no English translation and were set to NULL in the cleaned data.

---

## section: Common Analysis Patterns

**Monthly revenue trend:**
GROUP BY DATE_TRUNC('month', order_purchase_timestamp), SUM(price + freight_value)

**Top sellers by revenue:**
JOIN order_items → orders (filter delivered) → GROUP BY seller_id → SUM(price)

**Review score distribution:**
GROUP BY review_score → COUNT(*) → good for bar chart

**Delivery performance:**
Compare order_delivered_customer_date vs order_estimated_delivery_date.
Use EXTRACT(EPOCH FROM ...) / 86400 to get days difference.

**Customer lifetime value:**
GROUP BY customer_unique_id → SUM(payment_value) FROM order_payments

**State-level heatmap:**
JOIN customers → orders → SUM or COUNT → GROUP BY customer_state

**Payment installment analysis:**
AVG(payment_installments) WHERE payment_type = 'credit_card' GROUP BY month

**Cohort analysis by order month:**
DATE_TRUNC('month', order_purchase_timestamp) as cohort, track repeat purchase rate
