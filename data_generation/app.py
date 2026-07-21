import streamlit as st
import requests

st.set_page_config(page_title="Zomato Data Simulator", page_icon="", layout="wide")

st.title(" Zomato Synthetic Data Pipeline v11")
st.markdown("Configure the environmental parameters below to generate a highly realistic, relational dataset for Product Analytics. *Note: Weather (Monsoons) and Surge Pricing are calculated dynamically based on the generated calendar dates and time of day.*")

st.sidebar.header("Simulation Parameters")

with st.sidebar.expander(" User Base & Time Horizon", expanded=True):
    num_users = st.number_input("Number of Users to Generate", min_value=100, max_value=100000, value=5000, step=500)
    data_duration_months = st.slider("Time Horizon (Months)", min_value=1, max_value=36, value=6)
    zomato_gold_pct = st.slider("Zomato Gold Rollout %", min_value=0.0, max_value=1.0, value=0.20)

with st.sidebar.expander(" Data Storage", expanded=True):
    output_dir = st.text_input("Save Directory", value="../data", help="Saves relative to where your main.py is running.")

with st.sidebar.expander(" Marketing, Channels & Promos", expanded=False):
    st.markdown("**Acquisition Channel Mix (Weights)**")
    ch_organic = st.slider("Organic", 0.0, 10.0, 4.0)
    ch_paid = st.slider("Paid Search", 0.0, 10.0, 2.5)
    ch_social = st.slider("Social Media", 0.0, 10.0, 2.0)
    ch_ref = st.slider("Referral", 0.0, 10.0, 1.0)
    ch_email = st.slider("Email", 0.0, 10.0, 0.5)
    
    st.markdown("**Promo Code Mix (Weights)**")
    pr_none = st.slider("NONE", 0.0, 10.0, 5.5)
    pr_flat50 = st.slider("FLAT_50", 0.0, 10.0, 1.5)
    pr_bogo = st.slider("BOGO", 0.0, 10.0, 1.2)
    pr_free_del = st.slider("FREE_DELIVERY", 0.0, 10.0, 1.0)
    pr_20pct = st.slider("DISCOUNT_20PCT", 0.0, 10.0, 0.8)

    st.markdown("**Campaigns & Events**")
    push_campaign = st.checkbox("Active Push Notification Campaign")
    festival_season = st.checkbox("Festival Season Active (e.g. Diwali)")
    competitor_promo = st.checkbox("Competitor Promo Active (Mid-funnel attrition)")
    new_user_discount = st.checkbox("New User First Order Discount")
    referral_bonus = st.checkbox("Referral Bonus Active")

with st.sidebar.expander(" Product Features & A/B Tests", expanded=False):
    beta_ui = st.checkbox("Rollout Confusing Beta UI (Fails at Menu)")
    search_personalization = st.checkbox("ML Search Personalization (Boosts intent)")
    loyalty_points_mult = st.slider("Loyalty Points Multiplier (Gold boost)", min_value=1.0, max_value=3.0, value=1.0)

with st.sidebar.expander(" Platform Stability & Performance", expanded=False):
    app_latency = st.slider("App Latency (ms)", min_value=50, max_value=800, value=150)
    payment_reliability = st.slider("Payment Gateway Reliability", min_value=0.50, max_value=1.00, value=0.98)
    outage = st.selectbox("Simulate Gateway Outage", ["NONE", "iOS", "Android", "Web"])
    app_force_update = st.checkbox("Force App Update Required (~30% abandonment)")

with st.sidebar.expander(" Supply, Operations & Support", expanded=False):
    delivery_partner_avail = st.slider("Delivery Partner Availability", 0.0, 1.0, 1.0, help="<1.0 increases delivery time & cancellations")
    catalog_health = st.slider("Restaurant Catalog Health", 0.0, 1.0, 1.0, help="<1.0 hurts browse-to-cart conversion")
    dark_store_pct = st.slider("Dark Store Coverage (Tier 1)", 0.0, 1.0, 0.0, help="Speeds up delivery for Tier 1 users")
    support_quality = st.slider("Customer Support Quality", 0.0, 1.0, 0.85, help="<1.0 increases cancellation rate")
    surge_sensitivity = st.slider("Surge Price Sensitivity", 0.5, 2.0, 1.0, help=">1.0 increases checkout abandonment during surge")

