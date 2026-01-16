"""
ETL pipeline to transform FAOSTAT commodity price data.

Reads JSON payloads from `raw_data.faostat_prices`, applies normalization and
validation, and writes curated rows into `processed_data.commodity_prices`.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime

import pandas as pd
import pandera as pa
from pandera.typing import Series
from sqlalchemy import text

from pipelines.database import get_engine

LOGGER = logging.getLogger("etl.commodity_prices")


class CommodityPriceSchema(pa.SchemaModel):
    price_date: Series[pd.Timestamp] = pa.Field(nullable=False)
    commodity_id: Series[str] = pa.Field(nullable=True)
    commodity_name: Series[str] = pa.Field(nullable=True)
    price_type: Series[str] = pa.Field(nullable=True)
    price_currency: Series[str] = pa.Field(nullable=True)
    price_value: Series[float] = pa.Field(nullable=False)
    source_name: Series[str] = pa.Field(nullable=True)
    ingested_at: Series[pd.Timestamp] = pa.Field(nullable=True)
    raw_id: Series[int] = pa.Field(nullable=False)

    class Config:
        coerce = True


def _load_raw_dataframe() -> pd.DataFrame:
    engine = get_engine()
    with engine.connect() as conn:
        raw_df = pd.read_sql(
            "select id, payload::text as payload from raw_data.faostat_prices", conn
        )
    if raw_df.empty:
        LOGGER.warning("No rows available in raw_data.faostat_prices")
        return pd.DataFrame()

    payloads = raw_df["payload"].apply(json.loads)
    normalized = pd.json_normalize(payloads)
    normalized["raw_id"] = raw_df["id"]
    return normalized


def _coalesce_columns(df: pd.DataFrame, candidates: list[str], default=None):
    for column in candidates:
        if column in df:
            series = df[column]
            if not series.isna().all():
                return series
    return default if default is not None else pd.Series([None] * len(df))


def transform(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    output = pd.DataFrame()

    # Date handling
    date_series = _coalesce_columns(
        df,
        ["price_date", "timeperiod", "time", "year"],
    )
    date_series = date_series.astype(str).str.strip()
    output["price_date"] = pd.to_datetime(
        date_series, errors="coerce", format=None, utc=False
    )

    output["commodity_id"] = _coalesce_columns(
        df, ["commodity_id", "item_code", "Item Code (CPC)"]
    )
    output["commodity_name"] = _coalesce_columns(
        df, ["commodity_name", "item", "Item"]
    )
    output["price_type"] = _coalesce_columns(
        df, ["price_type", "element", "Element"]
    )
    output["price_currency"] = _coalesce_columns(
        df, ["price_currency", "unit", "Unit"], default="USD"
    )
    price_values = _coalesce_columns(df, ["price_value", "Value"])
    output["price_value"] = pd.to_numeric(price_values, errors="coerce")
    output["source_name"] = _coalesce_columns(
        df, ["source_name", "Source"], default="FAOSTAT"
    )
    ingested_series = _coalesce_columns(
        df, ["ingested_at"], default=datetime.utcnow()
    )
    output["ingested_at"] = pd.to_datetime(ingested_series, errors="coerce")
    output["raw_id"] = df["raw_id"]

    # Drop rows without essential fields
    output = output.dropna(subset=["price_date", "price_value"])
    output["price_value"] = output["price_value"].astype(float)
    output["price_date"] = output["price_date"].dt.tz_localize(None)
    output["ingested_at"] = output["ingested_at"].dt.tz_localize(None)

    # Deduplicate keeping the most recent ingested_at
    output = (
        output.sort_values("ingested_at", ascending=False)
        .drop_duplicates(
            subset=["price_date", "commodity_id", "price_type", "source_name"],
            keep="first",
        )
        .reset_index(drop=True)
    )

    return output


def load(df: pd.DataFrame) -> int:
    if df.empty:
        LOGGER.warning("No rows to load into processed_data.commodity_prices")
        return 0

    engine = get_engine()
    records = df.assign(price_date=df["price_date"].dt.date).to_dict("records")

    with engine.begin() as conn:
        conn.execute(
            text(
                """
                create table if not exists processed_data.commodity_prices (
                    price_date date not null,
                    commodity_id text,
                    commodity_name text,
                    price_type text,
                    price_currency text,
                    price_value numeric not null,
                    source_name text,
                    ingested_at timestamptz,
                    raw_id integer not null,
                    primary key (price_date, commodity_id, price_type, source_name)
                )
                """
            )
        )

        conn.execute(text("truncate table processed_data.commodity_prices"))
        conn.execute(
            text(
                """
                insert into processed_data.commodity_prices (
                    price_date,
                    commodity_id,
                    commodity_name,
                    price_type,
                    price_currency,
                    price_value,
                    source_name,
                    ingested_at,
                    raw_id
                )
                values (
                    :price_date,
                    :commodity_id,
                    :commodity_name,
                    :price_type,
                    :price_currency,
                    :price_value,
                    :source_name,
                    :ingested_at,
                    :raw_id
                )
                """
            ),
            records,
        )

        conn.execute(
            text(
                """
                insert into processed_data.dataset_metadata
                    (dataset_name, last_refreshed_at, row_count, notes)
                values
                    (:name, now(), :rows, :notes)
                on conflict (dataset_name) do update
                set last_refreshed_at = excluded.last_refreshed_at,
                    row_count = excluded.row_count,
                    notes = excluded.notes
                """
            ),
            {
                "name": "commodity_prices",
                "rows": len(df),
                "notes": "Generated by etl.commodity_prices_clean",
            },
        )

    return len(df)


def run():
    logging.basicConfig(level=logging.INFO)
    raw_df = _load_raw_dataframe()
    transformed = transform(raw_df)
    CommodityPriceSchema.validate(transformed, lazy=True)
    rows = load(transformed)
    LOGGER.info("Loaded %s rows into processed_data.commodity_prices", rows)


if __name__ == "__main__":
    run()
