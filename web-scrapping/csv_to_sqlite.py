"""
Commit staged Flipkart data into SQLite.

Run this AFTER flipkart_data_extraction.py.

Flow:
  1. Show the human the diff report (product_changes.csv).
  2. Ask for explicit approval before touching anything.
  3. Archive the current CSV + db.sqlite (timestamped) as a safety net.
  4. Replace the `product` table in db.sqlite with the new data.
  5. Sync db.sqlite into app/db.sqlite so the chatbot sees fresh data.
  6. Promote staging/*_new.csv files to the "live" CSVs so the next
     scrape run diffs against the right baseline.
"""

import shutil
import sqlite3
from pathlib import Path
from datetime import datetime

import pandas as pd

# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).parent
STAGING_DIR = BASE_DIR / "staging"

# Files produced by flipkart_data_extraction.py
NEW_DATA_FILE = STAGING_DIR / "flipkart_product_data_new.csv"
NEW_LINKS_FILE = STAGING_DIR / "flipkart_product_links_new.csv"
UNAVAILABLE_NEW_FILE = STAGING_DIR / "unavailable_products_new.csv"
FAILED_NEW_FILE = STAGING_DIR / "failed_products_new.csv"
CHANGES_FILE = STAGING_DIR / "product_changes.csv"

# "Live" files the rest of the project reads from
CURRENT_DATA_FILE = BASE_DIR / "flipkart_product_data.csv"
CURRENT_LINKS_FILE = BASE_DIR / "flipkart_product_links.csv"
UNAVAILABLE_FILE = BASE_DIR / "unavailable_products.csv"
FAILED_FILE = BASE_DIR / "failed_products.csv"

# SQLite database written by this pipeline
DB_PATH = BASE_DIR / "db.sqlite"

# SQLite database read by the chatbot (app/db.sqlite).
# Set to None if you don't want it synced automatically.
APP_DB_PATH = BASE_DIR.parent / "app" / "db.sqlite"

# Where the previous CSV/db gets archived before being overwritten
ARCHIVE_DIR = BASE_DIR / "archive"


# ============================================================
# STEP 1 — SHOW THE HUMAN WHAT CHANGED
# ============================================================

def show_change_summary():
    if not CHANGES_FILE.exists():
        print("No change report found. Run flipkart_data_extraction.py first.")
        return None

    changes_df = pd.read_csv(CHANGES_FILE)

    if changes_df.empty:
        print("No changes detected between the old and new data.")
        return changes_df

    print("\n========================================")
    print("PRODUCT CHANGE SUMMARY")
    print("========================================")

    counts = changes_df["change_type"].value_counts()
    for change_type, count in counts.items():
        print(f"{change_type:<10}: {count}")

    print("\nSample of changes:")
    print(changes_df.head(15).to_string(index=False))
    print(f"\nFull report: {CHANGES_FILE}")

    return changes_df


# ============================================================
# STEP 2 — HUMAN APPROVAL GATE
# ============================================================

def get_human_approval():
    print("\n========================================")
    answer = input("Apply these changes to the database? (yes/no): ").strip().lower()
    return answer in ("yes", "y")


# ============================================================
# STEP 3 — ARCHIVE CURRENT STATE BEFORE OVERWRITING
# ============================================================

def archive_current_state():
    ARCHIVE_DIR.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = ARCHIVE_DIR / timestamp
    run_dir.mkdir(exist_ok=True)

    for file in [CURRENT_DATA_FILE, CURRENT_LINKS_FILE, DB_PATH]:
        if file.exists():
            shutil.copy2(file, run_dir / file.name)

    print(f"Archived previous data/db to: {run_dir}")


# ============================================================
# STEP 4 — WRITE NEW DATA INTO SQLITE
# ============================================================

def update_database(df):
    with sqlite3.connect(DB_PATH) as conn:
        # Full replace, not append: prices/discounts/ratings change on
        # every run and appending would just accumulate duplicate rows.
        df.to_sql("product", conn, if_exists="replace", index=False)

    print(f"SQLite database updated: {DB_PATH}")

    if APP_DB_PATH is not None:
        APP_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(DB_PATH, APP_DB_PATH)
        print(f"Synced database to chatbot app: {APP_DB_PATH}")


# ============================================================
# STEP 5 — PROMOTE STAGING FILES TO "LIVE" FILES
# ============================================================

def promote_staging_files():
    file_pairs = [
        (NEW_DATA_FILE, CURRENT_DATA_FILE),
        (NEW_LINKS_FILE, CURRENT_LINKS_FILE),
        (UNAVAILABLE_NEW_FILE, UNAVAILABLE_FILE),
        (FAILED_NEW_FILE, FAILED_FILE),
    ]

    for src, dst in file_pairs:
        if src.exists():
            shutil.copy2(src, dst)
            print(f"Updated: {dst.name}")


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    print("\n========================================")
    print("CSV -> SQLITE SYNC (HUMAN APPROVAL REQUIRED)")
    print("========================================")

    if not NEW_DATA_FILE.exists():
        print(
            f"No new data found at {NEW_DATA_FILE}. "
            "Run flipkart_data_extraction.py first."
        )
        raise SystemExit(1)

    show_change_summary()

    if not get_human_approval():
        print("Aborted. No changes were applied.")
        raise SystemExit(0)

    archive_current_state()

    new_df = pd.read_csv(NEW_DATA_FILE)
    update_database(new_df)

    promote_staging_files()

    print("\n========================================")
    print("SYNC COMPLETED SUCCESSFULLY")
    print("========================================")