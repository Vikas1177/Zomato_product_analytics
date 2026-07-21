import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(
    page_title="Zomato Analytics",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }

div[data-testid="metric-container"] {
    background: #F9FAFB;
    border: 1px solid #E5E7EB;
    border-left: 3px solid #E23744;
    padding: 16px 20px;
    border-radius: 8px;
}

.stTabs [data-baseweb="tab-list"] {
    background: #F3F4F6;
    border-radius: 8px;
    padding: 3px;
    gap: 2px;
    border: 1px solid #E5E7EB;
}
.stTabs [data-baseweb="tab"] {
    color: #6B7280;
    font-family: 'Inter', sans-serif;
    font-size: 0.80rem;
    font-weight: 500;
    border-radius: 6px;
    padding: 7px 14px;
    border: none !important;
    background: transparent !important;
    transition: color 0.15s;
}
.stTabs [aria-selected="true"] {
    background: #E23744 !important;
    color: #FFFFFF !important;
    font-weight: 600 !important;
}

details {
    background: #F9FAFB !important;
    border: 1px solid #E5E7EB !important;
    border-radius: 8px !important;
}

hr { border-color: #E5E7EB !important; margin: 18px 0 !important; }

.sec-label {
    font-family: 'Inter', sans-serif;
    font-size: 0.67rem;
    font-weight: 700;
    color: #E23744;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin: 22px 0 12px 0;
    display: flex;
    align-items: center;
    gap: 10px;
}
.sec-label::after { content: ''; flex: 1; height: 1px; background: #E5E7EB; }
</style>
""", unsafe_allow_html=True)


R    = "#E23744"
OR   = "#FF8C42"
YL   = "#F5A623"
GR   = "#27AE60"
BL   = "#2980B9"
GY   = "#9CA3AF"
PU   = "#8E44AD"
TL   = "#16A085"

BG   = "#FFFFFF"
CARD = "#FAFAFA"
GRID = "#E5E7EB"
TK   = "#6B7280"
WH   = "#111111"

CAT  = [R, OR, YL, GR, BL, PU, TL, "#F48FB1"]

CHANNEL_COLORS = {
    "organic":      GR,
    "paid_search":  BL,
    "social_media": OR,
    "referral":     R,
    "email":        YL,
}


def T(fig, title="", h=300):
    fig.update_layout(
        title=dict(text=title, font=dict(family="Inter", size=13, color=WH), x=0, pad=dict(l=0)),
        paper_bgcolor=BG, plot_bgcolor=BG,
        font=dict(family="Inter", color=TK, size=11),
        height=h,
        margin=dict(l=8, r=8, t=40, b=8),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=10, color=TK),
                    orientation="h", yanchor="bottom", y=1.1, xanchor="right", x=1),
        xaxis=dict(gridcolor=GRID, linecolor=GRID, tickfont=dict(color=TK), zeroline=False),
        yaxis=dict(gridcolor=GRID, linecolor=GRID, tickfont=dict(color=TK), zeroline=False),
    )
    return fig

def sec(label):
    st.markdown(f'<div class="sec-label">{label}</div>', unsafe_allow_html=True)

def hex_rgba(hex_color, alpha=0.15):
    h = hex_color.lstrip('#')
    r, g, b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
    return f"rgba({r},{g},{b},{alpha})"


@st.cache_data
def load_data():
    try:
        users  = pd.read_csv("data/users.csv")
        events = pd.read_csv("data/events.csv")
        orders = pd.read_csv("data/orders.csv")

        users['signup_date'] = pd.to_datetime(users['signup_date'])
        events['event_time'] = pd.to_datetime(events['event_time'])
        orders['order_time'] = pd.to_datetime(orders['order_time'])

        pay_ev = (
            events[events['event_name'] == 'payment_success']
            [['user_id', 'event_time', 'weather_at_time', 'surge_active']]
            .copy().sort_values('event_time').reset_index(drop=True)
        )
        orders_s = orders.sort_values('order_time').reset_index(drop=True)

        if len(pay_ev) > 0 and len(orders_s) > 0:
            enriched = pd.merge_asof(
                orders_s,
                pay_ev.rename(columns={'event_time': '_pay_time'}),
                left_on='order_time', right_on='_pay_time',
                by='user_id', tolerance=pd.Timedelta('2min'), direction='nearest'
            ).drop(columns=['_pay_time'])
        else:
            enriched = orders_s.copy()
            enriched['weather_at_time'] = np.nan
            enriched['surge_active']    = np.nan

        ov_e = [c for c in events.columns  if c in users.columns and c != 'user_id']
        ov_o = [c for c in enriched.columns if c in users.columns and c != 'user_id']

        merged_events = pd.merge(events.drop(columns=ov_e),   users, on='user_id', how='left')
        merged_orders = pd.merge(enriched.drop(columns=ov_o), users, on='user_id', how='left')

        return users, events, orders, merged_events, merged_orders

    except FileNotFoundError:
        st.error("  Data files not found in `data/`. Run the simulation API first to generate CSVs.")
        st.stop()

df_users, df_events, df_orders, df_merged_events, df_merged_orders = load_data()

min_dt = df_events['event_time'].min().strftime('%b %Y')
max_dt = df_events['event_time'].max().strftime('%b %Y')

st.markdown(f"""
    <div style="padding-top:6px;">
        <h1 style="margin:0; font-size:1.8rem; font-weight:700; color:#111111; font-family:'Inter',sans-serif;">
            Zomato Intelligence Dashboard
        </h1>
        <p style="margin:3px 0 0 2px; color:#9CA3AF; font-size:0.8rem;
                  font-family:'Inter',sans-serif;">
            Data from {min_dt} — {max_dt}
        </p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("""
<div style='height:1px; background:#E5E7EB; margin:10px 0 20px 0;'></div>
""", unsafe_allow_html=True)


with st.expander("Segment Filters", expanded=False):
    c1, c2, c3, c4 = st.columns(4)

    min_date = df_events['event_time'].min().date()
    max_date = df_events['event_time'].max().date()
    date_rng = c1.date_input("Date range", value=(min_date, max_date),
                             min_value=min_date, max_value=max_date, key="d_global")

    tiers = c2.multiselect("City tier", sorted(df_users['city_tier'].unique()),
                           default=sorted(df_users['city_tier'].unique()), key="t_global")

    plats = c3.multiselect("Platform", sorted(df_users['platform'].unique()),
                           default=sorted(df_users['platform'].unique()), key="p_global")

    gold = c4.multiselect("Gold status", [True, False], default=[True, False],
                          format_func=lambda x: "Gold" if x else "Standard", key="g_global")

    c5, c6, c7, c8 = st.columns(4)

    age = c5.slider("Age range", int(df_users['age'].min()), int(df_users['age'].max()),
                    (int(df_users['age'].min()), int(df_users['age'].max())), key="a_global")

    cohorts = c6.multiselect("Onboarding cohort", sorted(df_users['onboarding_cohort'].unique()),
                             default=sorted(df_users['onboarding_cohort'].unique()), key="oc_global")

    cities = c7.multiselect("City", sorted(df_users['city'].unique()),
                            default=sorted(df_users['city'].unique()), key="c_global")

    if 'acquisition_channel' in df_users.columns:
        channels = c8.multiselect("Acquisition channel", sorted(df_users['acquisition_channel'].astype(str).unique()),
                                  default=sorted(df_users['acquisition_channel'].astype(str).unique()), key="ac_global")
    else:
        channels = []

fu = df_users[
    df_users['age'].between(age[0], age[1]) &
    df_users['city_tier'].isin(tiers) &
    df_users['platform'].isin(plats) &
    df_users['is_zomato_gold'].isin(gold) &
    df_users['onboarding_cohort'].isin(cohorts) &
    df_users['city'].isin(cities)
]
if channels:
    fu = fu[fu['acquisition_channel'].isin(channels)]

ids = fu['user_id']
fe  = df_merged_events[df_merged_events['user_id'].isin(ids)]
fo  = df_merged_orders[df_merged_orders['user_id'].isin(ids)]

if len(date_rng) == 2:
    start_dt = pd.to_datetime(date_rng[0])
    end_dt = pd.to_datetime(date_rng[1]) + pd.Timedelta(days=1, seconds=-1)
    fe = fe[fe['event_time'].between(start_dt, end_dt)]
    fo = fo[fo['order_time'].between(start_dt, end_dt)]
elif len(date_rng) == 1:
    start_dt = pd.to_datetime(date_rng[0])
    end_dt = pd.to_datetime(date_rng[0]) + pd.Timedelta(days=1, seconds=-1)
    fe = fe[fe['event_time'].between(start_dt, end_dt)]
    fo = fo[fo['order_time'].between(start_dt, end_dt)]

st.markdown("<br>", unsafe_allow_html=True)


t1, t2, t3, t4, t5, t6 = st.tabs([
    "Overview",
    "Funnel & Activation",
    "Retention",
    "Segmentation",
    "Monetization",
    "Operations",
])


with t1:
    delivered = fo[fo['order_status'] == 'Delivered']

    if not fo.empty:
        latest_month = fo['order_time'].dt.to_period('M').max()
        maou = fo[
            (fo['order_time'].dt.to_period('M') == latest_month) &
            (fo['order_status'] == 'Delivered')
        ]['user_id'].nunique()
    else:
        maou = 0

    ordering_users  = delivered['user_id'].nunique() if not delivered.empty else 1
    total_orders    = len(delivered)
    orders_per_user = total_orders / ordering_users if ordering_users > 0 else 0

    gmv = delivered['amount_inr'].sum() if not delivered.empty else 0

    if not delivered.empty:
        user_oc     = delivered.groupby('user_id').size()
        repeat_rate = (user_oc > 1).mean() * 100
    else:
        repeat_rate = 0

    aov = delivered['amount_inr'].mean() if not delivered.empty else 0

    app_opens  = fe[fe['event_name'] == 'app_open']['session_id'].nunique()
    pay_ok     = fe[fe['event_name'] == 'payment_success']['session_id'].nunique()
    pay_fail   = fe[fe['event_name'] == 'payment_failed']['session_id'].nunique()
    crashes    = fe[fe['event_name'] == 'app_crash']['session_id'].nunique()
    tot_sess   = fe['session_id'].nunique()
    conv       = pay_ok / app_opens * 100          if app_opens > 0 else 0
    crash_r    = crashes / tot_sess * 100           if tot_sess > 0 else 0
    pay_fail_r = pay_fail / (pay_ok+pay_fail) * 100 if (pay_ok+pay_fail) > 0 else 0
    cancel_r   = len(fo[fo['order_status']=='Cancelled']) / len(fo) * 100 if len(fo) > 0 else 0
    gold_pct   = fu['is_zomato_gold'].mean() * 100  if len(fu) > 0 else 0

    sec("North Star Metrics")
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Monthly Active Ordering Users", f"{maou:,}")
    k2.metric("Orders per Active User",        f"{orders_per_user:.1f}")
    k3.metric("GMV",                           f"₹{gmv/1e6:.2f}M")
    k4.metric("Avg Order Value",               f"₹{aov:,.0f}")
    k5.metric("Repeat Order Rate",             f"{repeat_rate:.1f}%")

    sec("Platform Health")
    ph1, ph2, ph3, ph4, ph5 = st.columns(5)
    ph1.metric("Funnel Conversion",  f"{conv:.1f}%",       delta=f"{conv-15:.1f}% vs 15% target")
    ph2.metric("Gold Adoption",      f"{gold_pct:.1f}%",   delta=f"{gold_pct-30:.1f}% vs 30% target")
    ph3.metric("Crash Rate",         f"{crash_r:.2f}%",    delta=f"{crash_r-1:.2f}% vs 1% target",    delta_color="inverse")
    ph4.metric("Pay Failure Rate",   f"{pay_fail_r:.1f}%", delta=f"{pay_fail_r-5:.1f}% vs 5% target", delta_color="inverse")
    ph5.metric("Cancel Rate",        f"{cancel_r:.1f}%",   delta=f"{cancel_r-5:.1f}% vs 5% target",   delta_color="inverse")

    if not delivered.empty:
        sec("Monthly GMV vs Orders")
        d = delivered.assign(month=lambda x: x['order_time'].dt.to_period('M').astype(str))
        monthly = d.groupby('month').agg(gmv=('amount_inr','sum'), orders=('amount_inr','count')).reset_index()
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Bar(x=monthly['month'], y=monthly['gmv'], name='GMV ₹',
                             marker_color=R, opacity=0.85), secondary_y=False)
        fig.add_trace(go.Scatter(x=monthly['month'], y=monthly['orders'], name='Orders',
                                 line=dict(color=OR, width=2), mode='lines+markers',
                                 marker=dict(size=5, color=OR)), secondary_y=True)
        fig.update_layout(paper_bgcolor=BG, plot_bgcolor=BG, font_color=TK, height=280,
                          margin=dict(l=8,r=8,t=40,b=8),
                          title=dict(text="Monthly Delivered GMV & Order Volume",
                                     font=dict(family="Inter", size=13, color=WH)),
                          legend=dict(bgcolor="rgba(0,0,0,0)", orientation="h", yanchor="bottom", y=1.1, xanchor="right", x=1))
        fig.update_xaxes(gridcolor=GRID, linecolor=GRID)
        fig.update_yaxes(gridcolor=GRID, linecolor=GRID)
        st.plotly_chart(fig, use_container_width=True, key="t1_monthly_gmv")

    sec("Activity Trends")
    tl, tr = st.columns([3, 1])
    with tl:
        if not fe.empty:
            daily = (fe[fe['event_name']=='app_open']
                     .assign(date=lambda d: d['event_time'].dt.date)
                     .groupby('date').size().reset_index(name='sessions'))
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=daily['date'], y=daily['sessions'], mode='lines',
                line=dict(color=R, width=1.8),
                fill='tozeroy', fillcolor='rgba(226,55,68,0.07)'
            ))
            T(fig, "Daily App Opens", h=260)
            st.plotly_chart(fig, use_container_width=True, key="t1_daily_opens")
    with tr:
        if not fo.empty:
            sc = fo['order_status'].value_counts().reset_index()
            sc.columns = ['Status', 'Count']
            fig = px.pie(sc, values='Count', names='Status', hole=0.62,
                         color_discrete_map={'Delivered': GR, 'Cancelled': R})
            fig.update_traces(textinfo='percent+label', textfont_size=10, pull=[0.03, 0])
            T(fig, "Order Status", h=260); fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True, key="t1_order_status")

    sec("Order Value Distribution")
    if not delivered.empty:
        fig = px.histogram(delivered, x='amount_inr', nbins=40,
                           color_discrete_sequence=[R], opacity=0.85,
                           labels={'amount_inr': 'Order Value ₹', 'count': 'Orders'})
        T(fig, "Order Value Distribution (Delivered Orders)", h=280)
        fig.update_layout(xaxis=dict(tickprefix='₹'))
        st.plotly_chart(fig, use_container_width=True, key="t1_order_dist")


