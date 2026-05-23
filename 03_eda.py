"""
=============================================================
PHASE 3 — EXPLORATORY DATA ANALYSIS (EDA)
Consumer Spending Intelligence Platform
=============================================================
What this script does:
  1. Monthly revenue trend
  2. Top 10 best selling products
  3. Revenue by country
  4. Sales by day of week
  5. Sales by hour of day
  6. Average order value
  7. Customer purchase frequency
  8. Saves all charts to outputs/ folder
  9. Saves a text summary report

Run: python 03_eda.py
=============================================================
"""

import pandas as pd
import sqlite3
import os
import matplotlib
matplotlib.use("Agg")  # no display needed — saves to file
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from datetime import datetime

# ── CONFIG ────────────────────────────────────────────────
DB_PATH     = "data/retail.db"
OUTPUT_DIR  = "outputs"

# Chart style
BG_COLOR    = "#0f1117"
CARD_COLOR  = "#1a1d27"
ACCENT      = "#4f8ef7"
ACCENT2     = "#36c98e"
TEXT_COLOR  = "#e0e0e0"
MUTED_COLOR = "#888888"

# ── HELPER ────────────────────────────────────────────────
def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def save_fig(filename):
    path = os.path.join(OUTPUT_DIR, filename)
    plt.savefig(path, dpi=150, bbox_inches="tight",
                facecolor=BG_COLOR, edgecolor="none")
    plt.close()
    log(f"  Saved → outputs/{filename}")

def setup_ax(ax, title):
    """Apply consistent dark theme to any axis."""
    ax.set_facecolor(CARD_COLOR)
    ax.set_title(title, color=TEXT_COLOR, fontsize=13,
                 fontweight="bold", pad=12)
    ax.tick_params(colors=MUTED_COLOR, labelsize=9)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#333344")
    ax.spines["bottom"].set_color("#333344")
    ax.yaxis.label.set_color(MUTED_COLOR)
    ax.xaxis.label.set_color(MUTED_COLOR)
    ax.grid(axis="y", color="#333344", linewidth=0.5, linestyle="--")


# ── LOAD DATA ─────────────────────────────────────────────
def load_data():
    log(f"Loading clean_transactions from {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM clean_transactions", conn)
    conn.close()
    df["invoice_date"] = pd.to_datetime(df["invoice_date"])
    log(f"  Loaded {len(df):,} rows ✓")
    return df


# ── CHART 1: MONTHLY REVENUE TREND ───────────────────────
def chart_monthly_revenue(df):
    log("Generating Chart 1 — Monthly Revenue Trend...")

    monthly = (df.groupby(["year", "month"])["revenue"]
               .sum()
               .reset_index()
               .sort_values(["year", "month"]))
    monthly["label"] = (monthly["month"].astype(str).str.zfill(2)
                        + "/" + monthly["year"].astype(str).str[-2:])

    fig, ax = plt.subplots(figsize=(14, 5), facecolor=BG_COLOR)
    setup_ax(ax, "Monthly Revenue Trend (Dec 2009 – Dec 2011)")

    x = range(len(monthly))
    ax.fill_between(x, monthly["revenue"], alpha=0.15, color=ACCENT)
    ax.plot(x, monthly["revenue"], color=ACCENT, linewidth=2.5,
            marker="o", markersize=4)

    # Highlight peak month
    peak_idx = monthly["revenue"].idxmax()
    peak_row = monthly.loc[peak_idx]
    ax.annotate(
        f"Peak: £{peak_row['revenue']/1000:.0f}K",
        xy=(list(monthly.index).index(peak_idx), peak_row["revenue"]),
        xytext=(0, 18), textcoords="offset points",
        color=ACCENT2, fontsize=9, ha="center",
        arrowprops=dict(arrowstyle="->", color=ACCENT2, lw=1)
    )

    ax.set_xticks(x)
    ax.set_xticklabels(monthly["label"], rotation=45, ha="right")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(
        lambda v, _: f"£{v/1000:.0f}K"))
    ax.set_ylabel("Revenue")

    plt.tight_layout()
    save_fig("01_monthly_revenue.png")


# ── CHART 2: TOP 10 PRODUCTS ──────────────────────────────
def chart_top_products(df):
    log("Generating Chart 2 — Top 10 Products by Revenue...")

    top = (df[df["description"] != "UNKNOWN"]
           .groupby("description")["revenue"]
           .sum()
           .sort_values(ascending=True)
           .tail(10))

    fig, ax = plt.subplots(figsize=(10, 6), facecolor=BG_COLOR)
    setup_ax(ax, "Top 10 Products by Revenue")

    bars = ax.barh(range(len(top)), top.values,
                   color=ACCENT, alpha=0.85, height=0.6)

    # Value labels on bars
    for bar, val in zip(bars, top.values):
        ax.text(val + 2000, bar.get_y() + bar.get_height()/2,
                f"£{val/1000:.0f}K",
                va="center", ha="left",
                color=TEXT_COLOR, fontsize=9)

    ax.set_yticks(range(len(top)))
    ax.set_yticklabels([t[:35] for t in top.index],
                       color=TEXT_COLOR, fontsize=9)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(
        lambda v, _: f"£{v/1000:.0f}K"))
    ax.set_xlabel("Total Revenue")

    plt.tight_layout()
    save_fig("02_top_products.png")


