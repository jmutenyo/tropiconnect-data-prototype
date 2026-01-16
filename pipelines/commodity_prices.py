"""
Prototype ingestion pipeline for commodity price data.

Steps:
1. Attempt to download FAOSTAT price statistics via API.
2. Fallback to bundled sample CSV when API is unreachable.
3. Persist raw payload in `raw_data.faostat_prices`.
4. Record ingestion run metadata in `raw_data.ingestion_runs`.
"""

from __future__ import annotations

import argparse
import io
import logging
import os
from datetime import datetime

import pandas as pd
import requests
from sqlalchemy import text

from .database import get_engine

LOGGER = logging.getLogger("pipelines.commodity_prices")

FAOSTAT_DEFAULT_ENDPOINT = (
    "https://fenixservices.fao.org/faostat/api/v1/en/Prices/TM_PC/data"
)


def fetch_faostat_data(
    dataset_url: str,
    area_code: str = "41",  # Kenya
    item_code: str = "2514",  # Coffee, arabica
    element_code: str = "5532",  # Wholesale price
    year_start: int = 2020,
    year_end: int = 2023,
) -> pd.DataFrame:
    """Fetch price data from the FAOSTAT API."""
    params = {
        "area_code": area_code,
        "item_code": item_code,
        "element_code": element_code,
        "time_year": ",".join(str(year) for year in range(year_start, year_end + 1)),
    }
    LOGGER.info("Requesting FAOSTAT data", extra={"params": params})

    response = requests.get(dataset_url, params=params, timeout=60)
    response.raise_for_status()
    payload = response.json()

    data = payload.get("data", [])
    if not data:
        raise ValueError("FAOSTAT response contained no data rows.")

    df = pd.json_normalize(data)
    df["source_name"] = "FAOSTAT"
    return df


def load_sample_csv(path: str) -> pd.DataFrame:
    LOGGER.warning("Using local sample CSV %s", path)
    return pd.read_csv(path)


def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Standardize column names/values for raw ingestion."""
    column_mapping = {
        "time": "price_year",
        "timeperiod": "price_year",
        "value": "price_value",
        "item_code": "commodity_id",
    }
    df = df.rename(columns=column_mapping)
    for required in ["price_value"]:
        if required not in df.columns:
            raise ValueError(f"Required column '{required}' missing")

    df["ingested_at"] = datetime.utcnow()
    return df


def persist_raw(df: pd.DataFrame, source_name: str) -> int:
    engine = get_engine()
    rows = len(df)
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                insert into raw_data.faostat_prices (payload)
                values (:payload)
                """
            ),
            [{"payload": row.to_json()} for _, row in df.iterrows()],
        )
    return rows


def record_run(status: str, rows: int, message: str | None = None) -> None:
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                insert into raw_data.ingestion_runs
                    (source_name, run_started_at, run_finished_at, status, rows_ingested, error_message)
                values
                    (:source_name, :started, :finished, :status, :rows, :error)
                """
            ),
            {
                "source_name": "faostat_prices",
                "started": datetime.utcnow(),
                "finished": datetime.utcnow(),
                "status": status,
                "rows": rows,
                "error": message,
            },
        )


def ingest(use_sample: bool = False) -> None:
    """Main entry point for ingestion."""
    logging.basicConfig(level=logging.INFO)
    try:
        if use_sample:
            df = load_sample_csv("data/samples/faostat_prices_sample.csv")
        else:
            endpoint = os.getenv("FAOSTAT_ENDPOINT", FAOSTAT_DEFAULT_ENDPOINT)
            df = fetch_faostat_data(endpoint)

    except Exception as exc:  # noqa: BLE001
        LOGGER.error("Primary fetch failed: %s", exc)
        LOGGER.info("Falling back to bundled sample data")
        df = load_sample_csv("data/samples/faostat_prices_sample.csv")

    df = normalize_dataframe(df)
    try:
        rows = persist_raw(df, source_name="faostat_prices")
        record_run("success", rows)
        LOGGER.info("Ingested %s rows into raw_data.faostat_prices", rows)
    except Exception as exc:  # noqa: BLE001
        LOGGER.exception("Failed to persist raw data: %s", exc)
        record_run("failed", rows=0, message=str(exc))
        raise


def cli():
    parser = argparse.ArgumentParser(description="Ingest FAOSTAT commodity prices.")
    parser.add_argument("--use-sample", action="store_true", help="Force use of local CSV sample.")
    args = parser.parse_args()
    ingest(use_sample=args.use_sample)


if __name__ == "__main__":
    cli()