with t2:
    STEPS  = ['app_open','search','view_menu','add_to_cart','checkout','payment_success']
    LABELS = ['App Open','Search','View Menu','Add to Cart','Checkout','Pay Success']
    counts = [fe[fe['event_name']==s]['session_id'].nunique() for s in STEPS]

    sec("Session Flow Sankey — How Users Navigate the Funnel")
    if not fe.empty:
        node_labels = ['App Open','Search','View Menu','Add to Cart','Checkout','Payment ','Payment ','App Crash', 'Drop-Off']
        node_map = {'app_open':0,'search':1,'view_menu':2,'add_to_cart':3,
                    'checkout':4,'payment_success':5,'payment_failed':6,'app_crash':7, 'drop_off':8}
        node_colors = [BL, BL, BL, BL, BL, GR, R, R, GY]

        drop_counts = [counts[i] - counts[i+1] for i in range(len(counts)-1)]
        pay_fail_count = fe[fe['event_name'] == 'payment_failed']['session_id'].nunique()
        drop_counts[-1] = drop_counts[-1] - pay_fail_count

        srcs, tgts, vals, lcolors = [], [], [], []

        for i in range(len(counts)-1):
            srcs.append(i); tgts.append(i+1); vals.append(counts[i+1])
            lcolors.append("rgba(156,163,175,0.3)")
            if i < len(counts)-2:
                if drop_counts[i] > 0:
                    srcs.append(i); tgts.append(node_map['drop_off']); vals.append(drop_counts[i])
                    lcolors.append("rgba(156,163,175,0.15)")
            else:
                if pay_fail_count > 0:
                    srcs.append(i); tgts.append(node_map['payment_failed']); vals.append(pay_fail_count)
                    lcolors.append(hex_rgba(R, 0.2))
                if drop_counts[i] > 0:
                    srcs.append(i); tgts.append(node_map['drop_off']); vals.append(drop_counts[i])
                    lcolors.append("rgba(156,163,175,0.15)")

        if srcs:
            fig = go.Figure(go.Sankey(
                node=dict(label=node_labels, color=node_colors, pad=20, thickness=22,
                          line=dict(color='#333',width=0.5)),
                textfont=dict(family='DM Sans',size=11,color=WH),
                link=dict(source=srcs, target=tgts, value=vals, color=lcolors)
            ))
            T(fig, "Event Flow & Attrition Map", h=350)
            st.plotly_chart(fig, use_container_width=True, key="t2_sankey")

    sec("End-to-End Conversion Funnel")
    fl, fr = st.columns([3, 2])
    with fl:
        fig = go.Figure(go.Funnel(
            y=LABELS, x=counts,
            textinfo="value+percent initial",
            textposition="inside",
            textfont=dict(family="DM Sans", size=11),
            marker=dict(
                color=[R,"#D03040","#B52535","#95182A","#75101F","#550810"],
                line=dict(width=0.5, color=BG)
            ),
            connector=dict(line=dict(color=GRID, dash="dot", width=1))
        ))
        T(fig, "Session-level Conversion Funnel", h=390)
        st.plotly_chart(fig, use_container_width=True, key="t2_funnel_full")
    with fr:
        sos = [counts[i+1]/counts[i]*100 if counts[i]>0 else 0 for i in range(len(counts)-1)]
        lbl = [f"{LABELS[i]} → {LABELS[i+1]}" for i in range(len(LABELS)-1)]
        clr = [GR if r>=80 else (YL if r>=60 else R) for r in sos]
        fig = go.Figure(go.Bar(
            y=lbl, x=sos, orientation='h',
            text=[f"{r:.1f}%" for r in sos], textposition='outside',
            marker_color=clr, marker_line_width=0,
        ))
        T(fig, "Step-over-Step Conversion %", h=390)
        fig.update_layout(xaxis=dict(range=[0,118], ticksuffix='%'))
        st.plotly_chart(fig, use_container_width=True, key="t2_funnel_sos")

    sec("Funnel Conversion by Acquisition Channel")
    if not fe.empty and 'acquisition_channel' in fe.columns:
        ch_rows = []
        for ch in sorted(fe['acquisition_channel'].dropna().unique()):
            ch_fe  = fe[fe['acquisition_channel']==ch]
            opens  = ch_fe[ch_fe['event_name']=='app_open']['session_id'].nunique()
            for step, label in zip(STEPS, LABELS):
                cnt = ch_fe[ch_fe['event_name']==step]['session_id'].nunique()
                ch_rows.append({'Channel':ch.replace('_',' ').title(),'Step':label,
                                'Rate':cnt/opens*100 if opens>0 else 0})
        df_ch = pd.DataFrame(ch_rows)
        key_steps = ['Search','Add to Cart','Checkout','Pay Success']
        fig = px.bar(df_ch[df_ch['Step'].isin(key_steps)], x='Step', y='Rate',
                     color='Channel', barmode='group',
                     color_discrete_map={k.replace('_',' ').title():v for k,v in CHANNEL_COLORS.items()},
                     text_auto='.1f', labels={'Rate':'% of App Opens'})
        T(fig, "Funnel % by Channel (relative to App Opens)", h=340)
        fig.update_layout(yaxis=dict(ticksuffix='%'))
        st.plotly_chart(fig, use_container_width=True, key="t2_ch_funnel")

    sec("Funnel Breakdown by Segment")
    fa, fb = st.columns(2)

    with fa:
        ks = ['app_open','add_to_cart','checkout','payment_success']
        kl = ['App Open','Add Cart','Checkout','Pay']
        rows = []
        for g_val, label in [(True,'Gold'),(False,'Standard')]:
            u_ids = fu[fu['is_zomato_gold']==g_val]['user_id']
            ev    = fe[fe['user_id'].isin(u_ids)]
            base  = ev[ev['event_name']=='app_open']['session_id'].nunique()
            for s, l in zip(ks, kl):
                c = ev[ev['event_name']==s]['session_id'].nunique()
                rows.append({'Step':l,'Group':label,'Rate':c/base*100 if base>0 else 0})
        df_gf = pd.DataFrame(rows)
        fig = px.bar(df_gf, x='Step', y='Rate', color='Group', barmode='group',
                     color_discrete_map={'Gold':R,'Standard':GY},
                     text_auto='.1f', labels={'Rate':'% of App Opens'})
        T(fig, "Funnel: Gold vs Standard", h=300)
        fig.update_layout(yaxis=dict(ticksuffix='%'))
        st.plotly_chart(fig, use_container_width=True, key="t2_funnel_gold")

    with fb:
        if not fu.empty and not fe.empty:
            dev_rows = []
            for platform in sorted(fu['platform'].unique()):
                p_ids = fu[fu['platform']==platform]['user_id']
                p_fe  = fe[fe['user_id'].isin(p_ids)]
                opens = p_fe[p_fe['event_name']=='app_open']['session_id'].nunique()
                for step, label in zip(STEPS[1:], LABELS[1:]):
                    cnt = p_fe[p_fe['event_name']==step]['session_id'].nunique()
                    dev_rows.append({'Device': platform, 'Step': label,
                                     'Rate': cnt/opens*100 if opens > 0 else 0})
            if dev_rows:
                df_dev = pd.DataFrame(dev_rows)
                fig = px.bar(df_dev, x='Step', y='Rate', color='Device', barmode='group',
                             color_discrete_sequence=CAT, text_auto='.1f',
                             labels={'Rate': '% of App Opens', 'Device': 'Platform'})
                T(fig, "Funnel Conversion by Device for Each Step", h=300)
                fig.update_layout(yaxis=dict(ticksuffix='%'))
                st.plotly_chart(fig, use_container_width=True, key="t2_funnel_device")

    sec("Activation Velocity")
    first_open = fe[fe['event_name']=='app_open'].groupby('user_id')['event_time'].min().reset_index(name='first_open')
    first_cart = fe[fe['event_name']=='add_to_cart'].groupby('user_id')['event_time'].min().reset_index(name='first_cart')
    first_pay  = fe[fe['event_name']=='payment_success'].groupby('user_id')['event_time'].min().reset_index(name='first_pay')
    act = (first_open
           .merge(first_cart, on='user_id', how='left')
           .merge(first_pay,  on='user_id', how='left')
           .merge(fu[['user_id','onboarding_cohort','is_zomato_gold','platform']], on='user_id', how='left'))
    act['ttc'] = (act['first_cart'] - act['first_open']).dt.total_seconds() / 60
    act['ttp'] = (act['first_pay']  - act['first_open']).dt.total_seconds() / 60
    act.loc[act['ttc'] < 0, 'ttc'] = np.nan
    act.loc[act['ttp'] < 0, 'ttp'] = np.nan
    act_rate = act['first_pay'].notnull().mean()*100 if len(act) > 0 else 0

    av1,av2,av3 = st.columns(3)
    av1.metric("Activation Rate (1st Purchase)", f"{act_rate:.1f}%")
    av2.metric("Median: Open → Cart",            f"{act['ttc'].median():.1f} mins")
    av3.metric("Median: Open → Pay",             f"{act['ttp'].median():.1f} mins")

    aa, ab, ac = st.columns(3)
    with aa:
        ttc_coh = act.dropna(subset=['ttc']).groupby('onboarding_cohort')['ttc'].median().reset_index()
        fig = px.bar(ttc_coh, x='onboarding_cohort', y='ttc', color='onboarding_cohort',
                     color_discrete_map={'Standard':GY,'Frictionless':R},
                     text_auto='.1f', labels={'ttc':'Median Mins','onboarding_cohort':''})
        T(fig, "Time to Cart by Onboarding", h=250); fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True, key="t2_act_onb")
    with ab:
        ttp_data = act.dropna(subset=['ttp'])['ttp'].clip(0, 300)
        fig = px.histogram(ttp_data, nbins=35, color_discrete_sequence=[R], opacity=0.8)
        T(fig, "Time-to-First-Payment Distribution", h=250)
        fig.update_layout(xaxis_title="Minutes", yaxis_title="Users")
        st.plotly_chart(fig, use_container_width=True, key="t2_act_dist")
    with ac:
        act_plat = (act.groupby('platform')
                    .apply(lambda x: x['first_pay'].notnull().mean()*100)
                    .reset_index(name='Activation %'))
        fig = px.bar(act_plat, x='platform', y='Activation %', color='Activation %',
                      color_continuous_scale=[[0,'#FEE2E2'],[1,R]], text_auto='.1f')
        T(fig, "Activation Rate by Platform", h=250)
        fig.update_layout(yaxis=dict(ticksuffix='%'), coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True, key="t2_act_plat")

    sec("Activation Rate by Segment")
    if not fu.empty and not fe.empty:
        seg_rows = []
        overall_act = act['first_pay'].notnull().mean() * 100 if len(act) > 0 else 0
        seg_rows.append({'Segment': 'Overall', 'Activation %': overall_act})
        for coh in ['Frictionless', 'Standard']:
            coh_act = act[act['onboarding_cohort'] == coh]
            rate = coh_act['first_pay'].notnull().mean() * 100 if len(coh_act) > 0 else 0
            seg_rows.append({'Segment': coh, 'Activation %': rate})
        gold_act = act[act['is_zomato_gold'] == True]
        non_gold_act = act[act['is_zomato_gold'] == False]
        seg_rows.append({'Segment': 'Gold', 'Activation %': gold_act['first_pay'].notnull().mean() * 100 if len(gold_act) > 0 else 0})
        seg_rows.append({'Segment': 'Non-Gold', 'Activation %': non_gold_act['first_pay'].notnull().mean() * 100 if len(non_gold_act) > 0 else 0})
        for plat in sorted(act['platform'].dropna().unique()):
            plat_act = act[act['platform'] == plat]
            rate = plat_act['first_pay'].notnull().mean() * 100 if len(plat_act) > 0 else 0
            seg_rows.append({'Segment': plat, 'Activation %': rate})

        seg_df = pd.DataFrame(seg_rows)
        colors = [GR if r >= 60 else (YL if r >= 40 else R) for r in seg_df['Activation %']]
        fig = go.Figure(go.Bar(
            x=seg_df['Segment'], y=seg_df['Activation %'],
            text=[f"{v:.1f}%" for v in seg_df['Activation %']],
            textposition='outside', marker_color=colors
        ))
        T(fig, "Activation Rate (1st Purchase) by Segment", h=320)
        fig.update_layout(yaxis=dict(ticksuffix='%'))
        st.plotly_chart(fig, use_container_width=True, key="t2_act_segment")


