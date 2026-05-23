"""
=============================================================
PHASE 4 — CUSTOMER SEGMENTATION
Consumer Spending Intelligence Platform
=============================================================
What this script does:
  1. Computes RFM scores for every known customer
     R = Recency   (how recently they bought)
     F = Frequency (how many times they bought)
     M = Monetary  (how much they spent total)
  2. Scores each customer 1-5 on each dimension
  3. Labels customers into 6 segments:
     Champion / Loyal / New Customer / Potential / At Risk / Lost
  4. Saves RFM table back to SQL
  5. Generates 4 charts + segment report

Run: python 04_segmentation.py
=============================================================
"""

import pandas as pd
import sqlite3
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from datetime import datetime

# ── CONFIG ────────────────────────────────────────────────
DB_PATH    = "data/retail.db"
OUTPUT_DIR = "outputs"

# Chart style
BG_COLOR   = "#0f1117"
CARD_COLOR = "#1a1d27"
TEXT_COLOR = "#e0e0e0"
MUTED      = "#888888"

# Segment colors
SEG_COLORS = {
    "Champion"    : "#4f8ef7",
    "Loyal"       : "#36c98e",
    "New Customer": "#f7c948",
    "Potential"   : "#a78bfa",
    "At Risk"     : "#f97316",
    "Lost"        : "#ef4444",
}

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
    ax.set_facecolor(CARD_COLOR)
    ax.set_title(title, color=TEXT_COLOR, fontsize=13,
                 fontweight="bold", pad=12)
    ax.tick_params(colors=MUTED, labelsize=9)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#333344")
    ax.spines["bottom"].set_color("#333344")
    ax.grid(axis="y", color="#333344", linewidth=0.5, linestyle="--")


# ── STEP 1: LOAD DATA ─────────────────────────────────────
def load_data():
    log(f"Loading clean_transactions from {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM clean_transactions", conn)
    conn.close()
    df["invoice_date"] = pd.to_datetime(df["invoice_date"])
    log(f"  Loaded {len(df):,} rows ✓")
    return df


# ── STEP 2: COMPUTE RFM ───────────────────────────────────
def compute_rfm(df):
    log("Computing RFM metrics...")

    # Only known customers (exclude guests)
    known = df[df["customer_id"] != "GUEST"]

    # Snapshot = 1 day after last transaction
    snapshot_date = df["invoice_date"].max() + pd.Timedelta(days=1)
    log(f"  Snapshot date: {snapshot_date.date()}")

    rfm = known.groupby("customer_id").agg(
        recency   = ("invoice_date", lambda x: (snapshot_date - x.max()).days),
        frequency = ("invoice",      "nunique"),
        monetary  = ("revenue",      "sum")
    ).reset_index()

    rfm["monetary"] = rfm["monetary"].round(2)

    log(f"  RFM computed for {len(rfm):,} customers")
    log(f"  Avg Recency   : {rfm['recency'].mean():.0f} days")
    log(f"  Avg Frequency : {rfm['frequency'].mean():.1f} orders")
    log(f"  Avg Monetary  : £{rfm['monetary'].mean():,.2f}")

    return rfm


# ── STEP 3: SCORE CUSTOMERS 1-5 ───────────────────────────
def score_rfm(rfm):
    log("Scoring customers (1-5 per dimension)...")

    # Recency: LOWER days = BETTER = score 5
    rfm["r_score"] = pd.qcut(
        rfm["recency"], 5, labels=[5, 4, 3, 2, 1]
    ).astype(int)

    # Frequency: HIGHER orders = BETTER = score 5
    rfm["f_score"] = pd.qcut(
        rfm["frequency"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]
    ).astype(int)

    # Monetary: HIGHER spend = BETTER = score 5
    rfm["m_score"] = pd.qcut(
        rfm["monetary"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]
    ).astype(int)

    # Total RFM score (3 to 15)
    rfm["rfm_score"] = rfm["r_score"] + rfm["f_score"] + rfm["m_score"]

    log(f"  Scores range: {rfm['rfm_score'].min()} to {rfm['rfm_score'].max()}")
    return rfm


# ── STEP 4: ASSIGN SEGMENTS ───────────────────────────────
def assign_segments(rfm):
    log("Assigning customer segments...")

    def get_segment(row):
        r = row["r_score"]
        f = row["f_score"]

        if   r >= 4 and f >= 4: return "Champion"
        elif r >= 3 and f >= 3: return "Loyal"
        elif r >= 4 and f <= 2: return "New Customer"
        elif r <= 2 and f >= 3: return "At Risk"
        elif r <= 2 and f <= 2: return "Lost"
        else:                   return "Potential"

    rfm["segment"] = rfm.apply(get_segment, axis=1)

    # Print segment breakdown
    print()
    print("  SEGMENT BREAKDOWN:")
    print("  " + "-"*50)
    seg_summary = rfm.groupby("segment").agg(
        customers = ("customer_id", "count"),
        avg_spend = ("monetary",    "mean"),
        avg_days  = ("recency",     "mean"),
        revenue   = ("monetary",    "sum")
    ).sort_values("revenue", ascending=False)

    for seg, row in seg_summary.iterrows():
        print(f"  {seg:<15} {row['customers']:>5} customers  "
              f"£{row['avg_spend']:>8,.0f} avg spend  "
              f"{row['avg_days']:>4.0f} days since last buy")
    print()

    return rfm


