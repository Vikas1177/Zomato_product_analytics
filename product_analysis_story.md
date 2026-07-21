# 🍔 Zomato Product Analytics — GMV Deep Dive & Interview Story

> **North Star Metric: GMV (Gross Merchandise Value)**
> A complete product analysis of Zomato's user journey, identifying where and why GMV is leaking, and what to do about it.

---

## 📊 The Business Context (How to Open in an Interview)

> *"I built a product analytics project simulating Zomato's food delivery platform — 5,000 users, 33,000+ orders, 297,000+ sessions over 12 months. My north star metric was **GMV** (₹22.6M total delivered GMV). I decomposed GMV into its component levers, identified 5 critical problems costing an estimated ₹8–12M in annual GMV, and proposed data-backed interventions for each."*

---

## 🧮 GMV Decomposition — The Framework

GMV is not one number. It's a **product of levers**:

```
GMV = Active Users × Orders/User × Average Order Value (AOV)
```

Or more granularly through the funnel:

```
GMV = App Opens × Funnel Conversion % × (1 – Cancel Rate) × AOV
```

| Lever | Current Value | Benchmark | Gap |
|---|---|---|---|
| Total Users | 5,000 | — | — |
| Users Who Ever Ordered | 2,835 (56.7%) | 70%+ | **−13.3pp** |
| End-to-End Funnel Conversion | 11.1% | 15%+ | **−3.9pp** |
| Cancel Rate | 4.1% | <3% | **+1.1pp** |
| AOV | ₹711 | ₹750+ | **−₹39** |
| Repeat Rate (>1 order) | 69.3% | 75%+ | **−5.7pp** |
| Monthly GMV (latest, May '26) | ₹6.25M | — | Growing 42% MoM |

---

## 🔍 The 5 Critical GMV Problems (With Root Causes)

---

### Problem 1: 🚨 Massive Funnel Leak — Search → View Menu (46.9% conversion)

**The Data:**

| Funnel Step | Sessions | Step Conversion | Cumulative |
|---|---|---|---|
| App Open | 297,422 | — | 100% |
| Search | 261,942 | **88.1%** ✅ | 88.1% |
| View Menu | 122,943 | **46.9%** 🔴 | 41.3% |
| Add to Cart | 76,234 | 62.0% | 25.6% |
| Checkout | 50,648 | 66.4% | 17.0% |
| Payment Success | 33,137 | 65.4% | **11.1%** |

**The Insight:** The single biggest drop in the entire funnel is **Search → View Menu**. Over **half the users** (53.1%) who search for food never click into a restaurant menu. This is the #1 GMV killer.

**Why This Matters for GMV:** If we improve this step from 46.9% → 55%, holding everything else constant:
- Additional sessions reaching payment: ~5,300
- Estimated GMV uplift: **₹3.8M annually** (~17% increase)

**Root Causes (What You'd Say in an Interview):**
1. **Poor search relevance** — Users search but don't find what they want. The search algorithm may be ranking restaurants by distance alone, not by cuisine match, rating, or delivery time.
2. **Missing intent-based recommendations** — When a user searches "biryani", they should see the top 3 biryani places with ratings + ETA, not a generic list of 50 restaurants.
3. **No filters or too many results** — Analysis paralysis. Users abandon when faced with too many unranked options.
4. **Price/ETA shock on search results** — If the search results page shows "45 mins delivery" or high prices, users bounce before even viewing a menu.

**Recommendations:**
- **A/B test personalized search ranking** — Rank results by (past cuisine preference × rating × delivery ETA), not just distance
- **Add "Quick Picks" carousel** on search results — Show 3 personalized recommendations based on past orders
- **Show ETA + price range on search cards** — Set expectations before the click
- **Implement search autocomplete with cuisine tags** — Reduce friction from typos and vague queries

---

### Problem 2: 🌐 Web Platform is a Black Hole (14.3% activation, 96.5% payment failure)

**The Data:**

| Metric | Android | iOS | Web |
|---|---|---|---|
| Activation Rate | 57.8% | 60.0% | **14.3%** 🔴 |
| Sessions | 151,270 | 133,486 | 14,232 |
| Delivered Orders | 17,713 | 13,984 | **65** |
| Payment Success | 18,500 | 14,570 | **67** |
| Payment Failed | 395 | 295 | **1,864** 🔴 |
| **Payment Failure Rate** | **2.1%** | **2.0%** | **96.5%** 🔴 |

**The Insight:** Web has a **96.5% payment failure rate** compared to ~2% on mobile apps. Out of 14,232 web sessions, only 65 orders were ever delivered. This is not a product problem — this is a **broken payment gateway on web**.

**GMV Impact:** 14,232 sessions × 11.1% expected conversion × ₹711 AOV = **₹1.1M in lost GMV** just from web payment failures.

**Root Causes:**
1. **Payment gateway integration is broken on web** — The 96.5% failure rate is not user behavior, it's a technical bug. Likely a tokenization issue, 3DS redirect failing, or session timeout on the web checkout flow.
2. **No mobile-like UX on web** — Web checkout may lack saved cards, UPI deep-links, or wallet integration that mobile apps have.
3. **Web users may be first-time/low-intent** — Web traffic could be SEO/ad-driven with lower purchase intent, but the payment failure rate alone explains 95%+ of the problem.

**Recommendations:**
- **P0 bug fix: Fix web payment gateway** — This is likely a single engineering ticket worth ₹1.1M+ in recovered GMV
- **Add UPI QR code fallback for web checkout** — Even if card payments fail, give users a scannable QR
- **Implement "Continue on App" nudge** — For web users at checkout, deep-link them to the mobile app with cart preserved

---

### Problem 3: 📉 43.3% of Users Never Place a Single Order (Activation Crisis)

**The Data:**

| Segment | Activation Rate |
|---|---|
| Overall | **56.7%** (2,835 of 5,000 users) |
| Frictionless Onboarding | **66.3%** ✅ |
| Standard Onboarding | **47.3%** 🔴 |
| Gold Members | **98.0%** ✅ |
| Non-Gold | **46.9%** 🔴 |
| Android | 57.8% |
| iOS | 60.0% |
| Web | **14.3%** 🔴 |

**The Insight:** **2,165 users signed up but never ordered.** That's 43.3% of the user base generating exactly ₹0 GMV. The Frictionless onboarding cohort activates 19pp better than Standard (66.3% vs 47.3%), proving that onboarding design directly impacts GMV.

**GMV Impact:** If we move non-activated users to even a 1-order state:
- 2,165 users × 30% realistic conversion × ₹711 AOV = **₹461K incremental GMV**

**Root Causes:**
1. **Standard onboarding is too long/complex** — The 19pp gap between Frictionless (66.3%) and Standard (47.3%) proves friction kills activation. Likely too many sign-up steps, no skip options, or forced location/payment setup.
2. **No "first order" incentive for Standard users** — FIRST_ORDER_DISCOUNT promo was used only 53 times (0.16% of all orders). It's either not shown to new users or the discount isn't compelling enough.
3. **No re-engagement for signed-up-but-never-ordered users** — These 2,165 users likely downloaded the app, browsed, and left. No push notification, email, or in-app nudge brought them back.

**Recommendations:**
- **Migrate all new users to Frictionless onboarding** — The data proves it works. This alone could improve activation by 19pp for Standard cohort users.
- **Trigger a ₹100-off push notification within 24 hours of signup** for users who haven't ordered
- **Show personalized restaurant suggestions during onboarding** based on location detection — don't make users search cold
- **Implement a "First Bite Free" campaign** — Offer free delivery + ₹50 off on first order, prominently shown on app home for new users

---

### Problem 4: 💸 Delivery Time > 45 mins Causes 18–27% Cancellations

**The Data:**

| Delivery Time Bucket | Cancellation Rate |
|---|---|
| < 30 mins | **1.8%** ✅ |
| 30–45 mins | **1.8%** ✅ |
| 45–60 mins | **18.2%** 🔴 |
| > 60 mins | **27.2%** 🔴 |

**The Insight:** There's a **cliff at 45 minutes**. Cancellation rate jumps from ~1.8% to 18.2% (10× increase) once delivery crosses 45 minutes. Beyond 60 minutes, it's 27.2% — meaning 1 in 4 orders get cancelled.

**GMV Impact:** 
- Total cancellations: 1,375 orders
- At ₹711 AOV, that's **₹978K in cancelled GMV**
- If we reduce 45+ min deliveries (which cause ~80% of cancellations), we recover an estimated **₹780K**

**Root Causes:**
1. **Long-tail restaurants with slow kitchen times** — Some restaurants take 30+ minutes to prepare, and by the time the delivery partner arrives + transit, it crosses 45 minutes.
2. **Surge pricing → no delivery partners available** — During surge periods, delivery partners may be fewer, stretching delivery times.
3. **Poor ETA estimation** — Users expect 30 minutes but get 50. The mismatch, not the absolute time, triggers cancellations.
4. **No user communication during delay** — Orders that cross 45 minutes without a proactive "Your order is delayed but on its way" update get cancelled.

**Recommendations:**
- **Hard-cap ETA promises at 45 minutes** — If a restaurant's estimated prep + delivery > 45 min, either show a warning or don't show that restaurant in default results
- **Proactive delay notification at 35 minutes** — "Your food is being freshly prepared! Expected in 10 more minutes" reduces cancellation anxiety
- **Offer ₹30 discount coupon for next order** if delivery exceeds promised ETA — turns a negative experience into retention
- **Deprioritize slow restaurants in search ranking** — Restaurants consistently exceeding 45-min delivery should be ranked lower

---

### Problem 5: 🏙️ Tier 2/3 Cities are Undermonetized (31% of orders but 36% lower AOV)

**The Data:**

| City Tier | GMV | AOV | Orders | GMV Share |
|---|---|---|---|---|
| Tier 1 | ₹16.6M | ₹768 | 21,665 | **73.6%** |
| Tier 2 | ₹4.5M | ₹633 | 7,070 | **19.8%** |
| Tier 3 | ₹1.5M | ₹491 | 3,027 | **6.6%** |

**Top Cities by GMV:**

| City | GMV | Orders | AOV |
|---|---|---|---|
| Chennai | ₹3.8M | 4,913 | ₹771 |
| Hyderabad | ₹3.7M | 4,827 | ₹768 |
| Bangalore | ₹3.1M | 4,152 | ₹756 |
| Delhi | ₹3.1M | 3,912 | ₹784 |
| Mumbai | ₹2.9M | 3,861 | ₹758 |
| **Surat** | **₹0.4M** | **807** | **₹481** 🔴 |
| **Patna** | **₹0.3M** | **644** | **₹493** 🔴 |

**The Insight:** Tier 3 AOV (₹491) is **36% lower** than Tier 1 (₹768). This is partially driven by lower purchasing power, but also by limited restaurant selection and menu depth. Tier 2/3 contribute 26.4% of GMV but represent a growth opportunity if AOV can be improved.

**Root Causes:**
1. **Fewer premium restaurants** in Tier 2/3 cities — Limited options mean lower ticket sizes
2. **Price sensitivity** — Users in smaller cities are more discount-dependent
3. **Smaller basket sizes** — Users order for 1–2 people, not family-size orders
4. **Less menu variety** — Fewer cuisines → lower exploration → lower AOV

**Recommendations:**
- **Introduce "Meal Combos" for Tier 2/3** — Bundle (Main + Side + Drink) at a slight discount to increase basket size from ₹491 → ₹600+
- **Restaurant onboarding push in Tier 2/3** — Add more premium/branded restaurants to give users upmarket options
- **Smart upselling** — "Add a dessert for just ₹49" at checkout, targeted at Tier 2/3 users with low cart values
- **Free delivery threshold** — "Free delivery on orders above ₹500" to nudge Tier 3 users to add more items

---

## 🏆 What's Working Well (Strengths to Highlight in Interview)

### 1. Zomato Gold is a GMV Machine
| Metric | Gold | Non-Gold |
|---|---|---|
| GMV Contribution | **₹18.6M (82.5%)** | ₹3.9M (17.5%) |
| AOV | ₹719 | ₹675 |
| Repeat Rate | **98.5%** | 54.7% |
| Median Orders/User | **23** | 2 |
| Activation Rate | **98.0%** | 46.9% |

> *"Gold members are the engine of GMV. They contribute 82.5% of all revenue, order 11.5× more frequently, and have a near-perfect 98.5% repeat rate. Every 1pp increase in Gold adoption is worth approximately ₹186K in GMV."*

### 2. Monthly GMV is Compounding
| Month | GMV | MoM Growth |
|---|---|---|
| Sep '25 | ₹734K | — |
| Dec '25 | ₹1.25M | +70% (3-month) |
| Mar '26 | ₹3.32M | +165% (3-month) |
| May '26 | ₹6.25M | +88% (2-month) |

The business is on a strong growth trajectory. GMV grew **87×** from June '25 to May '26.

### 3. BOGO Promo Drives Highest AOV
| Promo | AOV | Orders | Revenue |
|---|---|---|---|
| BOGO | **₹805** ✅ | 5,353 | ₹4.3M |
| FREE_DELIVERY | ₹753 | 4,970 | ₹3.7M |
| NONE | ₹717 | 11,238 | ₹8.1M |
| FLAT_50 | ₹659 | 6,809 | ₹4.5M |
| DISCOUNT_20PCT | **₹587** 🔴 | 3,339 | ₹2.0M |

> *"BOGO drives 12% higher AOV than no-promo orders because users add more items to maximize the deal. DISCOUNT_20PCT actually cannibalizes AOV by 18%. I'd recommend shifting promo budget from flat discounts to BOGO/Free Delivery which increase basket size."*

### 4. Top 20% Users Drive 70.5% of GMV
| Segment | GMV Share |
|---|---|
| Top 10% users | **47.8%** |
| Top 20% users | **70.5%** |
| Bottom 50% users | ~5% |

This is a classic Pareto distribution. Protecting and growing the top 20% (power users) is more valuable than acquiring 1,000 new low-intent users.

---

## 📐 Metrics I'd Remove (and Why)

| Metric | Why Remove |
|---|---|
| **Weather Impact** | Data came back empty — no actionable insight. In a real product, weather data would matter for demand forecasting, but synthetic data didn't capture it well. |
| **Surge Impact** | Same — the merge_asof enrichment produced sparse matches. Would need better event-order linking in production. |
| **User Type labels (power_user, window_shopper etc.)** | These are pre-assigned labels in the data, not derived from behavior. In production you'd compute RFM segments. The labels are misleading — "window_shopper" users have 10,396 orders (₹7.5M GMV!), which isn't window shopping. I'd replace with an actual RFM segmentation. |

---

## 🎯 Impact Summary — The "So What" Slide

| Problem | Root Cause | Estimated GMV Impact | Fix Complexity |
|---|---|---|---|
| Search → Menu drop (46.9%) | Poor search ranking | **₹3.8M** | Medium (ML/algo) |
| Web payment 96.5% failure | Broken gateway | **₹1.1M** | Low (bug fix) |
| 43.3% never order | Bad onboarding | **₹461K** | Low (product) |
| 45+ min delivery cancellations | Slow restaurants + no communication | **₹780K** | Medium (ops) |
| Tier 2/3 low AOV (₹491–633) | Limited supply + no upselling | **₹500K** | Medium (growth) |
| **Total Recoverable GMV** | | **~₹6.6M** | |

> *"By addressing these 5 problems, we can recover an estimated **₹6.6M in annual GMV** — that's a **29% uplift** on the current ₹22.6M base. The highest-ROI fix is the web payment gateway bug (₹1.1M for likely a 1-sprint engineering fix), followed by search ranking improvements (₹3.8M) which require ML investment."*

---

## 🗣️ How to Tell This Story in an Interview (2-Minute Version)

> *"I built a product analytics case study simulating Zomato's food delivery platform with 5K users and 33K orders. My north star was GMV — ₹22.6M over 12 months.*
>
> *I decomposed GMV into its levers: active users × conversion × AOV × frequency. Then I built a Streamlit dashboard with 30+ interactive charts across 6 tabs — Overview, Funnel, Retention, Segmentation, Monetization, and Operations.*
>
> *The analysis revealed 5 major problems:*
>
> *First, the biggest funnel leak was Search → View Menu at 46.9% — more than half of search sessions drop off. This pointed to search relevance issues.*
>
> *Second, the web platform had a 96.5% payment failure rate — clearly a broken payment gateway, not user behavior. This single bug was costing ₹1.1M in lost GMV.*
>
> *Third, 43.3% of users never placed an order. The Frictionless onboarding cohort activated at 66.3% vs 47.3% for Standard — a 19pp gap proving onboarding design directly impacts revenue.*
>
> *Fourth, delivery times over 45 minutes caused cancellations to spike from 1.8% to 27.2% — a 15× increase. This was a clear cliff effect.*
>
> *Fifth, Tier 2/3 cities had 36% lower AOV than Tier 1, suggesting an upselling and supply-side opportunity.*
>
> *On the positive side, Zomato Gold was the GMV engine — 82.5% of revenue from Gold members who order 11.5× more frequently. And BOGO promos drove 12% higher AOV than no-promo orders, while DISCOUNT_20PCT actually hurt AOV by 18%.*
>
> *Total recoverable GMV across these 5 problems: approximately ₹6.6M, a 29% uplift. The highest-ROI fix was the web payment bug — ₹1.1M recoverable from likely a single engineering sprint."*

---

## 📈 Key Charts to Reference in Discussion

These are the most impactful visualizations from the dashboard:

1. **Session-level Conversion Funnel** → Shows the 46.9% Search → Menu drop visually
2. **Monthly Revenue vs Orders (dual-axis bar+line)** → Shows GMV compounding from ₹71K → ₹6.25M
3. **Cancellation Rate by Delivery Time** → The cliff at 45 minutes is dramatic and memorable
4. **Gold vs Standard: Repeat Rate bar chart** → 98.5% vs 54.7% is a jaw-dropping gap
5. **Payment Failure Rate by Platform** → Web at 96.5% vs ~2% on mobile — obvious bug
6. **Cohort Retention Heatmap** → Shows early cohorts retaining better, validating product maturity
7. **AOV by Promo Code** → BOGO at ₹805 vs DISCOUNT_20PCT at ₹587 — promo strategy insight
8. **Revenue Treemap (Channel × User Type)** → Shows Social Media × Regular users dominate revenue
9. **LTV Distribution** → Top 20% = 70.5% of GMV, classic power-law
10. **Activation Rate by Platform** → Web at 14.3% vs 60% iOS — the web problem visualized

---

> [!TIP]
> **Interview tip:** Always structure your answer as **Metric → Insight → Root Cause → Recommendation → Expected Impact**. This shows you think like a PM, not just an analyst.

> [!IMPORTANT]
> **If asked "what would you do first?"** — Answer: *"Fix the web payment gateway. It's the highest ROI: ₹1.1M recovery for likely the lowest engineering effort. Then invest in search ranking ML, which has the highest absolute impact at ₹3.8M but requires more resources."*
