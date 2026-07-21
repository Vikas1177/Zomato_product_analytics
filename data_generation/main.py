from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, validator
from typing import Dict
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import uuid
import os

app = FastAPI(title="Zomato Synthetic Data API", version="11.0")


_DEFAULT_CHANNEL_PROFILE: Dict = {
    "session_mult": 1.00, "conv_mult": 1.00, "aov_mult": 1.00, "gold_prob_scale": 1.00
}

CHANNEL_PROFILES: Dict[str, Dict] = {
    "organic":      dict(session_mult=1.00, conv_mult=1.00, aov_mult=1.05, gold_prob_scale=1.10),
    "paid_search":  dict(session_mult=0.70, conv_mult=1.15, aov_mult=0.95, gold_prob_scale=0.85),
    "social_media": dict(session_mult=0.85, conv_mult=0.88, aov_mult=1.10, gold_prob_scale=0.90),
    "referral":     dict(session_mult=1.00, conv_mult=1.22, aov_mult=1.00, gold_prob_scale=1.15),
    "email":        dict(session_mult=0.90, conv_mult=1.10, aov_mult=1.02, gold_prob_scale=1.00),
}

PROMO_EFFECTS: Dict[str, Dict] = {
    "NONE":                   dict(checkout_mult=1.00, payment_mult=1.00, aov_delta=  0, aov_mult=1.00),
    "FLAT_50":                dict(checkout_mult=1.50, payment_mult=1.40, aov_delta=-50, aov_mult=1.00),
    "BOGO":                   dict(checkout_mult=1.25, payment_mult=1.20, aov_delta=  0, aov_mult=1.12),
    "FREE_DELIVERY":          dict(checkout_mult=1.18, payment_mult=1.12, aov_delta=  0, aov_mult=1.05),
    "DISCOUNT_20PCT":         dict(checkout_mult=1.35, payment_mult=1.28, aov_delta=  0, aov_mult=0.82),
    "FIRST_ORDER_DISCOUNT":   dict(checkout_mult=1.65, payment_mult=1.55, aov_delta=-80, aov_mult=1.00),
}

USER_TYPE_PROFILES: Dict[str, Dict] = {
    "power_user":     dict(session_mult=3.0, checkout_mult=1.20),  # frequent, decisive
    "regular":        dict(session_mult=1.0, checkout_mult=1.00),  # baseline
    "occasional":     dict(session_mult=0.4, checkout_mult=0.95),  # infrequent, deliberate
    "window_shopper": dict(session_mult=1.5, checkout_mult=0.55),  # browses often, rarely buys
}



class SimulationParams(BaseModel):
    num_users: int = 1000
    data_duration_months: int = 6
    output_dir: str = "../data"

    app_latency_ms: int = 150

    push_notification_campaign: bool = False

    acquisition_channel_mix: Dict[str, float] = Field(default={
        "organic":      0.40,
        "paid_search":  0.25,
        "social_media": 0.20,
        "referral":     0.10,
        "email":        0.05,
    })

    promo_code_mix: Dict[str, float] = Field(default={
        "NONE":           0.55,
        "FLAT_50":        0.15,
        "BOGO":           0.12,
        "FREE_DELIVERY":  0.10,
        "DISCOUNT_20PCT": 0.08,
    })

    zomato_gold_rollout_pct: float = 0.20
    beta_ui_active: bool = False
    search_personalization_active: bool = False
    loyalty_points_multiplier: float = 1.0

    platform_outage: str = "NONE"
    payment_gateway_reliability: float = 0.98
    app_force_update_required: bool = False

    delivery_partner_availability: float = 1.0
    restaurant_catalog_health: float = 1.0
    dark_store_coverage_pct: float = 0.0
    customer_support_quality: float = 0.85

    festival_season_active: bool = False
    competitor_promo_active: bool = False
    surge_price_sensitivity: float = 1.0

    new_user_first_order_discount: bool = False
    referral_bonus_active: bool = False

    @validator("acquisition_channel_mix", pre=True)
    def _normalise_channel_mix(cls, v):
        total = sum(v.values())
        if total <= 0:
            raise ValueError("acquisition_channel_mix values must be positive")
        return {k: val / total for k, val in v.items()}

    @validator("promo_code_mix", pre=True)
    def _normalise_promo_mix(cls, v):
        total = sum(v.values())
        if total <= 0:
            raise ValueError("promo_code_mix values must be positive")
        return {k: val / total for k, val in v.items()}