# ── CHART 1: SEGMENT DISTRIBUTION (DONUT) ────────────────
def chart_segment_donut(rfm):
    log("Generating Chart 7 — Segment Distribution...")

    counts = rfm["segment"].value_counts()
    colors = [SEG_COLORS[s] for s in counts.index]

    fig, ax = plt.subplots(figsize=(8, 7), facecolor=BG_COLOR)
    ax.set_facecolor(BG_COLOR)

    wedges, texts, autotexts = ax.pie(
        counts.values,
        labels=counts.index,
        colors=colors,
        autopct="%1.1f%%",
        pctdistance=0.75,
        startangle=140,
        wedgeprops=dict(width=0.5, edgecolor=BG_COLOR, linewidth=2)
    )

    for text in texts:
        text.set_color(TEXT_COLOR)
        text.set_fontsize(11)
    for autotext in autotexts:
        autotext.set_color("white")
        autotext.set_fontsize(9)
        autotext.set_fontweight("bold")

    ax.set_title("Customer Segments Distribution",
                 color=TEXT_COLOR, fontsize=14, fontweight="bold", pad=20)

    # Center text
    ax.text(0, 0, f"{len(rfm):,}\nCustomers",
            ha="center", va="center",
            color=TEXT_COLOR, fontsize=13, fontweight="bold")

    plt.tight_layout()
    save_fig("07_segment_donut.png")


# ── CHART 2: REVENUE BY SEGMENT ───────────────────────────
def chart_segment_revenue(rfm):
    log("Generating Chart 8 — Revenue by Segment...")

    seg_rev = (rfm.groupby("segment")["monetary"]
               .sum()
               .sort_values(ascending=True))
    colors = [SEG_COLORS[s] for s in seg_rev.index]

    fig, ax = plt.subplots(figsize=(9, 6), facecolor=BG_COLOR)
    setup_ax(ax, "Total Revenue by Customer Segment")

    bars = ax.barh(range(len(seg_rev)), seg_rev.values,
                   color=colors, alpha=0.9, height=0.6)

    for bar, val in zip(bars, seg_rev.values):
        ax.text(val + 5000, bar.get_y() + bar.get_height()/2,
                f"£{val/1000:.0f}K",
                va="center", color=TEXT_COLOR, fontsize=10)

    ax.set_yticks(range(len(seg_rev)))
    ax.set_yticklabels(seg_rev.index, color=TEXT_COLOR, fontsize=10)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(
        lambda v, _: f"£{v/1000:.0f}K"))
    ax.set_xlabel("Total Revenue", color=MUTED)

    plt.tight_layout()
    save_fig("08_segment_revenue.png")


# ── CHART 3: RFM SCORE DISTRIBUTION ──────────────────────
def chart_rfm_scores(rfm):
    log("Generating Chart 9 — RFM Score Distribution...")

    fig, axes = plt.subplots(1, 3, figsize=(14, 5), facecolor=BG_COLOR)
    fig.suptitle("RFM Score Distributions",
                 color=TEXT_COLOR, fontsize=14, fontweight="bold", y=1.01)

    metrics = [
        ("r_score", "Recency Score",   "#4f8ef7"),
        ("f_score", "Frequency Score", "#36c98e"),
        ("m_score", "Monetary Score",  "#f7c948"),
    ]

    for ax, (col, title, color) in zip(axes, metrics):
        counts = rfm[col].value_counts().sort_index()
        ax.set_facecolor(CARD_COLOR)
        bars = ax.bar(counts.index, counts.values,
                      color=color, alpha=0.85, width=0.6)
        for bar in bars:
            ax.text(bar.get_x() + bar.get_width()/2,
                    bar.get_height() + 10,
                    str(int(bar.get_height())),
                    ha="center", color=TEXT_COLOR, fontsize=8)
        ax.set_title(title, color=TEXT_COLOR, fontsize=11, fontweight="bold")
        ax.set_xticks([1, 2, 3, 4, 5])
        ax.tick_params(colors=MUTED)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color("#333344")
        ax.spines["bottom"].set_color("#333344")
        ax.set_xlabel("Score (1=Low, 5=High)", color=MUTED, fontsize=9)
        ax.set_ylabel("Customers", color=MUTED, fontsize=9)
        ax.grid(axis="y", color="#333344", linewidth=0.5)

    plt.tight_layout()
    save_fig("09_rfm_scores.png")


