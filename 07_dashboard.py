"""
=============================================================
PHASE 7 — STREAMLIT DASHBOARD
Consumer Spending Intelligence Platform
=============================================================
Run: streamlit run 07_dashboard.py
=============================================================
"""

import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# ── CONFIG ────────────────────────────────────────────────
DB_PATH = "data/retail.db"

st.set_page_config(
    page_title="Consumer Spending Intelligence",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── CUSTOM CSS ────────────────────────────────────────────
st.markdown("""
<style>
    .main { background-color: #0f1117; }
    .block-container { padding-top: 1.5rem; }
    .metric-card {
        background: #1a1d27;
        border-radius: 12px;
        padding: 16px 20px;
        border: 1px solid #2a2d3a;
        text-align: center;
    }
    .metric-value {
        font-size: 28px;
        font-weight: 700;
        color: #4f8ef7;
        margin: 4px 0;
    }
    .metric-label {
        font-size: 12px;
        color: #888;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .metric-delta {
        font-size: 12px;
        color: #36c98e;
        margin-top: 2px;
    }
    .section-title {
        font-size: 16px;
        font-weight: 600;
        color: #e0e0e0;
        margin: 1.5rem 0 0.8rem 0;
        padding-bottom: 6px;
        border-bottom: 1px solid #2a2d3a;
    }
    div[data-testid="stSelectbox"] label { color: #aaa; }
    div[data-testid="stMetric"] { background: #1a1d27; border-radius: 10px; padding: 12px; }
</style>
""", unsafe_allow_html=True)


# ── DATA LOADING ──────────────────────────────────────────
@st.cache_data
def load_transactions():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM clean_transactions", conn)
    conn.close()
    df["invoice_date"] = pd.to_datetime(df["invoice_date"])
    return df

@st.cache_data
def load_segments():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM customer_segments", conn)
    conn.close()
    return df


# ── SIDEBAR ───────────────────────────────────────────────
def render_sidebar():
    with st.sidebar:
        st.markdown("## 🛒 Spend Intelligence")
        st.markdown("---")

        page = st.radio(
            "Navigate",
            ["📊 KPI Overview",
             "📈 Sales Analysis",
             "👥 Customer Segments",
             "🔍 Customer Explorer"],
            label_visibility="collapsed"
        )

        st.markdown("---")
        st.markdown("### Filters")

        df = load_transactions()
        min_date = df["invoice_date"].min().date()
        max_date = df["invoice_date"].max().date()

        date_range = st.date_input(
            "Date Range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )

        countries = ["All"] + sorted(df["country"].unique().tolist())
        country = st.selectbox("Country", countries)

        st.markdown("---")
        st.markdown(
            "<div style='color:#555;font-size:11px;text-align:center'>"
            "Consumer Spending Intelligence<br>Built with Python + Streamlit"
            "</div>",
            unsafe_allow_html=True
        )

    return page, date_range, country


# ── FILTER DATA ───────────────────────────────────────────
def filter_data(df, date_range, country):
    if len(date_range) == 2:
        start, end = date_range
        df = df[(df["invoice_date"].dt.date >= start) &
                (df["invoice_date"].dt.date <= end)]
    if country != "All":
        df = df[df["country"] == country]
    return df


# ── PAGE 1: KPI OVERVIEW ──────────────────────────────────
def page_kpi(df):
    st.markdown("## 📊 KPI Overview")
    st.markdown(
        f"<div style='color:#555;font-size:13px;margin-bottom:1rem'>"
        f"Showing {len(df):,} transactions • "
        f"{df['invoice_date'].min().date()} to {df['invoice_date'].max().date()}"
        f"</div>",
        unsafe_allow_html=True
    )

    # ── KPI Cards
    total_revenue  = df["revenue"].sum()
    total_orders   = df["invoice"].nunique()
    total_customers= df[df["customer_id"] != "GUEST"]["customer_id"].nunique()
    aov            = df.groupby("invoice")["revenue"].sum().mean()
    repeat_rate    = df[df["customer_id"] != "GUEST"].groupby(
                        "customer_id")["invoice"].nunique()
    repeat_pct     = (repeat_rate > 1).mean() * 100

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.metric("💰 Total Revenue",   f"£{total_revenue:,.0f}")
    with c2:
        st.metric("📦 Total Orders",    f"{total_orders:,}")
    with c3:
        st.metric("👤 Customers",       f"{total_customers:,}")
    with c4:
        st.metric("🛒 Avg Order Value", f"£{aov:,.0f}")
    with c5:
        st.metric("🔄 Repeat Rate",     f"{repeat_pct:.1f}%")

    st.markdown("---")

    # ── Monthly Revenue Trend
    st.markdown('<div class="section-title">Monthly Revenue Trend</div>',
                unsafe_allow_html=True)

    monthly = (df.groupby(df["invoice_date"].dt.to_period("M"))
               .agg(revenue=("revenue","sum"),
                    orders=("invoice","nunique"))
               .reset_index())
    monthly["month"] = monthly["invoice_date"].astype(str)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=monthly["month"], y=monthly["revenue"],
        fill="tozeroy", fillcolor="rgba(79,142,247,0.1)",
        line=dict(color="#4f8ef7", width=2.5),
        mode="lines+markers", marker=dict(size=5),
        name="Revenue", hovertemplate="£%{y:,.0f}<extra></extra>"
    ))
    fig.update_layout(
        plot_bgcolor="#1a1d27", paper_bgcolor="#0f1117",
        font_color="#aaa", height=320,
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(gridcolor="#2a2d3a", showgrid=True),
        yaxis=dict(gridcolor="#2a2d3a", tickprefix="£",
                   tickformat=",.0f"),
        showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── Bottom row
    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="section-title">Revenue by Country (Top 8)</div>',
                    unsafe_allow_html=True)
        country_rev = (df.groupby("country")["revenue"]
                       .sum().sort_values(ascending=False).head(8))
        fig2 = px.bar(
            x=country_rev.values, y=country_rev.index,
            orientation="h",
            color=country_rev.values,
            color_continuous_scale=["#1a3a6a","#4f8ef7"],
        )
        fig2.update_layout(
            plot_bgcolor="#1a1d27", paper_bgcolor="#1a1d27",
            font_color="#aaa", height=300,
            margin=dict(l=10, r=10, t=10, b=10),
            coloraxis_showscale=False,
            xaxis=dict(tickprefix="£", tickformat=",.0f",
                       gridcolor="#2a2d3a"),
            yaxis=dict(gridcolor="#2a2d3a"),
            showlegend=False
        )
        st.plotly_chart(fig2, use_container_width=True)

    with col2:
        st.markdown('<div class="section-title">Sales by Day of Week</div>',
                    unsafe_allow_html=True)
        day_order = ["Monday","Tuesday","Wednesday",
                     "Thursday","Friday","Saturday","Sunday"]
        day_rev = (df.groupby("day_of_week")["revenue"]
                   .sum().reindex(day_order))
        fig3 = px.bar(
            x=day_rev.index, y=day_rev.values,
            color=day_rev.values,
            color_continuous_scale=["#1a4a3a","#36c98e"],
        )
        fig3.update_layout(
            plot_bgcolor="#1a1d27", paper_bgcolor="#1a1d27",
            font_color="#aaa", height=300,
            margin=dict(l=10, r=10, t=10, b=10),
            coloraxis_showscale=False,
            yaxis=dict(tickprefix="£", tickformat=",.0f",
                       gridcolor="#2a2d3a"),
            xaxis=dict(gridcolor="#2a2d3a"),
            showlegend=False
        )
        st.plotly_chart(fig3, use_container_width=True)


