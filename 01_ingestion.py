"""
=============================================================
PHASE 1 — DATA INGESTION
Consumer Spending Intelligence Platform
=============================================================
What this script does:
  1. Reads both sheets from online_retail_II.xlsx
  2. Combines them into one DataFrame
  3. Renames columns to clean snake_case
  4. Validates that all expected columns are present
  5. Saves raw data into SQLite as 'raw_transactions' table

Run: python 01_ingestion.py
=============================================================
"""

import pandas as pd
import sqlite3
import os
import sys
from datetime import datetime

# ── CONFIG ────────────────────────────────────────────────
DATA_FILE  = "data/online_retail_II.xlsx"
DB_PATH    = "data/retail.db"
SHEETS     = ["Year 2009-2010", "Year 2010-2011"]

REQUIRED_COLUMNS = [
    "Invoice", "StockCode", "Description",
    "Quantity", "InvoiceDate", "Price",
    "Customer ID", "Country"
]

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def read_excel(filepath):
    log(f"Reading file: {filepath}")
    if not os.path.exists(filepath):
        log(f"ERROR: File not found → {filepath}")
        sys.exit(1)
    frames = []
    for sheet in SHEETS:
        log(f"  Loading sheet: '{sheet}'...")
        df = pd.read_excel(filepath, sheet_name=sheet, engine="openpyxl")
        df["_source_sheet"] = sheet
        log(f"  → {len(df):,} rows loaded")
        frames.append(df)
    combined = pd.concat(frames, ignore_index=True)
    log(f"Combined total: {len(combined):,} rows")
    return combined

def validate_schema(df):
    log("Validating schema...")
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        log(f"ERROR: Missing columns → {missing}")
        sys.exit(1)
    log(f"  All {len(REQUIRED_COLUMNS)} required columns found ✓")
    return df

def standardise_columns(df):
    log("Standardising column names...")
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
    df = df.rename(columns={"invoicedate": "invoice_date"})
    log(f"  Columns: {list(df.columns)}")
    return df

def parse_types(df):
    log("Parsing data types...")
    df["invoice_date"] = pd.to_datetime(df["invoice_date"], errors="coerce")
    df["quantity"]     = pd.to_numeric(df["quantity"],     errors="coerce")
    df["price"]        = pd.to_numeric(df["price"],        errors="coerce")
    log(f"  invoice_date → datetime ✓")
    log(f"  quantity, price → numeric ✓")
    return df

def save_to_sql(df, db_path):
    log(f"Saving raw data to SQLite → {db_path}")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    df.to_sql("raw_transactions", conn, if_exists="replace", index=False)
    count = conn.execute("SELECT COUNT(*) FROM raw_transactions").fetchone()[0]
    conn.close()
    log(f"  raw_transactions saved: {count:,} rows ✓")

def print_summary(df):
    print("\n" + "="*50)
    print("  INGESTION SUMMARY")
    print("="*50)
    print(f"  Total rows ingested : {len(df):,}")
    print(f"  Total columns       : {df.shape[1]}")
    print(f"  Date range          : {df['invoice_date'].min().date()} → {df['invoice_date'].max().date()}")
    print(f"  Null Customer IDs   : {df['customer_id'].isnull().sum():,} ({df['customer_id'].isnull().mean()*100:.1f}%)")
    print(f"  Null Descriptions   : {df['description'].isnull().sum():,}")
    print(f"  Source file         : {DATA_FILE}")
    print(f"  Saved to DB         : {DB_PATH} → table: raw_transactions")
    print("="*50 + "\n")

def main():
    print("\n" + "="*50)
    print("  PHASE 1 — DATA INGESTION")
    print("="*50 + "\n")
    df = read_excel(DATA_FILE)
    df = validate_schema(df)
    df = standardise_columns(df)
    df = parse_types(df)
    save_to_sql(df, DB_PATH)
    print_summary(df)
    log("Phase 1 complete → run 02_cleaning.py next")

if __name__ == "__main__":
    main()