# ── CHART 4: AVG SPEND PER SEGMENT ───────────────────────
def chart_avg_spend(rfm):
    log("Generating Chart 10 — Avg Spend per Segment...")

    seg_avg = (rfm.groupby("segment")["monetary"]
               .mean()
               .sort_values(ascending=False))
    colors = [SEG_COLORS[s] for s in seg_avg.index]

    fig, ax = plt.subplots(figsize=(9, 5), facecolor=BG_COLOR)
    setup_ax(ax, "Average Customer Spend by Segment")

    bars = ax.bar(range(len(seg_avg)), seg_avg.values,
                  color=colors, alpha=0.9, width=0.6)

    for bar, val in zip(bars, seg_avg.values):
        ax.text(bar.get_x() + bar.get_width()/2,
                bar.get_height() + 50,
                f"£{val:,.0f}",
                ha="center", color=TEXT_COLOR, fontsize=9)

    ax.set_xticks(range(len(seg_avg)))
    ax.set_xticklabels(seg_avg.index, color=TEXT_COLOR, fontsize=10)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(
        lambda v, _: f"£{v:,.0f}"))
    ax.set_ylabel("Average Spend (£)", color=MUTED)

    plt.tight_layout()
    save_fig("10_avg_spend_per_segment.png")


# ── SAVE RFM TO SQL ───────────────────────────────────────
def save_rfm_to_sql(rfm):
    log("Saving RFM table to SQL...")
    conn = sqlite3.connect(DB_PATH)
    rfm.to_sql("customer_segments", conn,
               if_exists="replace", index=False)
    count = conn.execute(
        "SELECT COUNT(*) FROM customer_segments"
    ).fetchone()[0]
    conn.close()
    log(f"  customer_segments saved: {count:,} rows ✓")


# ── SAVE SEGMENT REPORT ───────────────────────────────────
def save_segment_report(rfm):
    log("Saving segment report...")

    seg_summary = rfm.groupby("segment").agg(
        customers    = ("customer_id", "count"),
        total_revenue= ("monetary",    "sum"),
        avg_spend    = ("monetary",    "mean"),
        avg_orders   = ("frequency",   "mean"),
        avg_recency  = ("recency",     "mean"),
    ).sort_values("total_revenue", ascending=False)

    report = f"""
==============================================================
  SEGMENTATION REPORT — CONSUMER SPENDING INTELLIGENCE
  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
==============================================================

WHAT IS RFM SEGMENTATION?
  R = Recency   → How recently did the customer buy?
  F = Frequency → How many times did they buy?
  M = Monetary  → How much did they spend in total?

  Each customer is scored 1-5 on each dimension.
  Total score ranges from 3 (worst) to 15 (best).

SEGMENT DEFINITIONS
  Champion     → Bought recently, buys often, spends most
  Loyal        → Buys regularly, responds to promotions
  New Customer → Bought recently but not often yet
  Potential    → Average scores, room to grow
  At Risk      → Used to buy often but not recently
  Lost         → Haven't bought in a long time

==============================================================
SEGMENT RESULTS
==============================================================

"""
    for seg, row in seg_summary.iterrows():
        pct = row["customers"] / len(rfm) * 100
        report += f"  {seg}\n"
        report += f"    Customers     : {row['customers']:,} ({pct:.1f}%)\n"
        report += f"    Total Revenue : £{row['total_revenue']:,.2f}\n"
        report += f"    Avg Spend     : £{row['avg_spend']:,.2f}\n"
        report += f"    Avg Orders    : {row['avg_orders']:.1f}\n"
        report += f"    Avg Days Ago  : {row['avg_recency']:.0f} days\n\n"

    report += "=" * 62 + "\n"
    report += "BUSINESS ACTIONS\n"
    report += "=" * 62 + "\n"
    report += """
  Champion     -> Reward them! Loyalty program, early access
  Loyal        -> Upsell higher value products
  New Customer -> Onboarding emails, first purchase discount
  Potential    -> Send targeted promotions
  At Risk      -> Win-back campaign, special discount
  Lost         -> Last attempt re-engagement email
"""

    path = os.path.join(OUTPUT_DIR, "segmentation_report.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(report)

    print(report)
    log("  Report saved -> outputs/segmentation_report.txt")


# ── MAIN ──────────────────────────────────────────────────
def main():
    print("\n" + "=" * 55)
    print("  PHASE 4 -- CUSTOMER SEGMENTATION")
    print("=" * 55 + "\n")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    df  = load_data()
    rfm = compute_rfm(df)
    rfm = score_rfm(rfm)
    rfm = assign_segments(rfm)

    chart_segment_donut(rfm)
    chart_segment_revenue(rfm)
    chart_rfm_scores(rfm)
    chart_avg_spend(rfm)

    save_rfm_to_sql(rfm)
    save_segment_report(rfm)

    log("Phase 4 complete! Check outputs/ for charts.")
    log("Next -> run 05_features.py")


if __name__ == "__main__":
    main()