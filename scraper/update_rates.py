"""
Rate-refresh script — run manually or via the scheduled GitHub Action
(.github/workflows/update_rates.yml).

IMPORTANT (read this before you rely on it): there is no single clean feed of
Pakistani construction rates. This script is a STARTING TEMPLATE that
demonstrates the pattern (fetch -> extract a number with a regex -> write to
the national fallback row in data/material_rates.csv) using one illustrative
source. News sites change their HTML/URLs often, so treat the URL and
selector below as things you will need to re-verify and adjust periodically
-- that upkeep is expected, not a sign something is broken.

This template updates only the "_NationalFallback" rows (cement + steel).
The city-specific rows in data/material_rates.csv were seeded from a
one-off government CPI dataset and are not live-scraped; refreshing those
is a manual/periodic task described in the build guide, since that data
isn't published as a recurring feed.
"""

import re
import sys
from datetime import date

import pandas as pd
import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (educational project; contact: you@example.com)"}
DATA_PATH = "data/material_rates.csv"


def get_soup(url: str) -> BeautifulSoup:
    r = requests.get(url, headers=HEADERS, timeout=15)
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser")


def extract_price_per_bag(text: str):
    """Looks for patterns like 'Rs. 1,550 per bag' or 'Rs 1,550-1,610'."""
    match = re.search(r"(?:Rs\.?|PKR)\s?([\d,]{4,6})\s*(?:per\s*bag|/\s*bag)", text, re.IGNORECASE)
    if match:
        return float(match.group(1).replace(",", ""))
    return None


def extract_price_per_kg(text: str):
    """Looks for patterns like '232 per kg' or 'PKR 232/kg'."""
    match = re.search(r"(?:Rs\.?|PKR)?\s?(\d{3})\s*(?:per\s*kg|/\s*kg)", text, re.IGNORECASE)
    if match:
        return float(match.group(1))
    return None


def update_row(df: pd.DataFrame, city: str, material: str, new_price: float, source: str) -> pd.DataFrame:
    mask = (df["city"] == city) & (df["material"] == material)
    if not mask.any():
        print(f"WARNING: no existing row for {city}/{material} - skipping (add it manually first)")
        return df
    df.loc[mask, "unit_price_pkr"] = new_price
    df.loc[mask, "last_updated"] = date.today().isoformat()
    df.loc[mask, "source"] = source
    return df


def main():
    df = pd.read_csv(DATA_PATH)
    updated_any = False

    # --- Example target: a cement price tracker page ---
    # Replace this URL with a page you've manually checked contains a current,
    # extractable price - it WILL need re-verification over time.
    cement_url = "https://arynews.tv/tag/cement-price/"
    try:
        soup = get_soup(cement_url)
        text = soup.get_text(" ", strip=True)
        price = extract_price_per_bag(text)
        if price:
            df = update_row(df, "_NationalFallback", "Cement (OPC 50kg bag)", price, cement_url)
            updated_any = True
            print(f"Cement updated: PKR {price}/bag")
        else:
            print("Could not extract a cement price from the page - check the URL/regex manually.")
    except Exception as e:
        print(f"Cement scrape failed (non-fatal): {e}")

    # --- Example target: a steel rate tracker page ---
    steel_url = "https://icons.com.pk/?p=20887"
    try:
        soup = get_soup(steel_url)
        text = soup.get_text(" ", strip=True)
        price = extract_price_per_kg(text)
        if price:
            df = update_row(df, "_NationalFallback", "Steel Rebar (Grade 60)", price, steel_url)
            updated_any = True
            print(f"Steel updated: PKR {price}/kg")
        else:
            print("Could not extract a steel price from the page - check the URL/regex manually.")
    except Exception as e:
        print(f"Steel scrape failed (non-fatal): {e}")

    if updated_any:
        df.to_csv(DATA_PATH, index=False)
        print("Saved data/material_rates.csv")
    else:
        print("No updates made - leaving data/material_rates.csv unchanged.")
        sys.exit(0)  # not a failure - a quiet week is normal for this data


if __name__ == "__main__":
    main()