class ZomatoDataSimulator:
    def __init__(self, params: SimulationParams):
        self.params = params
        self.total_days = params.data_duration_months * 30
        self.start_date = datetime.now() - timedelta(days=self.total_days)

        self.base_funnel = {
            "app_open":        1.00,
            "search":          0.85,
            "view_menu":       0.70,
            "add_to_cart":     0.50,
            "checkout":        0.30,
            "payment_attempt": 0.25,  # renamed to attempt to allow explicit failure
        }

        self.city_mapping = {
            "Tier_1": ["Mumbai", "Delhi", "Bangalore", "Hyderabad", "Chennai"],
            "Tier_2": ["Pune", "Jaipur", "Ahmedabad", "Lucknow", "Chandigarh"],
            "Tier_3": ["Indore", "Bhopal", "Surat", "Patna", "Ludhiana"],
        }

        self.hour_weights = (
            [0.05 / 7] * 7 +   # 00–06  night / early morning
            [0.10 / 5] * 5 +   # 07–11  morning
            [0.30 / 4] * 4 +   # 12–15  lunch rush
            [0.15 / 3] * 3 +   # 16–18  afternoon
            [0.40 / 5] * 5     # 19–23  dinner rush
        )

        self._ch_names = list(params.acquisition_channel_mix.keys())
        self._ch_probs = list(params.acquisition_channel_mix.values())


    def _calculate_latency_penalty(self) -> float:
        """Funnel-wide conversion penalty when app_latency_ms > 200."""
        if self.params.app_latency_ms <= 200:
            return 1.0
        units = (self.params.app_latency_ms - 200) // 100
        return max(0.3, 1.0 - 0.05 * units)

    def _calculate_crash_probability(self) -> float:
        """Base crash rate 0.5 %; +1 % per 100 ms of excess latency over 200 ms."""
        base = 0.005
        if self.params.app_latency_ms > 200:
            extra = ((self.params.app_latency_ms - 200) // 100) * 0.01
            return min(0.15, base + extra)
        return base

    def _get_session_promo(self, user: dict, is_first_order_eligible: bool) -> str:
        """
        Return the promo code applied to this session.

        Priority: first-order discount → channel-affinity-weighted draw from promo_code_mix.
        Festival season suppresses NONE; Gold users see slightly fewer promos.
        """
        if is_first_order_eligible and self.params.new_user_first_order_discount:
            return "FIRST_ORDER_DISCOUNT"

        promo_types = list(self.params.promo_code_mix.keys())
        weights = list(self.params.promo_code_mix.values())

        channel_affinity: Dict[str, Dict[str, float]] = {
            "organic":      {},
            "email":        {"FLAT_50": 1.40, "DISCOUNT_20PCT": 1.30},
            "paid_search":  {"FLAT_50": 1.20, "DISCOUNT_20PCT": 1.10},
            "referral":     {"FREE_DELIVERY": 1.50, "BOGO": 1.20},
            "social_media": {"BOGO": 1.30, "FREE_DELIVERY": 1.20},
        }
        affinities = channel_affinity.get(user["acquisition_channel"], {})

        if self.params.referral_bonus_active and user["acquisition_channel"] == "referral":
            affinities["FREE_DELIVERY"] = affinities.get("FREE_DELIVERY", 1.0) * 1.50

        if self.params.festival_season_active:
            affinities["NONE"] = 0.45

        if user["is_zomato_gold"] and "NONE" in promo_types:
            none_idx = promo_types.index("NONE")
            weights = list(weights)
            weights[none_idx] *= 1.25

        adjusted = [w * affinities.get(pt, 1.0) for pt, w in zip(promo_types, weights)]
        total = sum(adjusted)
        return np.random.choice(promo_types, p=[w / total for w in adjusted])


    def generate_users(self) -> pd.DataFrame:
        users = []
        platforms = ["iOS", "Android", "Web"]
        city_tiers = ["Tier_1", "Tier_2", "Tier_3"]
        onboarding_cohorts = ["Standard", "Frictionless"]
        user_types = ["power_user", "regular", "occasional", "window_shopper"]
        user_type_weights = [0.10, 0.40, 0.20, 0.30]

        for _ in range(self.params.num_users):
            channel = np.random.choice(self._ch_names, p=self._ch_probs)
            cp = CHANNEL_PROFILES.get(channel, _DEFAULT_CHANNEL_PROFILE)

            gold_prob = min(0.95,
                self.params.zomato_gold_rollout_pct
                * cp["gold_prob_scale"]
                * float(np.random.uniform(0.85, 1.15))
            )
            is_gold = np.random.random() < gold_prob

            tier = np.random.choice(city_tiers, p=[0.60, 0.30, 0.10])
            city = np.random.choice(self.city_mapping[tier])

            age_roll = np.random.random()
            if age_roll < 0.65:
                age = np.random.randint(22, 31)
            elif age_roll < 0.85:
                age = np.random.randint(18, 22)
            else:
                age = np.random.randint(31, 55)

            signup_offset = np.random.randint(0, self.total_days)
            user_type = np.random.choice(user_types, p=user_type_weights)

            users.append({
                "user_id":             f"U_{str(uuid.uuid4())[:8]}",
                "signup_date":         self.start_date + timedelta(days=signup_offset),
                "age":                 age,
                "city":                city,
                "city_tier":           tier,
                "platform":            np.random.choice(platforms, p=[0.45, 0.50, 0.05]),
                "acquisition_channel": channel,
                "is_zomato_gold":      is_gold,
                "onboarding_cohort":   np.random.choice(onboarding_cohorts, p=[0.5, 0.5]),
                "user_type":           user_type,
            })
        return pd.DataFrame(users)

    def generate_events_and_orders(self, df_users: pd.DataFrame):
        events, orders = [], []
        latency_mult = self._calculate_latency_penalty()
        crash_prob   = self._calculate_crash_probability()
        time_scale   = max(1.0, float(self.params.data_duration_months))

        date_range = pd.date_range(
            start=self.start_date,
            end=datetime.now() + timedelta(days=5),
            freq="D"
        )
        unique_months = date_range.strftime("%Y-%m").unique()

        monthly_rain:   Dict[str, float] = {}
        monthly_demand: Dict[str, float] = {}
        for m in unique_months:
            month_num = int(m.split("-")[1])
            if month_num in [6, 7, 8]:
                monthly_rain[m] = float(np.clip(np.random.normal(0.60, 0.05), 0.48, 0.72))
            else:
                monthly_rain[m] = float(np.clip(np.random.normal(0.10, 0.02), 0.04, 0.16))
            monthly_demand[m] = float(np.clip(np.random.normal(1.0, 0.06), 0.78, 1.28))

        num_weeks = self.total_days // 7 + 2
        weekly_spike_mask = np.random.random(num_weeks) < 0.12  # 12 % of weeks are spike weeks
        weekly_mult = np.where(
            weekly_spike_mask,
            np.random.uniform(1.25, 1.80, num_weeks),    # spike: +25 % to +80 %
            np.random.normal(1.00, 0.04, num_weeks)       # normal: ±4 % noise
        )

        for _, user in df_users.iterrows():
            channel = user["acquisition_channel"]
            cp  = CHANNEL_PROFILES.get(channel, _DEFAULT_CHANNEL_PROFILE)
            utp = USER_TYPE_PROFILES.get(user["user_type"], USER_TYPE_PROFILES["regular"])

            base_sessions = 3 if user["is_zomato_gold"] else 1
            if user["onboarding_cohort"] == "Frictionless":
                base_sessions += 2

            lam = base_sessions * time_scale * cp["session_mult"] * utp["session_mult"]
            if 22 <= user["age"] <= 30:                           lam *= 1.20
            if user["city_tier"] == "Tier_1":                     lam *= 1.30
            if self.params.festival_season_active:                lam *= 1.50
            if self.params.referral_bonus_active and channel == "referral":
                                                                  lam *= 1.25
            if self.params.loyalty_points_multiplier > 1.0 and user["is_zomato_gold"]:
                lam *= 1.0 + 0.10 * (self.params.loyalty_points_multiplier - 1.0)

            num_sessions = np.random.poisson(lam=max(0.5, lam))
            if self.params.push_notification_campaign:
                num_sessions += int(2 * time_scale)

            days_active      = max(1, (datetime.now() - user["signup_date"]).days)
            user_order_count = 0   # tracks per-user order count for first-order logic

            for _ in range(num_sessions):
                session_id = f"S_{str(uuid.uuid4())[:8]}"

                day_offset = np.random.randint(0, days_active)
                base_date  = user["signup_date"] + timedelta(days=day_offset)

                if base_date.weekday() < 4 and np.random.random() < 0.30:
                    base_date += timedelta(days=5 - base_date.weekday())

                session_hour = np.random.choice(24, p=self.hour_weights)
                session_min  = np.random.randint(0, 60)
                current_time = base_date.replace(hour=session_hour, minute=session_min)
                is_weekend   = current_time.weekday() >= 5

                month_key    = current_time.strftime("%Y-%m")
                week_num     = min(day_offset // 7, len(weekly_mult) - 1)
                demand_shock = monthly_demand.get(month_key, 1.0) * float(weekly_mult[week_num])

                rain_prob = monthly_rain.get(month_key, 0.10)
                rain_prob = float(np.clip(rain_prob + np.random.normal(0, 0.03), 0, 0.90))
                current_weather = "rain" if np.random.random() < rain_prob else "clear"

                is_dinner_rush = 19 <= current_time.hour <= 22
                current_surge  = (
                    (current_weather == "rain" and np.random.random() < 0.70) or
                    (is_weekend and is_dinner_rush)
                )

                if self.params.app_force_update_required and np.random.random() < 0.30:
                    events.append({
                        "event_id":       str(uuid.uuid4()),
                        "session_id":     session_id,
                        "user_id":        user["user_id"],
                        "event_time":     current_time.isoformat(),
                        "event_name":     "app_update_prompt",
                        "platform":       user["platform"],
                        "weather_at_time": current_weather,
                        "surge_active":   current_surge,
                    })
                    continue  # abandon session; no further funnel steps

                is_first_eligible = (user_order_count == 0) and (days_active <= 7)
                session_promo = self._get_session_promo(dict(user), is_first_eligible)
                pfx = PROMO_EFFECTS.get(session_promo, PROMO_EFFECTS["NONE"])

                for step, base_prob in self.base_funnel.items():

                    if np.random.random() < crash_prob:
                        events.append({
                            "event_id":       str(uuid.uuid4()),
                            "session_id":     session_id,
                            "user_id":        user["user_id"],
                            "event_time":     current_time.isoformat(),
                            "event_name":     "app_crash",
                            "platform":       user["platform"],
                            "weather_at_time": current_weather,
                            "surge_active":   current_surge,
                        })
                        break

                    p = (base_prob
                         * latency_mult
                         * cp["conv_mult"]
                         * demand_shock
                         * float(np.random.uniform(0.92, 1.08)))  # per-step noise

                    if is_weekend:
                        p *= 1.15
                    if current_weather == "rain" and step == "search":
                        p *= 1.20
                    if self.params.beta_ui_active and step == "view_menu":
                        p *= 0.65
                    if self.params.search_personalization_active and step in ("search", "view_menu"):
                        p *= 1.15
                    if step in ("view_menu", "add_to_cart"):
                        p *= self.params.restaurant_catalog_health
                    if self.params.competitor_promo_active and step in ("search", "view_menu", "add_to_cart"):
                        p *= float(np.random.uniform(0.78, 0.93))
                    if self.params.festival_season_active and step in ("add_to_cart", "checkout"):
                        p *= float(np.random.uniform(1.15, 1.25))
                    if user["city_tier"] == "Tier_3" and session_promo == "NONE" and step == "checkout":
                        p *= 0.85   # Tier-3 users are more price-sensitive without a promo

                    if step == "checkout":
                        p *= pfx["checkout_mult"]
                    elif step == "payment_attempt":
                        p *= pfx["payment_mult"]

                    if step in ("add_to_cart", "checkout", "payment_attempt"):
                        p *= utp["checkout_mult"]

                    if user["is_zomato_gold"] and step in ("add_to_cart", "checkout", "payment_attempt"):
                        p = 0.90

                    if (self.params.loyalty_points_multiplier > 1.0
                            and user["is_zomato_gold"]
                            and step in ("checkout", "payment_attempt")):
                        p = min(1.0, p * (1.0 + 0.05 * (self.params.loyalty_points_multiplier - 1.0)))

                    if current_surge and step in ("checkout", "payment_attempt") and not user["is_zomato_gold"]:
                        p *= max(0.30, 1.0 - 0.40 * self.params.surge_price_sensitivity)

                    if np.random.random() > min(1.0, p):
                        break

                    final_event_name = step
                    if step == "payment_attempt":
                        base_fail = 1.0 - self.params.payment_gateway_reliability
                        base_fail = float(np.clip(
                            base_fail + np.random.normal(0, 0.004), 0.005, 1.0
                        ))
                        gw_fail = 0.95 if user["platform"] == self.params.platform_outage else base_fail
                        final_event_name = (
                            "payment_failed" if np.random.random() < gw_fail else "payment_success"
                        )

                    events.append({
                        "event_id":       str(uuid.uuid4()),
                        "session_id":     session_id,
                        "user_id":        user["user_id"],
                        "event_time":     current_time.isoformat(),
                        "event_name":     final_event_name,
                        "platform":       user["platform"],
                        "weather_at_time": current_weather,
                        "surge_active":   current_surge,
                    })
                    current_time += timedelta(seconds=np.random.randint(10, 60))

                    if final_event_name == "payment_failed":
                        break  # stop funnel on gateway failure

                    if final_event_name == "payment_success":
                        user_order_count += 1

                        base_aov = 400
                        if user["city_tier"] == "Tier_1":   base_aov += 100
                        elif user["city_tier"] == "Tier_3": base_aov -= 100
                        if user["age"] > 35:                base_aov += 120
                        if current_surge:                   base_aov += 150
                        if is_weekend:                      base_aov += 100

                        if self.params.festival_season_active:
                            base_aov *= float(np.random.uniform(1.20, 1.30))

                        base_aov *= cp["aov_mult"]

                        base_aov  = max(100, base_aov + pfx["aov_delta"])
                        base_aov *= pfx["aov_mult"]

                        has_dark_store = (
                            user["city_tier"] == "Tier_1"
                            and np.random.random() < self.params.dark_store_coverage_pct
                        )

                        delivery_time = np.random.randint(20, 45)
                        if current_weather == "rain":
                            delivery_time += np.random.randint(20, 31)   # 20–30 min rain penalty
                        if self.params.delivery_partner_availability < 1.0:
                            shortage_penalty = int(
                                (1.0 - self.params.delivery_partner_availability) * 35
                            )
                            delivery_time += np.random.randint(0, max(1, shortage_penalty))
                        if has_dark_store:
                            delivery_time = int(delivery_time * float(np.random.uniform(0.55, 0.70)))

                        base_cancel   = 0.30 if delivery_time > 50 else 0.02
                        support_mod   = 2.0 - 1.3 * self.params.customer_support_quality
                        ops_mod       = 1.0 + max(0.0, 1.0 - self.params.delivery_partner_availability)
                        cancel_prob   = min(0.95, base_cancel * support_mod * ops_mod)
                        order_status  = "Cancelled" if np.random.random() < cancel_prob else "Delivered"

                        orders.append({
                            "order_id":           f"ORD_{str(uuid.uuid4())[:8]}",
                            "user_id":            user["user_id"],
                            "order_time":         current_time.isoformat(),
                            "amount_inr":         round(float(np.random.normal(
                                                      base_aov, max(30, base_aov * 0.12)
                                                  )), 2),
                            "delivery_fee":       0 if user["is_zomato_gold"] else 40,
                            "promo_applied":      session_promo,
                            "delivery_time_mins": delivery_time,
                            "order_status":       order_status,
                        })

        return pd.DataFrame(events), pd.DataFrame(orders)



@app.post("/api/v1/simulate")
async def run_simulation(params: SimulationParams):
    try:
        simulator  = ZomatoDataSimulator(params)
        df_users   = simulator.generate_users()
        df_events, df_orders = simulator.generate_events_and_orders(df_users)

        os.makedirs(params.output_dir, exist_ok=True)
        df_users.to_csv(os.path.join(params.output_dir, "users.csv"),  index=False)
        df_events.to_csv(os.path.join(params.output_dir, "events.csv"), index=False)
        df_orders.to_csv(os.path.join(params.output_dir, "orders.csv"), index=False)

        metrics = {
            "simulation_duration_months":    params.data_duration_months,
            "total_users_generated":         len(df_users),
            "total_events_logged":           len(df_events),
            "total_orders_placed":           len(df_orders),
            "total_revenue_inr":             0,
            "average_order_value":           0,
            "gold_orders_pct":               0,
            "overall_funnel_conversion_pct": 0,
            "crash_rate_pct":                0,
            "payment_failure_rate_pct":      0,
            "order_cancellation_rate_pct":   0,
            "avg_delivery_time_mins":        0,
            "promo_uptake_pct":              0,    # % of orders with any active promo
            "promo_revenue_breakdown":       [],   # revenue + count per promo type
            "channel_user_breakdown_pct":    {},   # % users per acquisition channel
            "force_update_abandonment_pct":  0,    # % sessions lost to forced update
        }

        if len(df_events) > 0:
            app_opens     = len(df_events[df_events["event_name"] == "app_open"])
            pay_success   = len(df_events[df_events["event_name"] == "payment_success"])
            pay_failed    = len(df_events[df_events["event_name"] == "payment_failed"])
            crashes       = len(df_events[df_events["event_name"] == "app_crash"])
            force_updates = len(df_events[df_events["event_name"] == "app_update_prompt"])
            total_sessions = df_events["session_id"].nunique()

            if app_opens > 0:
                metrics["overall_funnel_conversion_pct"] = round(
                    pay_success / app_opens * 100, 2
                )
            if total_sessions > 0:
                metrics["crash_rate_pct"]               = round(crashes / total_sessions * 100, 2)
                metrics["force_update_abandonment_pct"] = round(
                    force_updates / total_sessions * 100, 2
                )
            total_attempts = pay_success + pay_failed
            if total_attempts > 0:
                metrics["payment_failure_rate_pct"] = round(
                    pay_failed / total_attempts * 100, 2
                )

        if not df_orders.empty:
            delivered = df_orders[df_orders["order_status"] == "Delivered"]
            cancelled = df_orders[df_orders["order_status"] == "Cancelled"]
            gold_orders = df_orders[df_orders["delivery_fee"] == 0]

            metrics["total_revenue_inr"]          = round(delivered["amount_inr"].sum(), 2)
            metrics["average_order_value"]         = round(df_orders["amount_inr"].mean(), 2)
            metrics["gold_orders_pct"]             = round(len(gold_orders) / len(df_orders) * 100, 2)
            metrics["order_cancellation_rate_pct"] = round(len(cancelled) / len(df_orders) * 100, 2)
            metrics["avg_delivery_time_mins"]      = round(
                df_orders["delivery_time_mins"].mean(), 2
            )

            promo_orders = df_orders[df_orders["promo_applied"] != "NONE"]
            metrics["promo_uptake_pct"] = round(len(promo_orders) / len(df_orders) * 100, 2)

            promo_rev = (
                df_orders
                .groupby("promo_applied")["amount_inr"]
                .agg(order_count="count", total_revenue="sum")
                .reset_index()
                .rename(columns={"amount_inr": "promo_applied"})
            )
            metrics["promo_revenue_breakdown"] = promo_rev.to_dict("records")

        if len(df_users) > 0:
            ch_pct = (
                df_users["acquisition_channel"]
                .value_counts(normalize=True)
                .mul(100).round(2)
                .to_dict()
            )
            metrics["channel_user_breakdown_pct"] = ch_pct

        return {
            "status":          "success",
            "message":         f"Synthetic data generated and saved to {params.output_dir}",
            "metrics_summary": metrics,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))