# ── PAGE 2: SALES ANALYSIS ────────────────────────────────
def page_sales(df):
    st.markdown("## 📈 Sales Analysis")

    # Top products
    st.markdown('<div class="section-title">Top 10 Products by Revenue</div>',
                unsafe_allow_html=True)
    top = (df[df["description"] != "UNKNOWN"]
           .groupby("description")["revenue"]
           .sum().sort_values(ascending=False).head(10)
           .reset_index())
    top.columns = ["Product", "Revenue"]

    fig = px.bar(top, x="Revenue", y="Product",
                 orientation="h",
                 color="Revenue",
                 color_continuous_scale=["#1a3a6a","#4f8ef7"])
    fig.update_layout(
        plot_bgcolor="#1a1d27", paper_bgcolor="#0f1117",
        font_color="#aaa", height=380,
        margin=dict(l=10, r=10, t=10, b=10),
        coloraxis_showscale=False,
        xaxis=dict(tickprefix="£", tickformat=",.0f",
                   gridcolor="#2a2d3a"),
        yaxis=dict(autorange="reversed", gridcolor="#2a2d3a")
    )
    st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="section-title">Sales by Hour of Day</div>',
                    unsafe_allow_html=True)
        hour_rev = df.groupby("hour")["revenue"].sum().reset_index()
        fig2 = px.bar(hour_rev, x="hour", y="revenue",
                      color="revenue",
                      color_continuous_scale=["#1a3a6a","#4f8ef7"])
        fig2.update_layout(
            plot_bgcolor="#1a1d27", paper_bgcolor="#1a1d27",
            font_color="#aaa", height=280,
            margin=dict(l=10,r=10,t=10,b=10),
            coloraxis_showscale=False,
            yaxis=dict(tickprefix="£",tickformat=",.0f",
                       gridcolor="#2a2d3a"),
            xaxis=dict(gridcolor="#2a2d3a",
                       tickvals=list(range(0,24,2)))
        )
        st.plotly_chart(fig2, use_container_width=True)

    with col2:
        st.markdown('<div class="section-title">Monthly Orders vs Revenue</div>',
                    unsafe_allow_html=True)
        monthly = (df.groupby(df["invoice_date"].dt.to_period("M"))
                   .agg(revenue=("revenue","sum"),
                        orders=("invoice","nunique"))
                   .reset_index())
        monthly["month"] = monthly["invoice_date"].astype(str)
        fig3 = px.scatter(monthly, x="orders", y="revenue",
                          text="month",
                          color="revenue",
                          color_continuous_scale=["#1a4a3a","#36c98e"])
        fig3.update_traces(textposition="top center",
                           textfont_size=8, marker_size=8)
        fig3.update_layout(
            plot_bgcolor="#1a1d27", paper_bgcolor="#1a1d27",
            font_color="#aaa", height=280,
            margin=dict(l=10,r=10,t=10,b=10),
            coloraxis_showscale=False,
            yaxis=dict(tickprefix="£",tickformat=",.0f",
                       gridcolor="#2a2d3a"),
            xaxis=dict(gridcolor="#2a2d3a")
        )
        st.plotly_chart(fig3, use_container_width=True)


