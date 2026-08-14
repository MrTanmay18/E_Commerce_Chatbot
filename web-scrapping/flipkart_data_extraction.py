"""
Flipkart product data extraction.

Human-supervised scraper (browser stays visible) that:
  1. Collects product links for a search query across N pages.
  2. Scrapes details for each product.
  3. Compares new data against the current "live" CSV and writes a
     change report for human review.

This script never touches SQLite directly. Run csv_to_sqlite.py
afterwards to review the change report and (on approval) commit the
new data to the database.
"""

import re
import time
import pandas as pd

from pathlib import Path
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).parent

STAGING_DIR = BASE_DIR / "staging"
STAGING_DIR.mkdir(exist_ok=True)

SEARCH_QUERY = "sports shoes for men"

FLIPKART_URL = "https://www.flipkart.com/"

NUMBER_OF_PAGES = 25

# For testing: set to a small number. Set to None to scrape everything.
MAX_PRODUCTS = 10

# Staging output (new run)
NEW_LINKS_FILE = STAGING_DIR / "flipkart_product_links_new.csv"
NEW_DATA_FILE = STAGING_DIR / "flipkart_product_data_new.csv"

# "Live" data from the previous approved run
CURRENT_DATA_FILE = BASE_DIR / "flipkart_product_data.csv"

# Diff report for human review
CHANGES_FILE = STAGING_DIR / "product_changes.csv"


# ============================================================
# SELENIUM DRIVER
# ============================================================

def create_driver():
    options = webdriver.ChromeOptions()

    # Human-supervised scraping — keep the browser visible.
    # Do NOT switch to headless mode.

    driver = webdriver.Chrome(options=options)
    driver.maximize_window()

    return driver


# ============================================================
# STEP 1 — COLLECT PRODUCT LINKS
# ============================================================

def collect_product_links(driver):
    print("\n========================================")
    print("STEP 1: COLLECTING PRODUCT LINKS")
    print("========================================")

    driver.get(FLIPKART_URL)

    print("Waiting for search input...")
    search_input = WebDriverWait(driver, 120).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '[autocomplete="off"]'))
    )

    print("Typing search query...")
    search_input.send_keys(SEARCH_QUERY)
    search_input.send_keys(Keys.RETURN)

    print("Waiting for search results...")
    WebDriverWait(driver, 120).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '[target="_blank"]'))
    )

    # --------------------------------------------------------
    # Build pagination links from the first page link found
    # --------------------------------------------------------

    first_page = driver.find_elements(By.CSS_SELECTOR, "nav a")[0]
    first_page_link = first_page.get_attribute("href")

    pagination_links = [first_page_link]
    for page_number in range(2, NUMBER_OF_PAGES + 1):
        pagination_links.append(first_page_link[:-1] + str(page_number))

    print(f"Pagination pages collected: {len(pagination_links)}")

    # --------------------------------------------------------
    # Visit each page and collect product links
    # --------------------------------------------------------

    all_product_links = []

    for index, page_link in enumerate(pagination_links, start=1):
        try:
            driver.get(page_link)

            WebDriverWait(driver, 120).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            WebDriverWait(driver, 120).until(
                EC.presence_of_element_located((By.CLASS_NAME, "rPDeLR"))
            )

            products = driver.find_elements(By.CLASS_NAME, "rPDeLR")
            links = [product.get_attribute("href") for product in products]
            all_product_links.extend(links)

            print(f"Page {index}/{NUMBER_OF_PAGES} completed | Products: {len(links)}")
            time.sleep(1)

        except Exception as e:
            print(f"Failed page {index}: {e}")

    # Clean up: drop None values and duplicates, preserving order
    all_product_links = [link for link in all_product_links if link]
    all_product_links = list(dict.fromkeys(all_product_links))

    if MAX_PRODUCTS is not None:
        all_product_links = all_product_links[:MAX_PRODUCTS]

    df_links = pd.DataFrame(all_product_links, columns=["product_link"])
    df_links.to_csv(NEW_LINKS_FILE, index=False)

    print(f"\nTotal unique product links: {len(df_links)}")
    print(f"Saved to: {NEW_LINKS_FILE}")

    return all_product_links


# ============================================================
# STEP 2 — SCRAPE PRODUCT DETAILS
# ============================================================

