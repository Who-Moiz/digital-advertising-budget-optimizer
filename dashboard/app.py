"""Interactive exploration and allocation; large-file work belongs in the CLI."""

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from ad_budget.analytics import aggregate, with_kpis
from ad_budget.optimizer import recommend
from ad_budget.schema import MEASURES, validate

st.set_page_config(page_title="Advertising Budget Optimizer", page_icon="📊", layout="wide")
st.title("Advertising Budget Optimizer")
st.caption("Campaign performance and budget scenarios · PKR · Synthetic demo data")
sample = Path(__file__).resolve().parents[1] / "data" / "sample" / "campaigns.csv"
with st.sidebar:
    st.header("Data and filters")
    upload = st.file_uploader("Upload campaign CSV (up to 200,000 rows)", type="csv")
try:
    frame = pd.read_csv(upload if upload else sample, nrows=200_001)
    if len(frame) > 200_000:
        st.error("Dashboard limit: 200,000 rows. Use CLI analytics for larger datasets.")
        st.stop()
    validate(frame)
except (ValueError, OSError) as exc:
    st.error(f"Unable to load data: {exc}")
    st.stop()

with st.sidebar:
    platforms = st.multiselect(
        "Platforms", sorted(frame.platform.unique()), default=sorted(frame.platform.unique())
    )
    cities = st.multiselect(
        "Cities", sorted(frame.city.unique()), default=sorted(frame.city.unique())
    )
    devices = st.multiselect(
        "Devices", sorted(frame.device.unique()), default=sorted(frame.device.unique())
    )
    start, end = pd.to_datetime(frame.date).agg(["min", "max"])
    dates = st.date_input(
        "Date range", (start.date(), end.date()), min_value=start.date(), max_value=end.date()
    )
    budget = st.number_input("Next budget (PKR)", min_value=100.0, value=1_000_000.0, step=10_000.0)
    minimum = st.slider("Minimum platform share (%)", 0, 20, 5) / 100
    maximum = st.slider("Maximum platform share (%)", 20, 100, 45) / 100
    saturation = st.slider("Diminishing returns assumption", 0.1, 2.0, 0.75, 0.05)

filtered = frame[
    frame.platform.isin(platforms) & frame.city.isin(cities) & frame.device.isin(devices)
].copy()
if len(dates) == 2:
    filtered = filtered[filtered.date.between(str(dates[0]), str(dates[1]))]
if filtered.empty:
    st.info("No records match these filters. Select more values.")
    st.stop()
totals = with_kpis(pd.DataFrame([filtered[list(MEASURES)].sum()])).iloc[0]
cards = st.columns(5)
for card, label, value in zip(
    cards,
    ["Spend", "Revenue", "ROAS", "CTR", "CPA"],
    [
        f"Rs. {totals.spend:,.0f}",
        f"Rs. {totals.revenue:,.0f}",
        f"{totals.roas:.2f}x",
        f"{totals.ctr:.2f}%",
        f"Rs. {totals.cpa:,.2f}",
    ],
):
    card.metric(label, value)
performance = aggregate(filtered)
overview, allocation, segments, records = st.tabs(
    ["Performance", "Budget recommendation", "Audience and campaigns", "Data"]
)
with overview:
    left, right = st.columns(2)
    left.plotly_chart(
        px.bar(performance, x="platform", y="roas", color="platform", title="Return on ad spend"),
        use_container_width=True,
    )
    daily = aggregate(filtered, "date")
    right.plotly_chart(
        px.line(daily, x="date", y=["spend", "revenue"], title="Daily spend and revenue (PKR)"),
        use_container_width=True,
    )
    st.dataframe(performance, hide_index=True, use_container_width=True)
    st.caption("CTR and conversion rate are percentages. Undefined ratios appear as blank values.")
with allocation:
    st.write("Allocate the next budget across the platforms present in your filtered data.")
    try:
        result = recommend(performance, budget, minimum, maximum, saturation=saturation)
        st.plotly_chart(
            px.bar(
                result,
                x="platform",
                y="recommended_budget",
                color="platform",
                title="Recommended spend (PKR)",
            ),
            use_container_width=True,
        )
        st.dataframe(
            result[
                [
                    "platform",
                    "recommended_budget",
                    "recommended_share_pct",
                    "share_change_pp",
                    "adjusted_roas",
                    "modeled_revenue",
                ]
            ],
            hide_index=True,
            use_container_width=True,
        )
        st.download_button(
            "Download budget plan",
            result.to_csv(index=False),
            "budget_recommendations.csv",
            "text/csv",
        )
        st.info(
            "Scenario estimate: historical attribution does not prove incremental return. "
            "The response curve is assumed. Validate recommendations with controlled tests."
        )
    except ValueError as exc:
        st.warning(str(exc))
with segments:
    dimension = st.selectbox("Compare by", ["campaign", "city", "device", "age", "gender"])
    st.dataframe(
        aggregate(filtered, dimension).sort_values("revenue", ascending=False),
        hide_index=True,
        use_container_width=True,
    )
with records:
    st.write(f"{len(filtered):,} matching records")
    st.dataframe(filtered.head(1000), hide_index=True, use_container_width=True)
    st.download_button(
        "Download platform KPIs",
        performance.to_csv(index=False),
        "platform_performance.csv",
        "text/csv",
    )