# ── PAGE 3: CUSTOMER SEGMENTS ─────────────────────────────
def page_segments():
    st.markdown("## 👥 Customer Segments")

    rfm = load_segments()

    SEG_COLORS = {
        "Champion"    : "#4f8ef7",
        "Loyal"       : "#36c98e",
        "New Customer": "#f7c948",
        "Potential"   : "#a78bfa",
        "At Risk"     : "#f97316",
        "Lost"        : "#ef4444",
    }

    # KPIs
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total Customers", f"{len(rfm):,}")
    with c2:
        champs = len(rfm[rfm["segment"]=="Champion"])
        st.metric("Champions", f"{champs:,}",
                  f"{champs/len(rfm)*100:.1f}% of base")
    with c3:
        at_risk = len(rfm[rfm["segment"]=="At Risk"])
        st.metric("At Risk", f"{at_risk:,}",
                  f"£{rfm[rfm['segment']=='At Risk']['monetary'].sum():,.0f} at stake")
    with c4:
        avg_spend = rfm["monetary"].mean()
        st.metric("Avg Customer Value", f"£{avg_spend:,.0f}")

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="section-title">Segment Distribution</div>',
                    unsafe_allow_html=True)
        counts = rfm["segment"].value_counts()
        fig = px.pie(
            values=counts.values, names=counts.index,
            hole=0.55,
            color=counts.index,
            color_discrete_map=SEG_COLORS
        )
        fig.update_layout(
            plot_bgcolor="#1a1d27", paper_bgcolor="#1a1d27",
            font_color="#aaa", height=320,
            margin=dict(l=10,r=10,t=10,b=10),
            legend=dict(font=dict(color="#aaa"))
        )
        fig.update_traces(textfont_color="white")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown('<div class="section-title">Revenue by Segment</div>',
                    unsafe_allow_html=True)
        seg_rev = (rfm.groupby("segment")["monetary"]
                   .sum().sort_values(ascending=False)
                   .reset_index())
        fig2 = px.bar(seg_rev, x="segment", y="monetary",
                      color="segment",
                      color_discrete_map=SEG_COLORS)
        fig2.update_layout(
            plot_bgcolor="#1a1d27", paper_bgcolor="#1a1d27",
            font_color="#aaa", height=320,
            margin=dict(l=10,r=10,t=10,b=10),
            showlegend=False,
            yaxis=dict(tickprefix="£",tickformat=",.0f",
                       gridcolor="#2a2d3a"),
            xaxis=dict(gridcolor="#2a2d3a")
        )
        st.plotly_chart(fig2, use_container_width=True)

    # Segment Table
    st.markdown('<div class="section-title">Segment Summary Table</div>',
                unsafe_allow_html=True)
    summary = rfm.groupby("segment").agg(
        Customers    = ("customer_id", "count"),
        Total_Revenue= ("monetary",    "sum"),
        Avg_Spend    = ("monetary",    "mean"),
        Avg_Orders   = ("frequency",   "mean"),
        Avg_Recency  = ("recency",     "mean"),
    ).round(0).sort_values("Total_Revenue", ascending=False)

    summary["Total_Revenue"] = summary["Total_Revenue"].apply(
        lambda x: f"£{x:,.0f}")
    summary["Avg_Spend"]     = summary["Avg_Spend"].apply(
        lambda x: f"£{x:,.0f}")
    summary.columns = ["Customers","Total Revenue",
                       "Avg Spend","Avg Orders","Avg Days Since Buy"]
    st.dataframe(summary, use_container_width=True)

    # Business Actions
    st.markdown('<div class="section-title">Recommended Actions</div>',
                unsafe_allow_html=True)
    actions = {
        "🏆 Champion"    : "Reward with loyalty program, early access to new products",
        "💚 Loyal"       : "Upsell premium products, ask for reviews",
        "🆕 New Customer": "Welcome email series, first purchase discount",
        "🌱 Potential"   : "Send targeted promotions, product recommendations",
        "⚠️ At Risk"     : "Win-back campaign with special discount offer",
        "❌ Lost"        : "Last-chance re-engagement email, survey why they left",
    }
    for seg, action in actions.items():
        st.markdown(
            f"<div style='background:#1a1d27;border-radius:8px;"
            f"padding:10px 14px;margin-bottom:6px;border:1px solid #2a2d3a'>"
            f"<b style='color:#e0e0e0'>{seg}</b> "
            f"<span style='color:#888'>→ {action}</span></div>",
            unsafe_allow_html=True
        )


