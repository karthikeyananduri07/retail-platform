"""
=============================================================
PHASE 2 — DATA CLEANING
Consumer Spending Intelligence Platform
=============================================================
"""

import pandas as pd
import sqlite3
import os
from datetime import datetime

DB_PATH = "data/retail.db"
SPECIAL_CODES = ["POST", "D", "M", "BANK CHARGES", "AMAZONFEE", "CRUK", "C2"]

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def report_removed(label, mask, total):
    n = mask.sum()
    pct = n / total * 100
    log(f"  {label:<35} → removing {n:>7,} rows ({pct:.2f}%)")
    return mask

def load_raw(db_path):
    log(f"Loading raw_transactions from {db_path}...")
    conn = sqlite3.connect(db_path)
    df = pd.read_sql("SELECT * FROM raw_transactions", conn)
    conn.close()
    df["invoice_date"] = pd.to_datetime(df["invoice_date"])
    log(f"  Loaded: {len(df):,} rows, {df.shape[1]} columns")
    return df

def remove_duplicates(df):
    log("Removing duplicate rows...")
    before = len(df)
    df = df.drop_duplicates()
    log(f"  Removed {before - len(df):,} exact duplicate rows")
    return df

def remove_bad_rows(df):
    log("Removing invalid / unwanted rows...")
    total = len(df)
    cancellations = report_removed("Cancellations (Invoice starts 'C')",
                                   df["invoice"].astype(str).str.startswith("C"), total)
    negative_qty  = report_removed("Non-positive Quantity",
                                   df["quantity"] <= 0, total)
    zero_price    = report_removed("Zero or negative Price",
                                   df["price"] <= 0, total)
    special_codes = report_removed("Special non-product StockCodes",
                                   df["stockcode"].astype(str).str.upper().isin(SPECIAL_CODES), total)
    bad_mask = cancellations | negative_qty | zero_price | special_codes
    df_clean = df[~bad_mask].copy()
    log(f"  Total removed: {bad_mask.sum():,} rows")
    log(f"  Rows remaining: {len(df_clean):,}")
    return df_clean

def fix_types(df):
    log("Fixing data types...")
    df["customer_id"] = (df["customer_id"].fillna(-1)
                         .astype(int).astype(str).replace("-1", "GUEST"))
    df["stockcode"]   = df["stockcode"].astype(str).str.strip().str.upper()
    df["invoice"]     = df["invoice"].astype(str).str.strip()
    df["description"] = (df["description"].fillna("UNKNOWN")
                         .astype(str).str.strip().str.upper())
    df["country"]     = df["country"].astype(str).str.strip()
    log("  All types fixed ✓")
    return df

def engineer_columns(df):
    log("Engineering new columns...")
    df["revenue"]      = (df["quantity"] * df["price"]).round(2)
    df["year"]         = df["invoice_date"].dt.year
    df["month"]        = df["invoice_date"].dt.month
    df["month_name"]   = df["invoice_date"].dt.strftime("%b")
    df["day_of_week"]  = df["invoice_date"].dt.day_name()
    df["hour"]         = df["invoice_date"].dt.hour
    df["is_weekend"]   = df["invoice_date"].dt.dayofweek >= 5
    df["is_guest"]     = df["customer_id"] == "GUEST"
    log("  revenue, year, month, day_of_week, hour, is_weekend, is_guest ✓")
    return df

def save_clean(df, db_path):
    log(f"Saving clean_transactions to {db_path}...")
    conn = sqlite3.connect(db_path)
    df.to_sql("clean_transactions", conn, if_exists="replace", index=False)
    count = conn.execute("SELECT COUNT(*) FROM clean_transactions").fetchone()[0]
    conn.close()
    log(f"  clean_transactions saved: {count:,} rows ✓")

def print_report(raw_df, clean_df):
    total_removed = len(raw_df) - len(clean_df)
    guests = clean_df["is_guest"].sum()
    print("\n" + "="*55)
    print("  CLEANING REPORT")
    print("="*55)
    print(f"  Raw rows              : {len(raw_df):>10,}")
    print(f"  Clean rows            : {len(clean_df):>10,}")
    print(f"  Total removed         : {total_removed:>10,}  ({total_removed/len(raw_df)*100:.1f}%)")
    print("-"*55)
    print(f"  Unique customers      : {clean_df['customer_id'].nunique():>10,}")
    print(f"  Guest rows (no ID)    : {guests:>10,}  ({guests/len(clean_df)*100:.1f}%)")
    print(f"  Unique invoices       : {clean_df['invoice'].nunique():>10,}")
    print(f"  Unique products       : {clean_df['stockcode'].nunique():>10,}")
    print(f"  Total revenue         : £{clean_df['revenue'].sum():>12,.2f}")
    print(f"  Date range            : {clean_df['invoice_date'].min().date()} → {clean_df['invoice_date'].max().date()}")
    print("="*55 + "\n")

def main():
    print("\n" + "="*55)
    print("  PHASE 2 — DATA CLEANING")
    print("="*55 + "\n")
    raw_df = load_raw(DB_PATH)
    df     = remove_duplicates(raw_df)
    df     = remove_bad_rows(df)
    df     = fix_types(df)
    df     = engineer_columns(df)
    save_clean(df, DB_PATH)
    print_report(raw_df, df)
    log("Phase 2 complete → run 03_eda.py next")

if __name__ == "__main__":
    main()