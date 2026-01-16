# Data consultancy Prototype (Local-First)

[![Streamlit](https://img.shields.io/badge/Streamlit-live_demo-orange)](#streamlit-dashboard-optional)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Core%20DB-blue)](#quick-start)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

Local, zero-cost data stack that ingests FAOSTAT price data, validates it with Pandera, and visualises curated metrics via Streamlit.

## Quick Start

1. **Clone & set up environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

2. **Configure environment variables**
   ```bash
   export POSTGRES_USER=<user>
   export POSTGRES_PASSWORD=<password>  # optional if not required
   export POSTGRES_HOST=localhost
   export POSTGRES_PORT=5433
   export POSTGRES_DB=tropi_data
   ```
   Adjust values to match your Postgres instance.

3. **Bootstrap PostgreSQL**
   ```bash
   psql -h $POSTGRES_HOST -p $POSTGRES_PORT -U $POSTGRES_USER -d $POSTGRES_DB \
     -f sql/setup_postgres.sql
   ```

4. **Ingest sample data**
   ```bash
   python -m pipelines.ingest commodity_prices --use-sample
   ```

5. **Run the ETL transform**
   ```bash
   python -m etl.commodity_prices_clean
   ```
   This validates raw payloads with Pandera and loads curated rows into
   `processed_data.commodity_prices`.

6. **Inspect results**
   ```bash
   psql -h $POSTGRES_HOST -p $POSTGRES_PORT -U $POSTGRES_USER -d $POSTGRES_DB \
     -c "select * from processed_data.commodity_prices limit 10;"
   ```

## Streamlit Dashboard (optional)

Spin up a demo dashboard:
```bash
streamlit run streamlit_app.py
```

- Sidebar filters for commodity, price type, and date range.
- Trend chart & summary metrics sourced from `processed_data.commodity_prices`.
- Ensure the same Postgres environment variables are set in the shell.

## Repository Layout

```
docs/           # Architecture notes, data source register, daily summary
pipelines/      # Ingestion scripts (API/CSV loaders)
etl/            # Transformation scripts (raw -> processed)
sql/            # Database schema setup scripts
data/samples/   # Sample payloads / CSV fixtures
logs/           # Runtime logs placeholder
streamlit_app.py
```

## Next Steps

- Integrate additional sources (NASA POWER climate, World Bank prices).
- Extend ETL modules with Pandera schemas across domains.
- Automate runs via cron/Task Scheduler or lightweight orchestration.
- Add feature engineering for ML readiness and enhance the Streamlit story with multi-domain dashboards.