with t3:
    sec("Overall Retention at a Glance")
    if not fu.empty and not fe.empty:
        fe_r = fe.copy()
        fe_r['days_since_signup'] = (fe_r['event_time'] - pd.to_datetime(fe_r['signup_date'])).dt.days
        max_date_global = df_events['event_time'].max()
        fu_r = fu.copy()
        fu_r['acct_age'] = (max_date_global - fu_r['signup_date']).dt.days

        d1_elig  = fu_r[fu_r['acct_age'] >= 1]['user_id']
        d7_elig  = fu_r[fu_r['acct_age'] >= 7]['user_id']
        d30_elig = fu_r[fu_r['acct_age'] >= 30]['user_id']

        d1_users  = fe_r[(fe_r['days_since_signup'] == 1)  & fe_r['user_id'].isin(d1_elig)]['user_id'].nunique()
        d7_users  = fe_r[(fe_r['days_since_signup'] == 7)  & fe_r['user_id'].isin(d7_elig)]['user_id'].nunique()
        d30_users = fe_r[(fe_r['days_since_signup'] == 30) & fe_r['user_id'].isin(d30_elig)]['user_id'].nunique()

        d1_rate  = d1_users  / len(d1_elig)  * 100 if len(d1_elig)  > 0 else 0
        d7_rate  = d7_users  / len(d7_elig)  * 100 if len(d7_elig)  > 0 else 0
        d30_rate = d30_users / len(d30_elig) * 100 if len(d30_elig) > 0 else 0

        rr1, rr2, rr3, rr4 = st.columns(4)
        rr1.metric("D1 Retention",  f"{d1_rate:.1f}%",  delta=f"{d1_users:,} active users",  delta_color="off")
        rr2.metric("D7 Retention",  f"{d7_rate:.1f}%",  delta=f"{d7_users:,} active users",  delta_color="off")
        rr3.metric("D30 Retention", f"{d30_rate:.1f}%", delta=f"{d30_users:,} active users", delta_color="off")
        rr4.metric("D1→D30 Erosion", f"{d1_rate-d30_rate:.1f}pp",
                   delta=f"{d30_rate/d1_rate*100:.0f}% of D1 retained at D30" if d1_rate > 0 else "—",
                   delta_color="inverse")

    sec("Monthly Cohort Retention Heatmap")
    if not fo.empty:
        fo_c = fo.copy()
        fo_c['signup_month'] = pd.to_datetime(fo_c['signup_date']).dt.to_period('M')
        fo_c['order_month']  = fo_c['order_time'].dt.to_period('M')
        fo_c['cohort_idx']   = ((fo_c['order_month'].dt.year - fo_c['signup_month'].dt.year)*12 +
                                 (fo_c['order_month'].dt.month - fo_c['signup_month'].dt.month))
        cp  = fo_c.groupby(['signup_month','cohort_idx'])['user_id'].nunique().unstack(fill_value=0)
        rm  = cp.divide(cp.iloc[:,0], axis=0)
        rm.index = rm.index.astype(str)
        fig = px.imshow(rm, text_auto=".1%", aspect="auto",
                         color_continuous_scale=[[0,'#FFF7F7'],[0.4,'#FCA5A5'],[1.0,R]],
                         labels=dict(x="Months Active", y="Signup Cohort", color="Retention"))
        T(fig, "Cohort Retention — Ordering Users per Month Since Signup", h=400)
        st.plotly_chart(fig, use_container_width=True, key="t3_cohort_heat")

    sec("Day-N Retention Benchmarks")
    if not fu.empty and not fe.empty:
        fe_c2 = fe.copy()
        fe_c2['days_since_signup'] = (fe_c2['event_time'] - pd.to_datetime(fe_c2['signup_date'])).dt.days
        max_date_r2 = df_events['event_time'].max()
        fu_c2 = fu.copy(); fu_c2['acct_age'] = (max_date_r2 - fu_c2['signup_date']).dt.days
        ret_rows = []
        seg_specs = [
            ('onboarding_cohort',['Standard','Frictionless']),
            ('is_zomato_gold',[True,False]),
        ]
        for seg_col, seg_vals in seg_specs:
            for sv in seg_vals:
                lbl  = sv if isinstance(sv,str) else ('Gold' if sv else 'Standard')
                cv_u = fu_c2[fu_c2[seg_col]==sv]['user_id']
                for dn, min_age in [(1,1),(7,7),(30,30)]:
                    elig   = fu_c2[(fu_c2['user_id'].isin(cv_u)) & (fu_c2['acct_age']>=min_age)]['user_id']
                    active = fe_c2[(fe_c2['days_since_signup']==dn) & (fe_c2['user_id'].isin(elig))]['user_id'].nunique()
                    pct    = active/len(elig)*100 if len(elig)>0 else 0
                    ret_rows.append({'Label':lbl,'Day':f'D{dn}','Retention %':pct,'Seg':seg_col})
        ret_df = pd.DataFrame(ret_rows)
        ra, rb = st.columns(2)
        with ra:
            df_onb = ret_df[ret_df['Seg']=='onboarding_cohort']
            fig = px.bar(df_onb, x='Day', y='Retention %', color='Label', barmode='group',
                         color_discrete_map={'Standard':GY,'Frictionless':R}, text_auto='.1f')
            T(fig, "D1/D7/D30 Retention: Onboarding Flow", h=280)
            fig.update_layout(yaxis=dict(ticksuffix='%'))
            st.plotly_chart(fig, use_container_width=True, key="t3_ret_onb")
        with rb:
            df_gld = ret_df[ret_df['Seg']=='is_zomato_gold']
            fig = px.bar(df_gld, x='Day', y='Retention %', color='Label', barmode='group',
                         color_discrete_map={'Gold':R,'Standard':GY}, text_auto='.1f')
            T(fig, "D1/D7/D30 Retention: Gold vs Standard", h=280)
            fig.update_layout(yaxis=dict(ticksuffix='%'))
            st.plotly_chart(fig, use_container_width=True, key="t3_ret_gold")

    sec("Ordering Retention by Acquisition Channel")
    if not fo.empty and 'acquisition_channel' in fo.columns:
        fo_ch = fo.copy()
        fo_ch['cohort_month'] = pd.to_datetime(fo_ch['signup_date']).dt.to_period('M')
        fo_ch['order_month']  = fo_ch['order_time'].dt.to_period('M')
        fo_ch['period'] = ((fo_ch['order_month'].dt.year  - fo_ch['cohort_month'].dt.year)*12 +
                           (fo_ch['order_month'].dt.month - fo_ch['cohort_month'].dt.month))
        fo_ch = fo_ch[fo_ch['period'] >= 0]
        ch_ret_rows = []
        for ch in sorted(fo_ch['acquisition_channel'].dropna().unique()):
            ch_users = fu[fu['acquisition_channel']==ch]['user_id'].nunique()
            ch_data  = fo_ch[fo_ch['acquisition_channel']==ch]
            for period in sorted(ch_data['period'].unique())[:6]:
                active = ch_data[ch_data['period']==period]['user_id'].nunique()
                ch_ret_rows.append({'Channel':ch.replace('_',' ').title(),
                                    'Period':period,
                                    'Retention %':active/ch_users*100 if ch_users>0 else 0})
        df_ch_ret = pd.DataFrame(ch_ret_rows)
        if not df_ch_ret.empty:
            fig = px.line(df_ch_ret, x='Period', y='Retention %', color='Channel',
                          color_discrete_map={k.replace('_',' ').title():v for k,v in CHANNEL_COLORS.items()},
                          markers=True, labels={'Period':'Months After Signup'})
            T(fig, "Retention % by Acquisition Channel Over Time", h=340)
            fig.update_layout(yaxis=dict(ticksuffix='%'), xaxis=dict(dtick=1))
            st.plotly_chart(fig, use_container_width=True, key="t3_ch_ret")

    sec("Repeat Order Behaviour")
    if not fo.empty:
        uoc = (fo.groupby('user_id').size().reset_index(name='orders')
               .merge(fu[['user_id','is_zomato_gold','onboarding_cohort']], on='user_id', how='left'))
        uoc['Type'] = pd.cut(uoc['orders'], bins=[0,1,3,7,9999],
                             labels=['1 Order','2–3 Orders','4–7 Orders','Power User'])
        oa, ob, oc_ = st.columns(3)
        with oa:
            td = uoc['Type'].value_counts().sort_index().reset_index(); td.columns=['Type','Users']
            fig = px.bar(td, x='Type', y='Users', color='Users',
                         color_continuous_scale=[[0,'#FEE2E2'],[1,R]])
            T(fig, "Order Frequency Segments", h=260); fig.update_layout(coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True, key="t3_rep_freq")
        with ob:
            rep = (uoc.groupby('is_zomato_gold')
                   .apply(lambda x: (x['orders']>1).mean()*100).reset_index(name='Repeat %'))
            rep['Status'] = rep['is_zomato_gold'].map({True:'Gold',False:'Standard'})
            fig = px.bar(rep, x='Status', y='Repeat %', color='Status',
                         color_discrete_map={'Gold':R,'Standard':GY}, text_auto='.1f')
            T(fig, "Repeat Rate: Gold vs Standard", h=260)
            fig.update_layout(yaxis=dict(ticksuffix='%'), showlegend=False)
            st.plotly_chart(fig, use_container_width=True, key="t3_rep_gold")
        with oc_:
            rep_coh = (uoc.groupby('onboarding_cohort')
                       .apply(lambda x: (x['orders']>1).mean()*100).reset_index(name='Repeat %'))
            fig = px.bar(rep_coh, x='onboarding_cohort', y='Repeat %', color='onboarding_cohort',
                         color_discrete_map={'Standard':GY,'Frictionless':R},
                         text_auto='.1f', labels={'onboarding_cohort':''})
            T(fig, "Repeat Rate by Onboarding Flow", h=260)
            fig.update_layout(yaxis=dict(ticksuffix='%'), showlegend=False)
            st.plotly_chart(fig, use_container_width=True, key="t3_rep_onb")