st.markdown("---")
if st.button(" Generate Synthetic Dataset", type="primary", use_container_width=True):
    
    payload = {
        "num_users": num_users,
        "data_duration_months": data_duration_months,
        "output_dir": output_dir,
        "app_latency_ms": app_latency,
        "push_notification_campaign": push_campaign,
        
        "acquisition_channel_mix": {
            "organic": ch_organic, "paid_search": ch_paid, "social_media": ch_social, 
            "referral": ch_ref, "email": ch_email
        },
        "promo_code_mix": {
            "NONE": pr_none, "FLAT_50": pr_flat50, "BOGO": pr_bogo, 
            "FREE_DELIVERY": pr_free_del, "DISCOUNT_20PCT": pr_20pct
        },
        
        "zomato_gold_rollout_pct": zomato_gold_pct,
        "beta_ui_active": beta_ui,
        "search_personalization_active": search_personalization,
        "loyalty_points_multiplier": loyalty_points_mult,
        
        "platform_outage": outage,
        "payment_gateway_reliability": payment_reliability,
        "app_force_update_required": app_force_update,
        
        "delivery_partner_availability": delivery_partner_avail,
        "restaurant_catalog_health": catalog_health,
        "dark_store_coverage_pct": dark_store_pct,
        "customer_support_quality": support_quality,
        
        "festival_season_active": festival_season,
        "competitor_promo_active": competitor_promo,
        "surge_price_sensitivity": surge_sensitivity,
        
        "new_user_first_order_discount": new_user_discount,
        "referral_bonus_active": referral_bonus
    }
    
    with st.spinner(f"Generating complex relational data for {data_duration_months} months... Please wait."):
        try:
            response = requests.post("http://127.0.0.1:8000/api/v1/simulate", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                metrics = data["metrics_summary"]
                
                st.success(" " + data["message"])
                
                st.subheader("Data Generation Summary")
                
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Total Users", f"{metrics['total_users_generated']:,}")
                col2.metric("Total Events", f"{metrics['total_events_logged']:,}")
                col3.metric("Total Orders", f"{metrics['total_orders_placed']:,}")
                col4.metric("Avg. Delivery Time", f"{metrics['avg_delivery_time_mins']} mins")
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                col5, col6, col7, col8 = st.columns(4)
                col5.metric("Delivered Revenue", f"₹{metrics['total_revenue_inr']:,.2f}")
                col6.metric("Avg. Order Value", f"₹{metrics['average_order_value']:,.2f}")
                col7.metric("Gold Order Share", f"{metrics['gold_orders_pct']}%")
                col8.metric("Promo Uptake", f"{metrics['promo_uptake_pct']}%")

                st.markdown("<br>", unsafe_allow_html=True)
                
                st.markdown("####  Operational Failures & Friction")
                f_col1, f_col2, f_col3, f_col4 = st.columns(4)
                f_col1.metric("App Crash Rate", f"{metrics['crash_rate_pct']}%", delta="Critical", delta_color="inverse")
                f_col2.metric("Payment Failure Rate", f"{metrics['payment_failure_rate_pct']}%", delta="Revenue Block", delta_color="inverse")
                f_col3.metric("Order Cancel Rate", f"{metrics['order_cancellation_rate_pct']}%", delta="Lost Fulfillment", delta_color="inverse")
                f_col4.metric("Force Update Drop", f"{metrics.get('force_update_abandonment_pct', 0)}%", delta="Funnel Leak", delta_color="inverse")
                
                st.markdown("<br>", unsafe_allow_html=True)
                st.info(f"**Overall Funnel Conversion:** {metrics['overall_funnel_conversion_pct']}% of users who opened the app successfully completed a payment.")
                
            else:
                st.error(f"Backend Error: {response.text}")
                
        except requests.exceptions.ConnectionError:
            st.error(" Could not connect to the backend. Is your FastAPI server running on port 8000?")