# ── CHART 3: REVENUE BY COUNTRY ───────────────────────────
def chart_revenue_by_country(df):
    log("Generating Chart 3 — Revenue by Country (Top 10)...")

    country = (df.groupby("country")["revenue"]
               .sum()
               .sort_values(ascending=False)
               .head(10))

    # Separate UK from the rest for color emphasis
    colors = [ACCENT if c == "United Kingdom" else ACCENT2
              for c in country.index]

    fig, ax = plt.subplots(figsize=(10, 5), facecolor=BG_COLOR)
    setup_ax(ax, "Revenue by Country (Top 10)")

    bars = ax.bar(range(len(country)), country.values,
                  color=colors, alpha=0.85, width=0.6)

    for bar, val in zip(bars, country.values):
        ax.text(bar.get_x() + bar.get_width()/2,
                bar.get_height() + 50000,
                f"£{val/1000:.0f}K",
                ha="center", va="bottom",
                color=TEXT_COLOR, fontsize=8)

    ax.set_xticks(range(len(country)))
    ax.set_xticklabels(country.index, rotation=30,
                       ha="right", color=TEXT_COLOR, fontsize=9)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(
        lambda v, _: f"£{v/1000:.0f}K"))
    ax.set_ylabel("Total Revenue")

    plt.tight_layout()
    save_fig("03_revenue_by_country.png")


# ── CHART 4: SALES BY DAY OF WEEK ────────────────────────
def chart_sales_by_day(df):
    log("Generating Chart 4 — Sales by Day of Week...")

    day_order = ["Monday", "Tuesday", "Wednesday",
                 "Thursday", "Friday", "Saturday", "Sunday"]
    day_rev = (df.groupby("day_of_week")["revenue"]
               .sum()
               .reindex(day_order))

    colors = [ACCENT if v == day_rev.max() else "#3a5a8a"
              for v in day_rev.values]

    fig, ax = plt.subplots(figsize=(9, 5), facecolor=BG_COLOR)
    setup_ax(ax, "Revenue by Day of Week")

    bars = ax.bar(range(7), day_rev.values,
                  color=colors, alpha=0.85, width=0.6)

    for bar, val in zip(bars, day_rev.values):
        ax.text(bar.get_x() + bar.get_width()/2,
                bar.get_height() + 20000,
                f"£{val/1000:.0f}K",
                ha="center", va="bottom",
                color=TEXT_COLOR, fontsize=9)

    ax.set_xticks(range(7))
    ax.set_xticklabels(day_order, color=TEXT_COLOR)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(
        lambda v, _: f"£{v/1000:.0f}K"))
    ax.set_ylabel("Total Revenue")

    plt.tight_layout()
    save_fig("04_sales_by_day.png")


# ── CHART 5: SALES BY HOUR ────────────────────────────────
def chart_sales_by_hour(df):
    log("Generating Chart 5 — Sales by Hour of Day...")

    hour_rev = (df.groupby("hour")["revenue"]
                .sum()
                .sort_index())

    fig, ax = plt.subplots(figsize=(11, 5), facecolor=BG_COLOR)
    setup_ax(ax, "Revenue by Hour of Day")

    colors = [ACCENT if v == hour_rev.max() else "#2a4a7a"
              for v in hour_rev.values]

    ax.bar(hour_rev.index, hour_rev.values,
           color=colors, alpha=0.85, width=0.7)
    ax.fill_between(hour_rev.index, hour_rev.values,
                    alpha=0.08, color=ACCENT)

    ax.set_xticks(hour_rev.index)
    ax.set_xticklabels([f"{h:02d}:00" for h in hour_rev.index],
                       rotation=45, ha="right", color=TEXT_COLOR, fontsize=8)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(
        lambda v, _: f"£{v/1000:.0f}K"))
    ax.set_ylabel("Total Revenue")
    ax.set_xlabel("Hour of Day")

    plt.tight_layout()
    save_fig("05_sales_by_hour.png")


