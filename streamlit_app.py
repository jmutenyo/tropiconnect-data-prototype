"""
Streamlit dashboard for TropiConnect prototype data.

Usage:
    streamlit run streamlit_app.py
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from pipelines.database import get_engine

st.set_page_config(
    page_title="TropiConnect Commodity Insight",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_data(ttl=300)
def load_prices() -> pd.DataFrame:
    engine = get_engine()
    query = """
        select
            price_date,
            commodity_id,
            commodity_name,
            price_type,
            price_currency,
            price_value,
            source_name,
            ingested_at
        from processed_data.commodity_prices
        order by price_date
    """
    with engine.connect() as conn:
        df = pd.read_sql(query, conn, parse_dates=["price_date", "ingested_at"])
    return df


def render_dashboard() -> None:
    st.title("TropiConnect Commodity Insight")
    st.markdown(
        "Explore curated FAOSTAT price data ingested through the local pipeline."
    )

    df = load_prices()
    if df.empty:
        st.warning(
            "No data available. Run the ingestion (`python -m pipelines.ingest ...`) "
            "and ETL (`python -m etl.commodity_prices_clean`) first."
        )
        return

    with st.sidebar:
        st.header("Filters")
        commodities = df["commodity_name"].fillna("Unknown").unique()
        selected_commodity = st.selectbox(
            "Commodity",
            options=sorted(commodities),
            index=0,
        )
        price_types = df["price_type"].fillna("Unknown").unique()
        selected_price_types = st.multiselect(
            "Price Types",
            options=sorted(price_types),
            default=sorted(price_types),
        )
        date_range = st.date_input(
            "Date range",
            value=(df["price_date"].min().date(), df["price_date"].max().date()),
        )

    filtered = df.copy()
    if selected_commodity:
        filtered = filtered[
            filtered["commodity_name"].fillna("Unknown") == selected_commodity
        ]
    if selected_price_types:
        filtered = filtered[
            filtered["price_type"].fillna("Unknown").isin(selected_price_types)
        ]
    if date_range and len(date_range) == 2:
        start, end = date_range
        filtered = filtered[
            (filtered["price_date"] >= pd.to_datetime(start))
            & (filtered["price_date"] <= pd.to_datetime(end))
        ]

    if filtered.empty:
        st.info("No data matches the current filters.")
        return

    latest_date = filtered["price_date"].max()
    latest_value = (
        filtered[filtered["price_date"] == latest_date]["price_value"].mean()
    )
    st.metric(
        "Most recent price",
        f"{latest_value:,.2f} {filtered['price_currency'].iloc[0]}",
        help=f"Average price on {latest_date.date()}",
    )

    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("Price Trend")
        st.line_chart(
            filtered.set_index("price_date")["price_value"],
            height=350,
        )
    with col2:
        st.subheader("Summary Statistics")
        st.dataframe(
            filtered[
                [
                    "price_date",
                    "price_value",
                    "price_type",
                    "price_currency",
                    "source_name",
                ]
            ].sort_values("price_date", ascending=False),
            use_container_width=True,
            height=350,
        )

    st.subheader("Raw Data")
    st.dataframe(filtered, use_container_width=True)


if __name__ == "__main__":
    render_dashboard()
