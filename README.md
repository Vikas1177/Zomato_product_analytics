# Zomato Product Analytics -- GMV Growth Analysis

A product analytics project built on a synthetic simulation of Zomato's food delivery platform. The objective is to decompose Gross Merchandise Value (GMV) into its constituent levers, identify bottlenecks that suppress revenue, theorize root causes behind each bottleneck, and propose data-backed interventions to recover lost GMV.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Data Overview](#data-overview)
3. [Tech Stack](#tech-stack)
4. [Project Structure](#project-structure)
5. [How to Run](#how-to-run)
6. [GMV Decomposition Framework](#gmv-decomposition-framework)
7. [Key Metrics Summary](#key-metrics-summary)
8. [Bottleneck Analysis](#bottleneck-analysis)
9. [What Is Working Well](#what-is-working-well)
10. [Recommendations Summary](#recommendations-summary)
11. [Limitations](#limitations)
12. [License](#license)

---

## Project Overview

This project simulates a complete food delivery platform with realistic user behavior, session funnels, order dynamics, promotional effects, and operational parameters. The simulation is powered by a FastAPI backend that accepts over 20 configurable parameters (latency, payment reliability, promo mix, channel mix, delivery partner availability, etc.) and produces three interrelated datasets. The analytics layer is a Streamlit dashboard with 6 tabs and 30+ interactive charts spanning funnel analysis, retention, segmentation, monetization, and operations.

The north star metric is **GMV (Gross Merchandise Value)**. The analysis identifies 5 critical problems collectively responsible for an estimated 6.6M INR in lost annual GMV and proposes targeted fixes for each.

---

## Data Overview

The dataset is **entirely synthetic**, generated through a configurable simulation engine. It models 12 months of activity (June 2025 -- May 2026) for a food delivery platform.

### Datasets

| File | Records | Description |
|---|---|---|
| `users.csv` | 5,000 rows | One row per registered user with demographic and behavioral attributes |
| `events.csv` | ~297,000 rows | Session-level event stream capturing every step from app open through payment |
| `orders.csv` | ~33,000 rows | One row per order placed, with status, amount, promo, and delivery metadata |

### Schema: users.csv

| Column | Type | Description |
|---|---|---|
| user_id | string | Unique identifier (format: U_xxxxxxxx) |
| signup_date | datetime | Date the user registered on the platform |
| age | integer | User age (range: 18--54) |
| city | string | City name (15 cities across 3 tiers) |
| city_tier | string | Tier_1, Tier_2, or Tier_3 |
| platform | string | iOS, Android, or Web |
| acquisition_channel | string | organic, paid_search, social_media, referral, email |
| is_zomato_gold | boolean | Whether the user is a Gold subscriber |
| onboarding_cohort | string | Standard or Frictionless |
| user_type | string | power_user, regular, occasional, window_shopper |

### Schema: events.csv

| Column | Type | Description |
|---|---|---|
| event_id | string | Unique event identifier |
| session_id | string | Unique session identifier (format: S_xxxxxxxx) |
| user_id | string | Foreign key to users |
| event_time | datetime | Timestamp of the event |
| event_name | string | One of: app_open, search, view_menu, add_to_cart, checkout, payment_success, payment_failed, app_crash |
| platform | string | Platform at time of event |
| weather_at_time | string | clear or rain |
| surge_active | boolean | Whether surge pricing was active |

### Schema: orders.csv

| Column | Type | Description |
|---|---|---|
| order_id | string | Unique order identifier (format: ORD_xxxxxxxx) |
| user_id | string | Foreign key to users |
| order_time | datetime | Timestamp of order placement |
| amount_inr | float | Order value in INR |
| delivery_fee | float | Delivery fee (0 for Gold members, 40 for Standard) |
| promo_applied | string | NONE, FLAT_50, BOGO, FREE_DELIVERY, DISCOUNT_20PCT, FIRST_ORDER_DISCOUNT |
| delivery_time_mins | integer | Delivery time in minutes |
| order_status | string | Delivered or Cancelled |

### Data Characteristics

- **City distribution**: 60% Tier 1, 30% Tier 2, 10% Tier 3 users across 15 cities
- **Platform split**: 50% Android, 45% iOS, 5% Web
- **Gold membership**: ~19.1% of users are Zomato Gold subscribers
- **Age skew**: 85% of users are between 18 and 31 years old
- **Order timing**: Peak ordering occurs during dinner rush (19:00--23:00) and Saturday evenings show highest order density
- **Weather effects**: Monsoon months (June--August) increase delivery times by 20--30 minutes, raising cancellations
- **Promo distribution**: 55% of orders have no promo; FLAT_50 (15%), BOGO (12%), FREE_DELIVERY (10%), DISCOUNT_20PCT (8%) make up the rest

---

## Tech Stack

| Component | Technology |
|---|---|
| Data Generation | Python, FastAPI, Pydantic, NumPy, Pandas |
| Data Simulation UI | Streamlit |
| Analytics Dashboard | Streamlit, Plotly (Express + Graph Objects) |
| Static Charts | Plotly (exported as PNG) |
| Data Storage | CSV files |

---

## Project Structure

```
product_analytics/
|-- analytics.py                 # Streamlit dashboard (6 tabs, 30+ charts)
|-- data/
|   |-- users.csv                # 5,000 users
|   |-- events.csv               # ~297,000 session events
|   |-- orders.csv               # ~33,000 orders
|-- data_generation/
|   |-- main.py                  # FastAPI simulation engine (ZomatoDataSimulator)
|   |-- app.py                   # Streamlit UI for configuring simulation parameters
|-- plots/                       # 25 pre-rendered PNG charts
|-- product_analysis_story.md    # Narrative analysis document
```

---

## How to Run

### Prerequisites

- Python 3.9+
- pip

### Install Dependencies

```bash
pip install streamlit pandas numpy plotly fastapi uvicorn requests pydantic
```

### Generate Data (Optional -- data is pre-generated)

Start the FastAPI backend:

```bash
cd data_generation
uvicorn main:app --reload --port 8000
```

Then launch the data generation UI:

```bash
streamlit run data_generation/app.py
```

Configure simulation parameters and generate the dataset via the UI. The default configuration produces 5,000 users over 12 months with a Web platform payment gateway outage enabled.

### Run the Analytics Dashboard

```bash
streamlit run analytics.py
```

The dashboard opens with 6 tabs: Overview, Funnel & Activation, Retention, Segmentation, Monetization, and Operations. Each tab includes segment filters for date range, age, city tier, platform, Gold status, onboarding cohort, city, and acquisition channel.

---

## GMV Decomposition Framework

GMV is decomposed as a product of sequential levers:

```
GMV = Active Users x Orders/User x Average Order Value (AOV)
```

Through the funnel lens:

```
GMV = App Opens x Funnel Conversion % x (1 - Cancel Rate) x AOV
```

| Lever | Current Value | Benchmark | Gap |
|---|---|---|---|
| Total Users | 5,000 | -- | -- |
| Users Who Ordered | 2,835 (56.7%) | 70%+ | -13.3pp |
| End-to-End Funnel Conversion | 11.1% | 15%+ | -3.9pp |
| Cancel Rate | 4.1% | <3% | +1.1pp |
| AOV | 711 INR | 750+ INR | -39 INR |
| Repeat Rate (>1 order) | 69.3% | 75%+ | -5.7pp |
| Monthly GMV (latest, May 2026) | 6.25M INR | -- | Growing 42% MoM |

---

## Key Metrics Summary

### North Star Metrics

| Metric | Value |
|---|---|
| Total Delivered GMV | 22.59M INR |
| Monthly Active Ordering Users (latest) | 1,628 |
| Orders per Active User | 11.3 |
| Average Order Value | 711 INR |
| Average Customer LTV | 8,062 INR |
| Repeat Order Rate | 69.3% |
| Gold GMV Share | 82.5% |

### Platform Health

| Metric | Value | Target | Status |
|---|---|---|---|
| Funnel Conversion | 11.1% | 15% | Below target |
| Gold Adoption | 19.1% | 30% | Below target |
| Crash Rate | 1.87% | <1% | Above target |
| Payment Failure Rate | 7.2% | <5% | Above target |
| Cancel Rate | 4.1% | <5% | Within target |

### Retention

| Metric | Value |
|---|---|
| D1 Retention | 29.2% |
| D7 Retention | 31.9% |
| D30 Retention | 28.0% |
| D1 to D30 Erosion | 1.2pp (96% of D1 retained at D30) |

---

## Bottleneck Analysis

### Bottleneck 1: Funnel Leak at Search to View Menu (46.9% conversion)

**Data**

The conversion funnel shows six steps from app open to payment success. The largest single-step drop occurs between Search and View Menu, where only 46.9% of sessions that perform a search proceed to view a restaurant menu. By comparison, App Open to Search converts at 88.1%, and all subsequent steps convert between 62% and 66%.

| Funnel Step | Sessions | Step Conversion | Cumulative |
|---|---|---|---|
| App Open | 297,422 | -- | 100% |
| Search | 261,942 | 88.1% | 88.1% |
| View Menu | 122,943 | 46.9% | 41.3% |
| Add to Cart | 76,234 | 62.0% | 25.6% |
| Checkout | 50,648 | 66.4% | 17.0% |
| Payment Success | 33,137 | 65.4% | 11.1% |

**Estimated GMV impact**: Improving this step from 46.9% to 55% would push approximately 5,300 additional sessions to payment, translating to roughly 3.8M INR in annual GMV uplift.

**Theorized root causes**:
- Search ranking relies on distance alone without incorporating cuisine match, restaurant rating, or estimated delivery time
- Search results present too many unranked options, causing decision paralysis
- Estimated delivery times or price ranges shown on search result cards create sticker shock before users click into a menu
- No intent-based recommendations surface for specific queries (a search for "biryani" shows a generic list instead of top-rated biryani restaurants)

**Proposed solutions**:
- A/B test a personalized search ranking model that weights past cuisine preference, rating, and delivery ETA
- Add a "Quick Picks" carousel on search results showing 3 personalized recommendations
- Display ETA and price range on search result cards to set expectations
- Implement search autocomplete with cuisine tags to reduce friction from typos and vague queries

---

### Bottleneck 2: Web Platform Payment Failure (96.5% failure rate)

**Data**

The payment failure rate by platform reveals Web at 96.5% compared to Android at 2.1% and iOS at 2.0%. Out of 14,232 web sessions across the analysis period, only 65 orders were delivered.

| Metric | Android | iOS | Web |
|---|---|---|---|
| Sessions | 151,270 | 133,486 | 14,232 |
| Delivered Orders | 17,713 | 13,984 | 65 |
| Payment Failure Rate | 2.1% | 2.0% | 96.5% |

**Estimated GMV impact**: 14,232 sessions at 11.1% expected conversion and 711 INR AOV equals approximately 1.1M INR in lost GMV from web payment failures alone.

**Theorized root causes**:
- A broken payment gateway integration on web, likely involving tokenization, 3DS redirect, or session timeout during the checkout flow
- Web checkout lacks saved cards, UPI deep-links, and wallet integrations available on mobile apps
- Web traffic skews toward first-time, low-intent users from SEO or ad channels, though the 96.5% failure rate indicates a technical rather than behavioral issue

**Proposed solutions**:
- P0 engineering fix for the web payment gateway (this is likely a single ticket yielding 1.1M INR in recovered GMV)
- Add UPI QR code fallback for web checkout
- Implement a "Continue on App" deep-link nudge for web users at checkout that preserves the cart state

---

### Bottleneck 3: Activation Crisis (43.3% of users never order)

**Data**

Of 5,000 registered users, 2,165 (43.3%) never placed a single order. Activation rates vary significantly by onboarding cohort: Frictionless onboarding achieves 66.3% versus 47.3% for Standard, a 19 percentage point gap. Gold members activate at 98.0% while non-Gold activates at 46.9%.

| Segment | Activation Rate |
|---|---|
| Overall | 56.7% |
| Frictionless Onboarding | 66.3% |
| Standard Onboarding | 47.3% |
| Gold Members | 98.0% |
| Non-Gold | 46.9% |
| Android | 57.8% |
| iOS | 60.0% |
| Web | 14.3% |

**Estimated GMV impact**: Converting even 30% of the 2,165 inactive users at 711 INR AOV yields 461K INR in incremental GMV.

**Theorized root causes**:
- Standard onboarding involves too many steps (forced location setup, payment registration) before users can browse
- The FIRST_ORDER_DISCOUNT promo was used only 56 times across the entire dataset (0.16% of orders), suggesting it is either not surfaced to new users or the discount is not compelling
- No re-engagement mechanism exists for users who sign up but do not order within the first 24--48 hours

**Proposed solutions**:
- Migrate all new users to the Frictionless onboarding flow, which the data proves activates 19pp more users
- Trigger a push notification with 100 INR discount within 24 hours of signup for users who have not ordered
- Surface personalized restaurant suggestions during onboarding based on detected location
- Implement a "First Bite Free" campaign (free delivery plus 50 INR off first order) prominently shown on the app home screen for new users

---

### Bottleneck 4: Delivery Time Cliff at 45 Minutes (18--27% cancellation rate)

**Data**

Cancellation rate remains flat at 1.8% for deliveries under 45 minutes. It spikes to 18.2% for 45--60 minute deliveries and 27.2% for deliveries exceeding 60 minutes. This is a 10x increase at the 45-minute threshold.

| Delivery Time Bucket | Cancellation Rate |
|---|---|
| <30 mins | 1.8% |
| 30--45 mins | 1.8% |
| 45--60 mins | 18.2% |
| >60 mins | 27.2% |

The delivery time distribution histogram shows a steep drop-off beyond 45 minutes, with a long tail extending to ~75 minutes. The long tail corresponds to rain-affected deliveries during monsoon months.

**Estimated GMV impact**: 1,375 total cancellations at 711 INR AOV equals 978K INR in cancelled GMV. Since orders exceeding 45 minutes drive approximately 80% of cancellations, addressing this recovers an estimated 780K INR.

**Theorized root causes**:
- Some restaurants have preparation times exceeding 30 minutes; combined with delivery partner transit, total time crosses 45 minutes
- During surge periods (rain, weekend dinner rush), delivery partner availability decreases, stretching delivery times
- ETA estimation is inaccurate, and the gap between promised and actual delivery time triggers cancellations rather than the absolute wait
- Orders that exceed 45 minutes without proactive communication are cancelled at higher rates

**Proposed solutions**:
- Cap ETA promises at 45 minutes; if estimated prep plus delivery exceeds this, display a warning or deprioritize the restaurant in search results
- Send a proactive delay notification at the 35-minute mark with an updated ETA
- Offer a 30 INR discount coupon for the next order when delivery exceeds the promised ETA
- Deprioritize restaurants that consistently exceed 45-minute delivery times in search rankings

---

### Bottleneck 5: Tier 2/3 Cities Undermonetized (36% lower AOV)

**Data**

Tier 1 cities generate 73.6% of total GMV with an AOV of 768 INR. Tier 2 contributes 19.8% at 633 INR AOV. Tier 3 contributes 6.6% at 491 INR AOV. The AOV gap between Tier 1 and Tier 3 is 277 INR (36%).

| City Tier | GMV | AOV | Orders | GMV Share |
|---|---|---|---|---|
| Tier 1 | 16.6M INR | 768 INR | 21,665 | 73.6% |
| Tier 2 | 4.5M INR | 633 INR | 7,070 | 19.8% |
| Tier 3 | 1.5M INR | 491 INR | 3,027 | 6.6% |

At the city level, the lowest-performing cities are Surat (481 INR AOV), Patna (493 INR AOV), and Bhopal (~486 INR AOV), all Tier 3.

**Estimated GMV impact**: Raising Tier 2/3 AOV by 15% through upselling and supply improvements would yield approximately 500K INR in incremental GMV.

**Theorized root causes**:
- Fewer premium or branded restaurants available in Tier 2/3 cities limits average ticket size
- Higher price sensitivity among Tier 2/3 users, with greater dependence on discounts
- Smaller basket sizes driven by single-person ordering rather than family-size orders
- Limited cuisine variety reduces exploration and cross-selling opportunity

**Proposed solutions**:
- Introduce "Meal Combos" for Tier 2/3 (Main + Side + Drink at a slight discount) to push basket size from 491 to 600+ INR
- Accelerate restaurant onboarding in Tier 2/3 cities, targeting premium and branded restaurants
- Implement contextual upselling at checkout ("Add a dessert for just 49 INR") targeted at Tier 2/3 users with low cart values
- Set a free delivery threshold ("Free delivery on orders above 500 INR") to nudge users toward larger baskets

---

## What Is Working Well

### Zomato Gold as a GMV Engine

Gold members constitute 19.1% of the user base but drive 82.5% of total GMV. Their repeat rate is 98.5% versus 54.9% for Standard users. Median orders per Gold user is 23 compared to 2 for Standard. Every 1 percentage point increase in Gold adoption translates to approximately 186K INR in additional GMV.

| Metric | Gold | Standard |
|---|---|---|
| GMV Contribution | 18.6M INR (82.5%) | 3.9M INR (17.5%) |
| AOV | 719 INR | 675 INR |
| Repeat Rate | 98.5% | 54.9% |
| Median Orders/User | 23 | 2 |
| Activation Rate | 98.0% | 46.9% |

### Monthly GMV Compounding

GMV grew from approximately 71K INR in June 2025 to 6.25M INR in May 2026. Both order volume and GMV show consistent month-over-month growth, with the order volume line and GMV bars rising in parallel.

### BOGO Promo Drives Highest AOV

BOGO produces 805 INR AOV, 12% higher than no-promo orders at 717 INR. FREE_DELIVERY achieves 753 INR AOV. DISCOUNT_20PCT reduces AOV to 587 INR, an 18% decrease versus baseline, indicating margin erosion without basket size gains.

| Promo | AOV | Orders |
|---|---|---|
| BOGO | 805 INR | 5,597 |
| FREE_DELIVERY | 753 INR | 5,195 |
| NONE | 717 INR | 11,720 |
| FLAT_50 | 659 INR | 7,083 |
| DISCOUNT_20PCT | 587 INR | 3,486 |

### Referral Channel Delivers Highest LTV

Average customer LTV by acquisition channel: Referral (12,504 INR) leads all channels, followed by Organic (8,828 INR), Email (8,029 INR), Social Media (7,305 INR), and Paid Search (6,336 INR). Referral users also show the highest retention over time, maintaining approximately 30% retention at month 5 compared to 17--22% for other channels.

### Strong Retention Curve

D1 to D30 erosion is only 1.2 percentage points (29.2% to 28.0%), meaning 96% of users who return on Day 1 are still active at Day 30. This indicates that once users are activated, the product retains them effectively.

---

## Recommendations Summary

| Problem | Root Cause | Estimated GMV Impact | Fix Complexity | Priority |
|---|---|---|---|---|
| Search to Menu drop (46.9%) | Poor search ranking | 3.8M INR | Medium (ML/algo) | High |
| Web payment 96.5% failure | Broken gateway | 1.1M INR | Low (bug fix) | Critical |
| 43.3% never order | Onboarding friction | 461K INR | Low (product) | High |
| 45+ min delivery cancellations | Slow restaurants, no communication | 780K INR | Medium (ops) | Medium |
| Tier 2/3 low AOV | Limited supply, no upselling | 500K INR | Medium (growth) | Medium |
| **Total Recoverable GMV** | | **~6.6M INR** | | |

Prioritized execution order:
1. Fix the web payment gateway -- highest ROI at 1.1M INR for likely a single engineering sprint
2. Migrate all users to Frictionless onboarding -- proven 19pp activation improvement
3. Invest in search ranking ML -- highest absolute impact at 3.8M INR but requires more resources
4. Implement proactive delay notifications and ETA caps at 45 minutes
5. Launch Tier 2/3 upselling and free delivery threshold programs

---


## Limitations

- The dataset is synthetic. All patterns, distributions, and anomalies (such as the Web payment failure) were deliberately injected via simulation parameters. Real-world data would contain noise patterns and confounding variables not present here.
- Weather and surge pricing effects are sparsely matched to orders via merge_asof with a 2-minute tolerance, producing many null enrichments. These dimensions were excluded from the final analysis.
- User type labels (power_user, window_shopper, etc.) are pre-assigned during data generation rather than derived from behavioral signals. In production, RFM segmentation or clustering would replace these labels.
- The simulation does not model restaurant-side behavior, delivery partner logistics, or customer support interactions. Cancellation logic is a simplified function of delivery time and support quality parameters.
- Cohort retention analysis is limited by the 12-month simulation window. Longer time horizons would be needed to observe steady-state retention behavior.

---

## License

This project is for educational and portfolio purposes. The dataset is synthetic and does not contain any real user data.