# ── CHART 6: PURCHASE FREQUENCY ───────────────────────────
def chart_purchase_frequency(df):
    log("Generating Chart 6 — Customer Purchase Frequency...")

    known = df[df["customer_id"] != "GUEST"]
    freq = (known.groupby("customer_id")["invoice"]
            .nunique()
            .clip(upper=20))  # cap at 20 for readability

    fig, ax = plt.subplots(figsize=(10, 5), facecolor=BG_COLOR)
    setup_ax(ax, "Customer Purchase Frequency (orders per customer)")

    ax.hist(freq, bins=20, color=ACCENT2, alpha=0.8, edgecolor=BG_COLOR)
    ax.axvline(freq.mean(), color=ACCENT, linewidth=2,
               linestyle="--", label=f"Mean: {freq.mean():.1f} orders")
    ax.legend(facecolor=CARD_COLOR, labelcolor=TEXT_COLOR, fontsize=9)

    ax.set_xlabel("Number of Orders")
    ax.set_ylabel("Number of Customers")

    plt.tight_layout()
    save_fig("06_purchase_frequency.png")


# ── TEXT SUMMARY REPORT ───────────────────────────────────
def save_text_report(df):
    log("Generating text summary report...")

    known = df[df["customer_id"] != "GUEST"]
    freq  = known.groupby("customer_id")["invoice"].nunique()
    aov   = df.groupby("invoice")["revenue"].sum().mean()
    best_day  = df.groupby("day_of_week")["revenue"].sum().idxmax()
    best_hour = df.groupby("hour")["revenue"].sum().idxmax()
    top_product = (df[df["description"] != "UNKNOWN"]
                   .groupby("description")["revenue"]
                   .sum().idxmax())
    top_country = df.groupby("country")["revenue"].sum().idxmax()

    report = f"""
==============================================================
  EDA REPORT — CONSUMER SPENDING INTELLIGENCE PLATFORM
  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
==============================================================

DATASET OVERVIEW
  Total transactions        : {len(df):,}
  Unique customers          : {df['customer_id'].nunique():,}
  Unique products           : {df['stockcode'].nunique():,}
  Unique invoices (orders)  : {df['invoice'].nunique():,}
  Countries                 : {df['country'].nunique()}
  Date range                : {df['invoice_date'].min().date()} → {df['invoice_date'].max().date()}

REVENUE METRICS
  Total revenue             : £{df['revenue'].sum():,.2f}
  Average order value (AOV) : £{aov:,.2f}
  Highest single order      : £{df.groupby('invoice')['revenue'].sum().max():,.2f}
  Lowest single order       : £{df.groupby('invoice')['revenue'].sum().min():,.2f}

TOP INSIGHTS
  Best selling product      : {top_product}
  Top revenue country       : {top_country}
  Best day to sell          : {best_day}
  Best hour to sell         : {best_hour:02d}:00

CUSTOMER BEHAVIOUR
  Known customers           : {len(known['customer_id'].unique()):,}
  Guest transactions        : {df['is_guest'].sum():,} ({df['is_guest'].mean()*100:.1f}%)
  Avg orders per customer   : {freq.mean():.1f}
  Max orders by 1 customer  : {freq.max()}
  Customers with 1 order    : {(freq == 1).sum():,} ({(freq==1).mean()*100:.1f}%)
  Customers with 5+ orders  : {(freq >= 5).sum():,} ({(freq>=5).mean()*100:.1f}%)

MONTHLY REVENUE (TOP 5 MONTHS)
"""
    monthly = (df.groupby(["year","month"])["revenue"]
               .sum().sort_values(ascending=False).head(5))
    for (year, month), rev in monthly.items():
        report += f"  {year}-{month:02d}  →  £{rev:,.0f}\n"

    report += "\nCHARTS SAVED TO outputs/ FOLDER\n"
    report += "  01_monthly_revenue.png\n"
    report += "  02_top_products.png\n"
    report += "  03_revenue_by_country.png\n"
    report += "  04_sales_by_day.png\n"
    report += "  05_sales_by_hour.png\n"
    report += "  06_purchase_frequency.png\n"
    report += "="*62 + "\n"

    path = os.path.join(OUTPUT_DIR, "eda_report.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(report)

    print(report)
    log(f"  Report saved → outputs/eda_report.txt")


# ── MAIN ──────────────────────────────────────────────────
def main():
    print("\n" + "="*55)
    print("  PHASE 3 — EDA & BUSINESS METRICS")
    print("="*55 + "\n")

    # Create outputs folder
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    log(f"Output folder ready → {OUTPUT_DIR}/")

    df = load_data()

    chart_monthly_revenue(df)
    chart_top_products(df)
    chart_revenue_by_country(df)
    chart_sales_by_day(df)
    chart_sales_by_hour(df)
    chart_purchase_frequency(df)
    save_text_report(df)

    log("Phase 3 complete! Open the outputs/ folder to see your charts.")
    log("Next → run 04_segmentation.py")


if __name__ == "__main__":
    main()