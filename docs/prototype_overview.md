# TropiConnect Prototype — Day 1 Summary

## Objectives
- Stand up a local, zero-cost data stack to showcase core TropiConnect functionality.
- Ingest FAOSTAT commodity price data (sample-based MVP) into PostgreSQL.
- Transform and validate data for analytics/ML readiness.
- Provide a demo-ready visualization for stakeholders.

## Architecture Snapshot

```
FAOSTAT sample CSV/API
        │
        ▼
Python ingestion (pipelines/commodity_prices.py)
        │
        ▼
PostgreSQL
  ├── raw_data.faostat_prices     (JSON payloads + ingestion audit)
  ├── raw_data.ingestion_runs     (status & metadata)
  ├── processed_data.commodity_prices  (cleaned table)
  └── processed_data.dataset_metadata  (refresh history)
        │
        ▼
Streamlit dashboard (streamlit_app.py) + future ML feature prep
```

## Key Components Delivered

### Ingestion Layer (`pipelines/`)
- `commodity_prices.py`
  - Fetch FAOSTAT price data via API with sample CSV fallback.
  - Persist raw rows as JSON into `raw_data.faostat_prices`.
  - Record run metadata in `raw_data.ingestion_runs`.
- `database.py`
  - Centralized SQLAlchemy engine builder using env vars.
- `ingest.py`
  - CLI entry point: `python -m pipelines.ingest commodity_prices --use-sample`.

### Transformation Layer (`etl/`)
- `commodity_prices_clean.py`
  - Reads raw JSON payloads.
  - Normalizes date, commodity identifiers, price metrics.
  - Validates using Pandera schema (`CommodityPriceSchema`).
  - Loads clean data into `processed_data.commodity_prices`.
  - Updates dataset metadata (`processed_data.dataset_metadata`).
  - Entry point: `python -m etl.commodity_prices_clean`.

### Data Storage (`sql/setup_postgres.sql`)
- Creates schemas:
  - `raw_data`, `processed_data`, `analytics`.
- Tables:
  - `raw_data.faostat_prices`, `raw_data.ingestion_runs`.
  - `processed_data.commodity_prices`, `processed_data.dataset_metadata`.

### Visualization (`streamlit_app.py`)
- Connects to PostgreSQL using shared engine.
- Sidebar filters for commodity, price type, and date range.
- Displays metrics, line chart trends, summary statistics, raw data table.
- Launch via `streamlit run streamlit_app.py`.

### Supporting Files
- `data/samples/faostat_prices_sample.csv` for offline ingestion testing.
- `requirements.txt` pinned to numpy < 2.0, includes Pandera and Streamlit.
- `README.md` updated with end-to-end run instructions.
- `docs/data_sources.md` capturing initial source register.

## Current Workflow

1. **Configure environment**
   ```bash
   export POSTGRES_USER=jessemutenyo
   export POSTGRES_HOST=localhost
   export POSTGRES_PORT=5433
   export POSTGRES_DB=tropi_data
   export POSTGRES_PASSWORD=<if required>
   ```

2. **Install dependencies**
   ```bash
   python3 -m pip install --upgrade --force-reinstall -r requirements.txt
   ```

3. **Bootstrap database**
   ```bash
   psql -h localhost -p 5433 -U jessemutenyo -d tropi_data -f sql/setup_postgres.sql
   ```

4. **Ingest sample data**
   ```bash
   python3 -m pipelines.ingest commodity_prices --use-sample
   ```

5. **Run ETL**
   ```bash
   python3 -m etl.commodity_prices_clean
   ```

6. **Visualize**
   ```bash
   streamlit run streamlit_app.py
   ```

## Next Iterations
- Integrate additional sources (NASA POWER climate data, World Bank Pink Sheet).
- Parameterize ingestion to accept arbitrary CSV/API inputs.
- Add more ETL modules with Pandera validation across domains.
- Expand Streamlit dashboard to include multi-domain views (climate vs. prices).
- Begin feature engineering for predictive models (rolling averages, anomaly detection).

## Notes & Lessons
- Pinning NumPy `< 2.0` avoids Pandera compatibility issues.
- Environment variables are critical; ensure they’re exported in the shell before running pipelines or Streamlit.
- Raw JSON storage provides flexibility for schema evolution, but formal staging models can be layered in later.
