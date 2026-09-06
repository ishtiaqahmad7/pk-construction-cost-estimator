"""
Cost calculation engine for the Pakistan House Construction Cost Estimator.

Two modes:
  - simple_estimate(): city per-sqft rate x area (grey structure + finishing)
  - detailed_estimate(): material quantities x current unit prices + labor%

Both read from the three CSVs in data/. See the accompanying build guide
for the full reasoning behind this data model.
"""

import pandas as pd

FALLBACK_CITY = "_NationalFallback"


def load_data(data_dir="data"):
    city_rates = pd.read_csv(f"{data_dir}/city_rates.csv")
    material_rates = pd.read_csv(f"{data_dir}/material_rates.csv")
    quantity_norms = pd.read_csv(f"{data_dir}/quantity_norms.csv")
    return city_rates, material_rates, quantity_norms


def simple_estimate(city_rates: pd.DataFrame, city: str, area_sqft: float, quality: str = "standard"):
    """Per-sqft rate x area. quality is 'standard' or 'premium'.

    Both grey structure and finishing now shift with quality tier: 'standard'
    lands in the lower third of the city's range, 'premium' in the upper
    third. (Earlier version used a flat midpoint for grey structure
    regardless of quality - validation against Zameen's calculator in Sep
    2026 showed real market rates skew toward the upper end of these
    ranges, so a flat midpoint under-estimated across the board.)
    """
    match = city_rates[city_rates["city"] == city]
    if match.empty:
        raise ValueError(f"No rate data for city '{city}'")
    row = match.iloc[0]

    grey_range = row.grey_structure_rate_high - row.grey_structure_rate_low
    if quality == "standard":
        grey = row.grey_structure_rate_low + grey_range / 6      # lower-third midpoint
        finishing = row.finishing_rate_low
    else:
        grey = row.grey_structure_rate_low + 5 * grey_range / 6  # upper-third midpoint
        finishing = row.finishing_rate_high

    per_sqft = grey + finishing
    total = per_sqft * area_sqft

    return {
        "per_sqft_rate": round(per_sqft),
        "total_cost": round(total),
        "grey_structure_cost": round(grey * area_sqft),
        "finishing_cost": round(finishing * area_sqft),
        "last_updated": row.last_updated,
        "source": row.source,
    }


def _rates_for_city(material_rates: pd.DataFrame, city: str) -> pd.DataFrame:
    """Return material rates for `city`, filling any missing materials from
    the _NationalFallback rows so the detailed estimate never silently drops
    a material just because a city-specific price hasn't been collected yet."""
    city_rows = material_rates[material_rates["city"] == city]
    fallback_rows = material_rates[material_rates["city"] == FALLBACK_CITY]

    have = set(city_rows["material"])
    needed_fallback = fallback_rows[~fallback_rows["material"].isin(have)]

    combined = pd.concat([city_rows, needed_fallback], ignore_index=True)
    return combined[["material", "unit", "unit_price_pkr", "last_updated", "source"]]


def detailed_estimate(material_rates: pd.DataFrame, quantity_norms: pd.DataFrame,
                       city: str, area_sqft: float, labor_pct: float = 0.32):
    """Material quantities (from quantity_norms) x current unit price (from
    material_rates, city-specific where available, else national fallback),
    plus labor as a percentage of TOTAL project cost (not just material cost)."""
    rates = _rates_for_city(material_rates, city)
    # both tables have a 'unit' column (e.g. bag, kg) - drop the quantity_norms
    # one and keep the rates' unit, since that's the one unit_price_pkr is priced in
    norms = quantity_norms.drop(columns=["unit"])
    merged = norms.merge(rates, on="material", how="left")

    missing = merged[merged["unit_price_pkr"].isna()]
    if not missing.empty:
        missing_list = ", ".join(missing["material"].tolist())
        raise ValueError(f"No price available (city or fallback) for: {missing_list}")

    merged["quantity_needed"] = merged["qty_per_sqft"] * area_sqft
    merged["cost"] = merged["quantity_needed"] * merged["unit_price_pkr"]

    material_total = merged["cost"].sum()
    # labor_pct expressed as % of TOTAL cost, so back it out from material total:
    labor_cost = material_total * (labor_pct / (1 - labor_pct))
    total = material_total + labor_cost

    breakdown = merged[["material", "quantity_needed", "unit", "unit_price_pkr", "cost", "last_updated", "source"]].copy()
    breakdown["quantity_needed"] = breakdown["quantity_needed"].round(2)
    breakdown["cost"] = breakdown["cost"].round(0)

    return {
        "breakdown": breakdown,
        "material_total": round(material_total),
        "labor_cost": round(labor_cost),
        "total_cost": round(total),
    }


if __name__ == "__main__":
    # Quick manual sanity check when running this file directly
    city_rates, material_rates, quantity_norms = load_data()
    print("=== Simple estimate: Lahore, 1500 sqft, standard ===")
    print(simple_estimate(city_rates, "Lahore", 1500, "standard"))
    print()
    print("=== Detailed estimate: Karachi, 1500 sqft ===")
    result = detailed_estimate(material_rates, quantity_norms, "Karachi", 1500)
    print(result["breakdown"].to_string(index=False))
    print(f"\nMaterial total: PKR {result['material_total']:,}")
    print(f"Labor cost:     PKR {result['labor_cost']:,}")
    print(f"TOTAL:          PKR {result['total_cost']:,}")
