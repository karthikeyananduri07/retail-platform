"""
=============================================================
CONSUMER SPENDING INTELLIGENCE PLATFORM
Cloud Deployment Version — uses CSV sample data
=============================================================
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Consumer Spending Intelligence",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; }
    .section-title {
        font-size: 16px;
        font-weight: 600;
        margin: 1.5rem 0 0.8rem 0;
        padding-bottom: 6px;
        border-bottom: 1px solid #2a2d3a;
    }
</style>
""", unsafe_allow_html=True)

# ── LOAD DATA ─────────────────────────────────────────────
@st.cache_data
def load_transactions():
    df = pd.read_csv(
        "sample_transactions.csv",
        parse_dates=["invoice_date"]
    )
    return df

@st.cache_data
def load_segments():
    return pd.read_csv("sample_segments.csv")

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
        st.caption("Built with Python + Streamlit\nData: UCI Online Retail II")

    return page, date_range, country

# ── FILTER ────────────────────────────────────────────────
def filter_data(df, date_range, country):
    if len(date_range) == 2:
        start, end = date_range
        df = df[
            (df["invoice_date"].dt.date >= start) &
            (df["invoice_date"].dt.date <= end)
        ]
    if country != "All":
        df = df[df["country"] == country]
    return df

# ── PAGE 1: KPI OVERVIEW ──────────────────────────────────
def page_kpi(df):
    st.markdown("## 📊 KPI Overview")
    st.caption(
        f"Showing {len(df):,} transactions • "
        f"{df['invoice_date'].min().date()} to "
        f"{df['invoice_date'].max().date()}"
    )

    total_revenue   = df["revenue"].sum()
    total_orders    = df["invoice"].nunique()
    total_customers = df[df["customer_id"] != "GUEST"]["customer_id"].nunique()
    aov             = df.groupby("invoice")["revenue"].sum().mean()
    repeat_rate     = (
        df[df["customer_id"] != "GUEST"]
        .groupby("customer_id")["invoice"].nunique()
    )
    repeat_pct = (repeat_rate > 1).mean() * 100

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("💰 Total Revenue",   f"£{total_revenue:,.0f}")
    c2.metric("📦 Total Orders",    f"{total_orders:,}")
    c3.metric("👤 Customers",       f"{total_customers:,}")
    c4.metric("🛒 Avg Order Value", f"£{aov:,.0f}")
    c5.metric("🔄 Repeat Rate",     f"{repeat_pct:.1f}%")

    st.markdown("---")

    # Monthly Revenue
    st.markdown("#### Monthly Revenue Trend")
    monthly = (
        df.groupby(df["invoice_date"].dt.to_period("M"))
        .agg(revenue=("revenue", "sum"))
        .reset_index()
    )
    monthly["month"] = monthly["invoice_date"].astype(str)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=monthly["month"], y=monthly["revenue"],
        fill="tozeroy",
        fillcolor="rgba(79,142,247,0.1)",
        line=dict(color="#4f8ef7", width=2.5),
        mode="lines+markers",
        marker=dict(size=5),
        hovertemplate="£%{y:,.0f}<extra></extra>"
    ))
    fig.update_layout(
        height=320,
        margin=dict(l=10, r=10, t=10, b=10),
        yaxis=dict(tickprefix="£", tickformat=",.0f"),
        showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Revenue by Country (Top 8)")
        country_rev = (
            df.groupby("country")["revenue"]
            .sum().sort_values(ascending=False).head(8)
        )
        fig2 = px.bar(
            x=country_rev.values,
            y=country_rev.index,
            orientation="h",
            color=country_rev.values,
            color_continuous_scale=["#1a3a6a", "#4f8ef7"]
        )
        fig2.update_layout(
            height=300,
            margin=dict(l=10, r=10, t=10, b=10),
            coloraxis_showscale=False,
            xaxis=dict(tickprefix="£", tickformat=",.0f"),
            showlegend=False
        )
        st.plotly_chart(fig2, use_container_width=True)

    with col2:
        st.markdown("#### Sales by Day of Week")
        day_order = ["Monday", "Tuesday", "Wednesday",
                     "Thursday", "Friday", "Saturday", "Sunday"]
        day_rev = (
            df.groupby("day_of_week")["revenue"]
            .sum().reindex(day_order)
        )
        fig3 = px.bar(
            x=day_rev.index,
            y=day_rev.values,
            color=day_rev.values,
            color_continuous_scale=["#1a4a3a", "#36c98e"]
        )
        fig3.update_layout(
            height=300,
            margin=dict(l=10, r=10, t=10, b=10),
            coloraxis_showscale=False,
            yaxis=dict(tickprefix="£", tickformat=",.0f"),
            showlegend=False
        )
        st.plotly_chart(fig3, use_container_width=True)

# ── PAGE 2: SALES ANALYSIS ────────────────────────────────
def page_sales(df):
    st.markdown("## 📈 Sales Analysis")

    st.markdown("#### Top 10 Products by Revenue")
    top = (
        df[df["description"] != "UNKNOWN"]
        .groupby("description")["revenue"]
        .sum().sort_values(ascending=False)
        .head(10).reset_index()
    )
    top.columns = ["Product", "Revenue"]

    fig = px.bar(
        top, x="Revenue", y="Product",
        orientation="h",
        color="Revenue",
        color_continuous_scale=["#1a3a6a", "#4f8ef7"]
    )
    fig.update_layout(
        height=380,
        margin=dict(l=10, r=10, t=10, b=10),
        coloraxis_showscale=False,
        xaxis=dict(tickprefix="£", tickformat=",.0f"),
        yaxis=dict(autorange="reversed")
    )
    st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Sales by Hour of Day")
        hour_rev = df.groupby("hour")["revenue"].sum().reset_index()
        fig2 = px.bar(
            hour_rev, x="hour", y="revenue",
            color="revenue",
            color_continuous_scale=["#1a3a6a", "#4f8ef7"]
        )
        fig2.update_layout(
            height=280,
            margin=dict(l=10, r=10, t=10, b=10),
            coloraxis_showscale=False,
            yaxis=dict(tickprefix="£", tickformat=",.0f")
        )
        st.plotly_chart(fig2, use_container_width=True)

    with col2:
        st.markdown("#### Revenue by Month")
        monthly = (
            df.groupby(["year", "month"])["revenue"]
            .sum().reset_index()
        )
        monthly["period"] = (
            monthly["year"].astype(str) + "-" +
            monthly["month"].astype(str).str.zfill(2)
        )
        fig3 = px.bar(
            monthly, x="period", y="revenue",
            color="revenue",
            color_continuous_scale=["#1a4a3a", "#36c98e"]
        )
        fig3.update_layout(
            height=280,
            margin=dict(l=10, r=10, t=10, b=10),
            coloraxis_showscale=False,
            yaxis=dict(tickprefix="£", tickformat=",.0f"),
            xaxis=dict(tickangle=45)
        )
        st.plotly_chart(fig3, use_container_width=True)

# ── PAGE 3: SEGMENTS ──────────────────────────────────────
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

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Customers", f"{len(rfm):,}")
    champs = len(rfm[rfm["segment"] == "Champion"])
    c2.metric("Champions", f"{champs:,}",
              f"{champs/len(rfm)*100:.1f}% of base")
    at_risk = len(rfm[rfm["segment"] == "At Risk"])
    c3.metric("At Risk", f"{at_risk:,}",
              f"£{rfm[rfm['segment']=='At Risk']['monetary'].sum():,.0f} at stake")
    c4.metric("Avg Customer Value",
              f"£{rfm['monetary'].mean():,.0f}")

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Segment Distribution")
        counts = rfm["segment"].value_counts()
        fig = px.pie(
            values=counts.values,
            names=counts.index,
            hole=0.55,
            color=counts.index,
            color_discrete_map=SEG_COLORS
        )
        fig.update_layout(
            height=320,
            margin=dict(l=10, r=10, t=10, b=10)
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("#### Revenue by Segment")
        seg_rev = (
            rfm.groupby("segment")["monetary"]
            .sum().sort_values(ascending=False)
            .reset_index()
        )
        fig2 = px.bar(
            seg_rev, x="segment", y="monetary",
            color="segment",
            color_discrete_map=SEG_COLORS
        )
        fig2.update_layout(
            height=320,
            margin=dict(l=10, r=10, t=10, b=10),
            showlegend=False,
            yaxis=dict(tickprefix="£", tickformat=",.0f")
        )
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("#### Segment Summary")
    summary = rfm.groupby("segment").agg(
        Customers    =("customer_id", "count"),
        Total_Revenue=("monetary",    "sum"),
        Avg_Spend    =("monetary",    "mean"),
        Avg_Orders   =("frequency",   "mean"),
        Avg_Recency  =("recency",     "mean"),
    ).round(0).sort_values("Total_Revenue", ascending=False)

    summary["Total_Revenue"] = summary["Total_Revenue"].apply(
        lambda x: f"£{x:,.0f}")
    summary["Avg_Spend"] = summary["Avg_Spend"].apply(
        lambda x: f"£{x:,.0f}")
    summary.columns = ["Customers", "Total Revenue",
                       "Avg Spend", "Avg Orders",
                       "Avg Days Since Buy"]
    st.dataframe(summary, use_container_width=True)

    st.markdown("#### Recommended Actions")
    actions = {
        "🏆 Champion"    : "Reward with loyalty program, early access",
        "💚 Loyal"       : "Upsell premium products, ask for reviews",
        "🆕 New Customer": "Welcome email series, first purchase discount",
        "🌱 Potential"   : "Send targeted promotions",
        "⚠️ At Risk"     : "Win-back campaign with special discount",
        "❌ Lost"        : "Last-chance re-engagement email",
    }
    for seg, action in actions.items():
        st.info(f"**{seg}** → {action}")

# ── PAGE 4: EXPLORER ──────────────────────────────────────
def page_explorer(df):
    st.markdown("## 🔍 Customer Explorer")
    st.markdown("Search any customer to see their full profile.")

    rfm     = load_segments()
    known   = df[df["customer_id"] != "GUEST"]
    cust_ids = sorted(known["customer_id"].unique().tolist())

    selected = st.selectbox("Select Customer ID", cust_ids)

    if selected:
        cdf     = known[known["customer_id"] == selected]
        seg_row = rfm[rfm["customer_id"] == selected]

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Total Orders",    cdf["invoice"].nunique())
        c2.metric("Total Spent",     f"£{cdf['revenue'].sum():,.2f}")
        c3.metric("Avg Order Value",
                  f"£{cdf.groupby('invoice')['revenue'].sum().mean():,.2f}")
        c4.metric("First Purchase",
                  str(cdf["invoice_date"].min().date()))
        if not seg_row.empty:
            c5.metric("Segment", seg_row["segment"].values[0])

        if not seg_row.empty:
            st.markdown("#### RFM Profile")
            r1, r2, r3, r4 = st.columns(4)
            r1.metric("Recency",
                      f"{seg_row['recency'].values[0]:.0f} days ago")
            r2.metric("Frequency",
                      f"{seg_row['frequency'].values[0]:.0f} orders")
            r3.metric("Monetary",
                      f"£{seg_row['monetary'].values[0]:,.2f}")
            r4.metric("RFM Score",
                      f"{seg_row['rfm_score'].values[0]:.0f} / 15")

        st.markdown("#### Purchase History")
        monthly = (
            cdf.groupby(cdf["invoice_date"].dt.to_period("M"))
            ["revenue"].sum().reset_index()
        )
        monthly["month"] = monthly["invoice_date"].astype(str)
        fig = px.bar(monthly, x="month", y="revenue",
                     color_discrete_sequence=["#4f8ef7"])
        fig.update_layout(
            height=260,
            margin=dict(l=10, r=10, t=10, b=10),
            yaxis=dict(tickprefix="£", tickformat=",.0f")
        )
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("#### All Transactions")
        table = (
            cdf[["invoice_date", "invoice", "description",
                 "quantity", "price", "revenue", "country"]]
            .sort_values("invoice_date", ascending=False)
            .head(50)
        )
        table["invoice_date"] = table["invoice_date"].dt.strftime(
            "%Y-%m-%d %H:%M")
        table["revenue"] = table["revenue"].apply(lambda x: f"£{x:.2f}")
        table["price"]   = table["price"].apply(lambda x: f"£{x:.2f}")
        st.dataframe(table, use_container_width=True, height=300)

# ── MAIN ──────────────────────────────────────────────────
def main():
    page, date_range, country = render_sidebar()

    df = load_transactions()
    df = filter_data(df, date_range, country)

    if df.empty:
        st.warning("No data found for selected filters.")
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