with t4:
    sec("User Demographics")
    d1, d2, d3 = st.columns(3)
    with d1:
        sb = fu.groupby(['city_tier','platform']).size().reset_index(name='n')
        fig = px.sunburst(sb, path=['city_tier','platform'], values='n', color='city_tier',
                          color_discrete_map={'Tier_1':R,'Tier_2':OR,'Tier_3':YL})
        T(fig, "Users by City Tier & Platform", h=300)
        st.plotly_chart(fig, use_container_width=True, key="t4_dem_sunburst")
    with d2:
        ab2 = pd.cut(fu['age'], bins=[17,22,26,31,40,60], labels=['18-22','23-26','27-31','32-40','41+'])
        ad = ab2.value_counts().sort_index().reset_index(); ad.columns = ['Age','Count']
        fig = px.bar(ad, x='Age', y='Count', color='Count',
                     color_continuous_scale=[[0,'#FEE2E2'],[1,R]])
        T(fig, "User Age Distribution", h=300); fig.update_layout(coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True, key="t4_dem_age")
    with d3:
        gd = fu['is_zomato_gold'].map({True:'Gold',False:'Standard'}).value_counts().reset_index()
        gd.columns = ['Type','Count']
        fig = px.pie(gd, names='Type', values='Count', hole=0.60,
                     color_discrete_map={'Gold':R,'Standard':'#D1D5DB'})
        fig.update_traces(textinfo='percent+label', textfont_size=11, pull=[0.04,0])
        T(fig, "Membership Mix", h=300); fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True, key="t4_dem_mix")

    sec("AOV by City Tier & Age Group")
    aov_t1, aov_t2 = st.columns(2)
    with aov_t1:
        if not fo.empty:
            tier_aov_new = (fo[fo['order_status']=='Delivered']
                            .groupby('city_tier')['amount_inr'].mean().reset_index()
                            .sort_values('amount_inr'))
            fig = px.bar(tier_aov_new, y='city_tier', x='amount_inr', orientation='h',
                         color='city_tier',
                         color_discrete_map={'Tier_1':R,'Tier_2':OR,'Tier_3':YL},
                         text_auto='.0f', labels={'amount_inr':'AOV ₹','city_tier':''})
            T(fig, "AOV by City Tier", h=240)
            fig.update_layout(showlegend=False, xaxis=dict(tickprefix='₹'))
            st.plotly_chart(fig, use_container_width=True, key="t4_aov_tier_new")
    with aov_t2:
        if not fo.empty and 'age' in fo.columns:
            fo_age_seg = fo[fo['order_status']=='Delivered'].copy()
            fo_age_seg['age_group'] = pd.cut(fo_age_seg['age'],
                                             bins=[17,22,26,31,40,60],
                                             labels=['18-22','23-26','27-31','32-40','41+'])
            age_aov_df = fo_age_seg.groupby('age_group', observed=True)['amount_inr'].mean().reset_index().dropna()
            fig = px.bar(age_aov_df, y='age_group', x='amount_inr', orientation='h',
                          color='amount_inr',
                          color_continuous_scale=[[0,'#DBEAFE'],[1,BL]],
                         text_auto='.0f', labels={'amount_inr':'AOV ₹','age_group':'Age Group'})
            T(fig, "AOV by Age Group", h=240)
            fig.update_layout(coloraxis_showscale=False, xaxis=dict(tickprefix='₹'))
            st.plotly_chart(fig, use_container_width=True, key="t4_aov_age")

    sec("GMV Distribution")
    r1, r2 = st.columns(2)
    with r1:
        city_rev = fo[fo['order_status']=='Delivered'].groupby('city_tier')['amount_inr'].sum().reset_index()
        fig = px.bar(city_rev, x='city_tier', y='amount_inr', color='city_tier',
                     color_discrete_map={'Tier_1':R,'Tier_2':OR,'Tier_3':YL},
                     text_auto='.0f', labels={'amount_inr':'GMV ₹','city_tier':'Tier'})
        T(fig, "Delivered GMV by City Tier", h=260); fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True, key="t4_rev_tier")
    with r2:
        fe_c = fe[fe['event_name']=='app_open'].assign(month=lambda x: x['event_time'].dt.to_period('M').astype(str))
        plat_trend = fe_c.groupby(['month','platform']).size().reset_index(name='sessions')
        fig = px.bar(plat_trend, x='month', y='sessions', color='platform', barmode='stack',
                     color_discrete_sequence=CAT, labels={'sessions':'App Opens'})
        T(fig, "Monthly Sessions by Platform", h=260)
        st.plotly_chart(fig, use_container_width=True, key="t4_rev_plat")

    sec("Channel GMV Deep-Dive")
    cr1, cr2 = st.columns(2)
    with cr1:
        if 'acquisition_channel' in fo.columns and not fo.empty:
            ch_rev = (fo[fo['order_status']=='Delivered']
                      .groupby('acquisition_channel')['amount_inr']
                      .agg(['sum','mean','count']).reset_index())
            ch_rev.columns = ['Channel','Total GMV','AOV','Orders']
            ch_rev['Channel'] = ch_rev['Channel'].str.replace('_',' ').str.title()
            fig = px.bar(ch_rev, x='Channel', y='Total GMV', color='Channel',
                         color_discrete_map={k.replace('_',' ').title():v for k,v in CHANNEL_COLORS.items()},
                         text_auto='.0f', labels={'Total GMV':'GMV ₹'})
            T(fig, "Total GMV by Acquisition Channel", h=290); fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True, key="t4_ch_rev")
    with cr2:
        if 'acquisition_channel' in fo.columns and not fo.empty:
            ch_aov_bar = (fo[fo['order_status']=='Delivered']
                          .groupby('acquisition_channel')['amount_inr']
                          .mean().reset_index())
            ch_aov_bar['Channel'] = ch_aov_bar['acquisition_channel'].str.replace('_',' ').str.title()
            ch_aov_bar = ch_aov_bar.sort_values('amount_inr', ascending=True)
            fig = px.bar(ch_aov_bar, y='Channel', x='amount_inr', orientation='h', color='Channel',
                         color_discrete_map={k.replace('_',' ').title():v for k,v in CHANNEL_COLORS.items()},
                         text_auto='.0f', labels={'amount_inr':'AOV ₹','Channel':''})
            T(fig, "AOV by Acquisition Channel", h=290)
            fig.update_layout(showlegend=False, xaxis=dict(tickprefix='₹'))
            st.plotly_chart(fig, use_container_width=True, key="t4_ch_aov_bar")

    sec("City-Level Performance")
    cy1, cy2 = st.columns(2)
    with cy1:
        if not fo.empty and 'city' in fo.columns:
            city_ord = (fo[fo['order_status']=='Delivered']
                        .groupby('city').size().reset_index(name='Orders')
                        .sort_values('Orders', ascending=True))
            fig = px.bar(city_ord, y='city', x='Orders', orientation='h',
                         color='Orders',
                         color_continuous_scale=[[0,'#FEE2E2'],[1,R]],
                         text_auto='d', labels={'city':''})
            T(fig, "Orders by City", h=max(300, len(city_ord)*22))
            fig.update_layout(coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True, key="t4_city_orders")
    with cy2:
        if not fo.empty and 'city' in fo.columns:
            city_aov_df = (fo[fo['order_status']=='Delivered']
                           .groupby('city')['amount_inr'].mean().reset_index()
                           .sort_values('amount_inr', ascending=True))
            fig = px.bar(city_aov_df, y='city', x='amount_inr', orientation='h',
                         color='amount_inr',
                         color_continuous_scale=[[0,'#FFF3E0'],[1,OR]],
                         text_auto='.0f', labels={'amount_inr':'AOV ₹','city':''})
            T(fig, "AOV by City", h=max(300, len(city_aov_df)*22))
            fig.update_layout(coloraxis_showscale=False, xaxis=dict(tickprefix='₹'))
            st.plotly_chart(fig, use_container_width=True, key="t4_city_aov")