def scrape_product_details(driver, product_links):
    print("\n========================================")
    print("STEP 2: SCRAPING PRODUCT DETAILS")
    print("========================================")

    product_details = []
    unavailable_products = []
    failed_products = []

    for index, product_url in enumerate(product_links, start=1):
        print(f"\nProcessing {index}/{len(product_links)}")

        try:
            driver.get(product_url)

            WebDriverWait(driver, 120).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )

            # ------------------------------------------------
            # Availability check
            # ------------------------------------------------
            try:
                status = driver.find_element(By.CLASS_NAME, "Z8JjpR").text
                if status in ["Currently Unavailable", "Sold Out"]:
                    unavailable_products.append(product_url)
                    print("Product unavailable")
                    continue
            except Exception:
                pass

            # ------------------------------------------------
            # Brand / Title
            # ------------------------------------------------
            brand = driver.find_element(By.CLASS_NAME, "mEh187").text

            title = driver.find_element(By.CLASS_NAME, "VU-ZEz").text
            title = re.sub(r"\s*\([^)]*\)", "", title).strip()

            # ------------------------------------------------
            # Price
            # ------------------------------------------------
            price_text = driver.find_element(By.CLASS_NAME, "Nx9bqj").text
            price = int("".join(re.findall(r"\d+", price_text)))

            # ------------------------------------------------
            # Discount
            # ------------------------------------------------
            try:
                discount_text = driver.find_element(By.CLASS_NAME, "UkUFwK").text
                discount = int("".join(re.findall(r"\d+", discount_text))) / 100
            except Exception:
                discount = None

            # ------------------------------------------------
            # Rating + total ratings
            # ------------------------------------------------
            try:
                review_status = driver.find_element(By.CLASS_NAME, "E3XX7J").text

                if review_status == "Be the first to Review this product":
                    avg_rating = None
                    total_ratings = None
                else:
                    avg_rating = float(
                        driver.find_element(By.CLASS_NAME, "XQDdHH").text
                    )
                    total_ratings_text = (
                        driver.find_element(By.CLASS_NAME, "Wphh3N").text.split(" ")[0]
                    )
                    total_ratings = int(total_ratings_text.replace(",", ""))
            except Exception:
                avg_rating = None
                total_ratings = None

            product_details.append(
                [product_url, title, brand, price, discount, avg_rating, total_ratings]
            )

            print(f"SUCCESS | {brand} | {title} | \u20b9{price}")
            time.sleep(1)

        except Exception as e:
            print(f"FAILED: {product_url}")
            print(f"Reason: {e}")
            failed_products.append(product_url)

    # ========================================================
    # Save results
    # ========================================================

    columns = [
        "product_link", "title", "brand", "price",
        "discount", "avg_rating", "total_ratings",
    ]

    df = pd.DataFrame(product_details, columns=columns)
    df = df.drop_duplicates(subset=["product_link"])
    df.to_csv(NEW_DATA_FILE, index=False)

    pd.DataFrame(unavailable_products, columns=["product_link"]).to_csv(
        STAGING_DIR / "unavailable_products_new.csv", index=False
    )
    pd.DataFrame(failed_products, columns=["product_link"]).to_csv(
        STAGING_DIR / "failed_products_new.csv", index=False
    )

    print("\n========================================")
    print("SCRAPING COMPLETED")
    print("========================================")
    print(f"Successful products : {len(df)}")
    print(f"Unavailable products: {len(unavailable_products)}")
    print(f"Failed products     : {len(failed_products)}")
    print(f"New CSV: {NEW_DATA_FILE}")

    return df


# ============================================================
# STEP 3 — COMPARE OLD VS NEW
# ============================================================

def compare_data(new_df):
    print("\n========================================")
    print("STEP 3: COMPARING DATA")
    print("========================================")

    if not CURRENT_DATA_FILE.exists():
        print("No existing product CSV found.")
        new_df.to_csv(CHANGES_FILE, index=False)
        return

    old_df = pd.read_csv(CURRENT_DATA_FILE)

    columns = [
        "product_link", "title", "brand", "price",
        "discount", "avg_rating", "total_ratings",
    ]
    old_df = old_df[columns]
    new_df = new_df[columns]

    merged = old_df.merge(
        new_df, on="product_link", how="outer",
        suffixes=("_old", "_new"), indicator=True,
    )

    new_products = merged[merged["_merge"] == "right_only"].copy()
    removed_products = merged[merged["_merge"] == "left_only"].copy()
    existing = merged[merged["_merge"] == "both"].copy()

    change_rows = []
    fields_to_compare = ["title", "brand", "price", "discount", "avg_rating", "total_ratings"]

    for _, row in existing.iterrows():
        changes = []
        for field in fields_to_compare:
            old_value = row[f"{field}_old"]
            new_value = row[f"{field}_new"]

            if pd.isna(old_value) and pd.isna(new_value):
                continue
            if old_value != new_value:
                changes.append(f"{field}: {old_value} -> {new_value}")

        if changes:
            change_rows.append({
                "product_link": row["product_link"],
                "change_type": "UPDATED",
                "changes": " | ".join(changes),
            })

    for _, row in new_products.iterrows():
        change_rows.append({
            "product_link": row["product_link"],
            "change_type": "NEW",
            "changes": "New product",
        })

    for _, row in removed_products.iterrows():
        change_rows.append({
            "product_link": row["product_link"],
            "change_type": "REMOVED",
            "changes": "Product no longer found",
        })

    changes_df = pd.DataFrame(change_rows)
    changes_df.to_csv(CHANGES_FILE, index=False)

    print(f"New products     : {len(new_products)}")
    print(f"Removed products : {len(removed_products)}")
    print(f"Updated products : {len(change_rows)}")
    print(f"\nChange report:\n{CHANGES_FILE}")


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    start_time = datetime.now()

    print("\n========================================")
    print("FLIPKART DATA REFRESH STARTED")
    print(f"Started: {start_time}")
    print(f"Search: {SEARCH_QUERY}")
    print("========================================")

    driver = create_driver()

    try:
        product_links = collect_product_links(driver)
        new_df = scrape_product_details(driver, product_links)
        compare_data(new_df)
    finally:
        driver.quit()

    print("\n========================================")
    print("SCRAPING FINISHED")
    print(f"Finished: {datetime.now()}")
    print("Human approval required before updating SQLite.")
    print("Next step: run csv_to_sqlite.py")
    print("========================================")