# ── PAGE 4: CUSTOMER EXPLORER ─────────────────────────────
def page_explorer(df):
    st.markdown("## 🔍 Customer Explorer")
    st.markdown("Search any customer to see their full profile and purchase history.")

    rfm = load_segments()
    known = df[df["customer_id"] != "GUEST"]

    # Search
    customer_ids = sorted(known["customer_id"].unique().tolist())
    selected = st.selectbox(
        "Select Customer ID",
        customer_ids,
        index=0
    )

    if selected:
        cdf = known[known["customer_id"] == selected].copy()
        seg_row = rfm[rfm["customer_id"] == selected]

        # Profile cards
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Total Orders",
                      cdf["invoice"].nunique())
        with col2:
            st.metric("Total Spent",
                      f"£{cdf['revenue'].sum():,.2f}")
        with col3:
            st.metric("Avg Order Value",
                      f"£{cdf.groupby('invoice')['revenue'].sum().mean():,.2f}")
        with col4:
            st.metric("First Purchase",
                      str(cdf["invoice_date"].min().date()))
        with col5:
            if not seg_row.empty:
                seg = seg_row["segment"].values[0]
                st.metric("Segment", seg)

        # RFM scores
        if not seg_row.empty:
            st.markdown('<div class="section-title">RFM Profile</div>',
                        unsafe_allow_html=True)
            r1, r2, r3, r4 = st.columns(4)
            with r1:
                st.metric("Recency",
                          f"{seg_row['recency'].values[0]:.0f} days ago")
            with r2:
                st.metric("Frequency",
                          f"{seg_row['frequency'].values[0]:.0f} orders")
            with r3:
                st.metric("Monetary",
                          f"£{seg_row['monetary'].values[0]:,.2f}")
            with r4:
                st.metric("RFM Score",
                          f"{seg_row['rfm_score'].values[0]:.0f} / 15")

        # Revenue over time
        st.markdown('<div class="section-title">Purchase History Over Time</div>',
                    unsafe_allow_html=True)
        monthly = (cdf.groupby(cdf["invoice_date"].dt.to_period("M"))
                   ["revenue"].sum().reset_index())
        monthly["month"] = monthly["invoice_date"].astype(str)

        fig = px.bar(monthly, x="month", y="revenue",
                     color_discrete_sequence=["#4f8ef7"])
        fig.update_layout(
            plot_bgcolor="#1a1d27", paper_bgcolor="#0f1117",
            font_color="#aaa", height=260,
            margin=dict(l=10,r=10,t=10,b=10),
            yaxis=dict(tickprefix="£",tickformat=",.0f",
                       gridcolor="#2a2d3a"),
            xaxis=dict(gridcolor="#2a2d3a")
        )
        st.plotly_chart(fig, use_container_width=True)

        # Transaction table
        st.markdown('<div class="section-title">All Transactions</div>',
                    unsafe_allow_html=True)
        table = (cdf[["invoice_date","invoice","description",
                      "quantity","price","revenue","country"]]
                 .sort_values("invoice_date", ascending=False)
                 .head(50))
        table["invoice_date"] = table["invoice_date"].dt.strftime("%Y-%m-%d %H:%M")
        table["revenue"] = table["revenue"].apply(lambda x: f"£{x:.2f}")
        table["price"]   = table["price"].apply(lambda x: f"£{x:.2f}")
        st.dataframe(table, use_container_width=True, height=300)


# ── MAIN ──────────────────────────────────────────────────
def main():
    page, date_range, country = render_sidebar()

    df = load_transactions()
    df = filter_data(df, date_range, country)

    if df.empty:
        st.warning("No data found for the selected filters.")
        return

    if page == "📊 KPI Overview":
        page_kpi(df)
    elif page == "📈 Sales Analysis":
        page_sales(df)
    elif page == "👥 Customer Segments":
        page_segments()
    elif page == "🔍 Customer Explorer":
        page_explorer(df)


if __name__ == "__main__":
    main()