with t5:
    del_o = fo[fo['order_status']=='Delivered']

    sec("GMV KPIs")
    ltv_val = del_o.groupby('user_id')['amount_inr'].sum().mean() if not del_o.empty else 0
    gold_rev = del_o[del_o['delivery_fee']==0]['amount_inr'].sum() if not del_o.empty else 0
    tot_rev  = del_o['amount_inr'].sum() if not del_o.empty else 1

    rk1, rk2, rk3, rk4 = st.columns(4)
    rk1.metric("Delivered GMV",    f"₹{del_o['amount_inr'].sum()/1e6:.2f}M" if not del_o.empty else "—")
    rk2.metric("Avg Order Value",      f"₹{del_o['amount_inr'].mean():,.0f}"     if not del_o.empty else "—")
    rk3.metric("Avg Customer LTV",     f"₹{ltv_val:,.0f}"                        if not del_o.empty else "—")
    rk4.metric("Gold GMV Share",   f"{gold_rev/tot_rev*100:.1f}%"             if tot_rev > 0 else "—")

    sec("Promo Code Impact")
    pa, pb, pc = st.columns(3)
    with pa:
        paov = del_o.groupby('promo_applied')['amount_inr'].mean().reset_index()
        fig = px.bar(paov, x='promo_applied', y='amount_inr', color='promo_applied',
                     color_discrete_sequence=CAT, text_auto='.0f',
                     labels={'amount_inr':'Avg Order ₹','promo_applied':''})
        T(fig, "AOV by Promo Code", h=260); fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True, key="t5_promo_aov")
    with pb:
        pvol = fo.groupby('promo_applied').size().reset_index(name='Orders')
        fig = px.bar(pvol, x='promo_applied', y='Orders', color='promo_applied',
                     color_discrete_sequence=CAT, text_auto='d', labels={'promo_applied':''})
        T(fig, "Order Volume by Promo", h=260); fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True, key="t5_promo_vol")
    with pc:
        prev = del_o.groupby('promo_applied')['amount_inr'].sum().reset_index()
        fig = px.pie(prev, values='amount_inr', names='promo_applied', hole=0.55,
                     color_discrete_sequence=CAT)
        fig.update_traces(textinfo='percent+label', textfont_size=10)
        T(fig, "GMV Share by Promo", h=260); fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True, key="t5_promo_rev")

    sec("Customer Lifetime Value by Acquisition Channel")
    if not del_o.empty and 'acquisition_channel' in del_o.columns:
        ltv_df = del_o.groupby(['user_id','acquisition_channel'])['amount_inr'].sum().reset_index()
        ltv_df.columns = ['user_id','channel','ltv']
        ltv_ch = ltv_df.groupby('channel')['ltv'].mean().reset_index()
        ltv_ch['Channel'] = ltv_ch['channel'].str.replace('_',' ').str.title()
        fig = px.bar(ltv_ch, x='Channel', y='ltv', color='Channel',
                     color_discrete_map={k.replace('_',' ').title():v for k,v in CHANNEL_COLORS.items()},
                     text_auto='.0f', labels={'ltv':'Avg LTV ₹'})
        T(fig, "Average LTV per Customer by Channel", h=300)
        fig.update_layout(showlegend=False, yaxis=dict(tickprefix='₹'))
        st.plotly_chart(fig, use_container_width=True, key="t5_ltv_bar")

    sec("Gold Membership GMV Impact")
    ga, gb = st.columns(2)
    with ga:
        if not del_o.empty:
            del_c = del_o.assign(Membership=del_o['delivery_fee'].apply(lambda x:'Gold' if x==0 else 'Standard'))
            stats = del_c.groupby('Membership').agg(orders=('amount_inr','count'),aov=('amount_inr','mean')).reset_index()
            fig = make_subplots(rows=1, cols=2, subplot_titles=['Order Volume','Avg Order Value ₹'])
            fig.add_trace(go.Bar(x=stats['Membership'], y=stats['orders'], marker_color=[R,GY],
                                 showlegend=False, text=stats['orders'], textposition='outside'), row=1,col=1)
            fig.add_trace(go.Bar(x=stats['Membership'], y=stats['aov'], marker_color=[R,GY],
                                 showlegend=False, text=[f"₹{v:.0f}" for v in stats['aov']],
                                 textposition='outside'), row=1,col=2)
            fig.update_layout(paper_bgcolor=BG, plot_bgcolor=BG, font_color=TK, height=280,
                               margin=dict(l=8,r=8,t=44,b=8),
                               title=dict(text="Gold vs Standard: Volume & AOV",
                                          font=dict(family="Inter",size=13,color=WH)))
            fig.update_xaxes(gridcolor=GRID, linecolor=GRID)
            fig.update_yaxes(gridcolor=GRID, linecolor=GRID)
            st.plotly_chart(fig, use_container_width=True, key="t5_gold_vol_aov")
    with gb:
        if not del_o.empty:
            del_c = del_o.assign(Membership=del_o['delivery_fee'].apply(lambda x:'Gold' if x==0 else 'Standard'))
            gmv_by_mem = del_c.groupby('Membership')['amount_inr'].sum().reset_index()
            gmv_by_mem.columns = ['Membership', 'GMV']
            fig = px.bar(gmv_by_mem, x='Membership', y='GMV', color='Membership',
                         color_discrete_map={'Gold':R,'Standard':GY},
                         text_auto='.0f', labels={'GMV':'GMV ₹'})
            T(fig, "GMV Contribution: Gold vs Standard", h=280)
            fig.update_layout(showlegend=False, yaxis=dict(tickprefix='₹'))
            st.plotly_chart(fig, use_container_width=True, key="t5_gold_gmv_contrib")

    sec("Gold vs Standard — Engagement Depth")
    if not fo.empty:
        uoc_g = fo.groupby('user_id').size().reset_index(name='n_orders')
        uoc_g = uoc_g.merge(fu[['user_id','is_zomato_gold']], on='user_id', how='left')
        uoc_g['Membership'] = uoc_g['is_zomato_gold'].map({True:'Gold',False:'Standard'})
        med_orders = uoc_g.groupby('Membership')['n_orders'].median().reset_index()
        med_orders.columns = ['Membership', 'Median Orders']
        mg1, mg2 = st.columns(2)
        with mg1:
            fig = px.bar(med_orders, x='Membership', y='Median Orders', color='Membership',
                         color_discrete_map={'Gold':R,'Standard':GY}, text_auto='.0f')
            T(fig, "Median Orders per User: Gold vs Standard", h=260)
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True, key="t5_gold_median_orders")
        with mg2:
            rep_g = uoc_g.groupby('Membership').apply(
                lambda x: (x['n_orders'] > 1).mean() * 100).reset_index(name='Repeat %')
            fig = px.bar(rep_g, x='Membership', y='Repeat %', color='Membership',
                         color_discrete_map={'Gold':R,'Standard':GY}, text_auto='.1f')
            T(fig, "Repeat Rate: Gold vs Standard", h=260)
            fig.update_layout(yaxis=dict(ticksuffix='%'), showlegend=False)
            st.plotly_chart(fig, use_container_width=True, key="t5_gold_repeat")


