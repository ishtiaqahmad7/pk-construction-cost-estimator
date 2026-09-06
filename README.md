# Pakistan House Construction Cost Estimator

A Streamlit app that estimates house construction costs across major Pakistani
cities, in two modes:
- **Simple** — city per-sqft rate × covered area
- **Detailed** — core structural materials (cement, steel, bricks, sand, crush) × current unit price + labor

## Quick start (local)

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy

Push this repo to GitHub, then deploy on [share.streamlit.io](https://share.streamlit.io)
pointing at `app.py`. See the full build guide (shared alongside this repo)
for the complete Colab → Gradio → GitHub → Streamlit workflow this was built with.

## Data

- `data/city_rates.csv` — per-sqft grey structure & finishing rate ranges, per city
- `data/material_rates.csv` — current unit prices for core materials, per city where available, with a `_NationalFallback` row used for any city not yet covered
- `data/quantity_norms.csv` — rule-of-thumb material quantity per sqft, used by Detailed mode

**Rates are seeded from public sources as of Jan–Aug 2026** (see the `source`
column in each CSV) and are estimates for early-stage budgeting, not formal
quotations. Rows marked "needs local validation" have not been checked
against local dealer/contractor quotes yet.

## Keeping data fresh

`scraper/update_rates.py` is a starting template that refreshes the national
fallback cement/steel prices. It's wired to run automatically via
`.github/workflows/update_rates.yml` on the 1st and 15th of each month, but
the target URLs/regexes will need periodic manual review — see the comments
in that file for why.

## Status of this build

This is a v1 starter: validated with real seed data and a working cost model
(see `cost_model.py`'s `__main__` block for a quick sanity check), but the
city coverage, quantity norms, and detailed-mode material list are all
intentionally minimal — extend them as you validate against real local quotes.
