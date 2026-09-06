import streamlit as st
from cost_model import load_data, simple_estimate, detailed_estimate

st.set_page_config(page_title="Pakistan Construction Cost Estimator", page_icon="🏗️", layout="centered")

st.title("🏗️ Pakistan House Construction Cost Estimator")
st.caption(
    "Estimates only, for early-stage budgeting. Actual costs vary by contractor, "
    "site conditions, design, and material quality tier. Not a substitute for a "
    "professional quotation."
)

city_rates, material_rates, quantity_norms = load_data()

col1, col2 = st.columns(2)
with col1:
    city = st.selectbox("City", sorted(city_rates["city"].tolist()))
    area = st.number_input("Covered area (sqft)", min_value=100, value=1500, step=50)
with col2:
    mode = st.radio("Estimate type", ["Simple", "Detailed"])
    quality = st.radio("Finishing quality (simple mode)", ["standard", "premium"])

st.divider()

if st.button("Estimate cost", type="primary", use_container_width=True):
    if mode == "Simple":
        r = simple_estimate(city_rates, city, area, quality)
        st.metric("Estimated total cost", f"PKR {r['total_cost']:,}")

        c1, c2 = st.columns(2)
        c1.metric("Grey structure", f"PKR {r['grey_structure_cost']:,}")
        c2.metric("Finishing", f"PKR {r['finishing_cost']:,}")

        st.caption(f"Per sqft rate used: PKR {r['per_sqft_rate']:,}  |  Rates last updated: {r['last_updated']}")
        st.caption(f"Source: {r['source']}")

    else:
        try:
            r = detailed_estimate(material_rates, quantity_norms, city, area)
        except ValueError as e:
            st.error(str(e))
        else:
            st.metric("Estimated total (core structural materials + labor)", f"PKR {r['total_cost']:,}")
            st.info(
                "Detailed mode currently prices core structural materials only "
                "(cement, steel, bricks, sand, crush) plus labor. It does not yet include "
                "formwork/shuttering, excavation, doors & windows, electrical, plumbing, "
                "or finishing trades — so this total will read lower than Simple mode's "
                "grey-structure figure for the same city and area. See the build guide's "
                "roadmap section for extending this table."
            )
            st.dataframe(
                r["breakdown"][["material", "quantity_needed", "unit", "unit_price_pkr", "cost"]],
                use_container_width=True,
                hide_index=True,
            )
            c1, c2 = st.columns(2)
            c1.metric("Material subtotal", f"PKR {r['material_total']:,}")
            c2.metric("Labor (est.)", f"PKR {r['labor_cost']:,}")

with st.expander("Data sources & disclaimer"):
    st.markdown(
        """
        Rates are compiled from a mix of:
        - Government urban inter-city consumer price index data (construction & energy items),
          reported via *The News* (Jan 2026 figures for Karachi, Lahore, Islamabad, Peshawar, Quetta)
        - National retail market reports (cement, steel) for cities without a city-specific row yet
        - Published regional construction cost guides for grey structure / finishing per-sqft ranges

        These are **indicative estimates for early-stage budgeting**, not formal quotations.
        Cities marked "Estimated ... needs local validation" in the data files have not yet
        been checked against local dealer/contractor quotes — treat those numbers with extra caution.
        """
    )