with t6:
    tot_sess = fe['session_id'].nunique()
    crashes  = fe[fe['event_name']=='app_crash']['session_id'].nunique()
    pay_ok   = fe[fe['event_name']=='payment_success']['session_id'].nunique()
    pay_fail = fe[fe['event_name']=='payment_failed']['session_id'].nunique()
    cr_rate  = crashes/tot_sess*100           if tot_sess>0 else 0
    pf_rate  = pay_fail/(pay_ok+pay_fail)*100 if (pay_ok+pay_fail)>0 else 0
    can_rate = len(fo[fo['order_status']=='Cancelled'])/len(fo)*100 if len(fo)>0 else 0

    sec("Platform Health at a Glance")
    oh1,oh2,oh3,oh4 = st.columns(4)
    oh1.metric("App Crash Rate",       f"{cr_rate:.2f}%",  delta="▲ Crashes/Sessions", delta_color="inverse")
    oh2.metric("Payment Failure Rate", f"{pf_rate:.2f}%",  delta="▲ Failed/Attempts",  delta_color="inverse")
    oh3.metric("Order Cancel Rate",    f"{can_rate:.2f}%", delta="▲ Cancelled/Total",  delta_color="inverse")
    oh4.metric("Total Failure Events", f"{crashes+pay_fail:,}")

    sec("Payment Failure & Crash Analysis by Platform")
    cf1, cf2 = st.columns(2)
    with cf1:
        plat_ps = fe[fe['event_name']=='payment_success'].groupby('platform')['session_id'].nunique().reset_index(name='OK')
        plat_pf = fe[fe['event_name']=='payment_failed'].groupby('platform')['session_id'].nunique().reset_index(name='Fail')
        pdf = plat_ps.merge(plat_pf, on='platform', how='outer').fillna(0)
        pdf['Fail %'] = pdf['Fail']/(pdf['OK']+pdf['Fail'])*100
        fig = px.bar(pdf, x='platform', y='Fail %', color='platform',
                     color_discrete_sequence=CAT, text_auto='.1f', labels={'Fail %':'Failure Rate %'})
        T(fig, "Payment Failure Rate by Platform", h=280)
        fig.update_layout(yaxis=dict(ticksuffix='%'), showlegend=False)
        st.plotly_chart(fig, use_container_width=True, key="t6_fail_plat")
    with cf2:
        plat_s = fe.groupby('platform')['session_id'].nunique().reset_index(name='Sessions')
        plat_c = fe[fe['event_name']=='app_crash'].groupby('platform')['session_id'].nunique().reset_index(name='Crashes')
        cdf = plat_s.merge(plat_c, on='platform', how='left').fillna(0)
        cdf['Crash %'] = cdf['Crashes']/cdf['Sessions']*100
        fig = px.bar(cdf, x='platform', y='Crash %', color='platform',
                     color_discrete_sequence=CAT, text_auto='.2f', labels={'Crash %':'Crash Rate %'})
        T(fig, "App Crash Rate by Platform", h=280)
        fig.update_layout(yaxis=dict(ticksuffix='%'), showlegend=False)
        st.plotly_chart(fig, use_container_width=True, key="t6_crash_plat")

    sec("Cancellation by Delivery Time")
    if not fo.empty:
        fo_del_b = fo.assign(del_bucket=pd.cut(fo['delivery_time_mins'],
                             bins=[0,30,45,60,9999], labels=['<30m','30–45m','45–60m','>60m']))
        cr_del = fo_del_b.groupby('del_bucket', observed=False).apply(
            lambda x: (x['order_status']=='Cancelled').mean()*100).reset_index(name='Cancel %')
        fig = px.bar(cr_del, x='del_bucket', y='Cancel %', color='Cancel %',
                     color_continuous_scale=[[0,'#FEE2E2'],[1,R]], text_auto='.1f',
                     labels={'del_bucket':'Delivery Time'})
        T(fig, "Cancellation Rate by Delivery Time Bucket", h=280)
        fig.update_layout(yaxis=dict(ticksuffix='%'), coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True, key="t6_can_del_new")

    sec("Delivery Operations")
    d1, d2 = st.columns(2)
    with d1:
        fig = px.histogram(fo, x='delivery_time_mins', nbins=30,
                           color_discrete_sequence=[R], opacity=0.8)
        T(fig, "Delivery Time Distribution", h=280)
        fig.update_layout(xaxis_title="Delivery Time (mins)")
        st.plotly_chart(fig, use_container_width=True, key="t6_del_time")
    with d2:
        fail_ev = (fe[fe['event_name'].isin(['app_crash','payment_failed'])]
                   ['event_name'].value_counts().reset_index())
        fail_ev.columns = ['Event','Count']
        fig = px.bar(fail_ev, x='Event', y='Count', color='Event',
                     color_discrete_map={'app_crash':R,'payment_failed':OR}, text_auto='d')
        T(fig, "Total Failure Events", h=280); fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True, key="t6_fail_event")

    sec("Order Volume Heatmap — Hour × Day of Week")
    if not fo.empty:
        fo_h = fo.copy()
        fo_h['hour'] = fo_h['order_time'].dt.hour
        fo_h['dow']  = fo_h['order_time'].dt.day_name()
        dow_order = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
        oheat = fo_h.groupby(['dow','hour']).size().reset_index(name='orders')
        ohpiv = oheat.pivot(index='dow', columns='hour', values='orders').reindex(dow_order).fillna(0)
        fig = px.imshow(ohpiv, color_continuous_scale=[[0,'#FFF7F7'],[0.35,'#FCA5A5'],[1.0,R]],
                        labels=dict(x="Hour of Day", y="", color="Orders"), aspect="auto")
        fig.update_traces(text=ohpiv.values.astype(int), texttemplate="%{text}", textfont_size=9)
        T(fig, "Orders Placed by Hour & Day of Week", h=320)
        fig.update_layout(coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True, key="t6_order_heatmap")

    sec("Monthly Order Volume by Status")
    if not fo.empty:
        fo_cm = fo.assign(month=lambda x: x['order_time'].dt.to_period('M').astype(str))
        ms = fo_cm.groupby(['month','order_status']).size().reset_index(name='count')
        fig = px.bar(ms, x='month', y='count', color='order_status', barmode='stack',
                     color_discrete_map={'Delivered':GR,'Cancelled':R},
                     labels={'count':'Orders','order_status':'Status'})
        T(fig, "Monthly Order Volume by Status", h=280)
        st.plotly_chart(fig, use_container_width=True, key="t6_ord_stat")