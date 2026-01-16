# Data consultancy Prototype (Local-First)

## Quick Start

1. **Clone & set up environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt  # placeholder until Pipfile/poetry is added
   ```

2. **Configure environment variables**
   - Copy `.env.example` to `.env`
   - Provide API keys or endpoints as needed (NASA POWER, FAOSTAT, etc.)

3. **Run PostgreSQL locally**
   ```bash
   docker compose up -d
   psql -h localhost -U postgres -d tropiconnect -f sql/setup_postgres.sql
   ```

4. **Execute an ingestion**
   ```bash
   python -m pipelines.ingest commodity_prices --use-sample
   ```

5. **Run the ETL transform**
   ```bash
   python -m etl.commodity_prices_clean
   ```
   This validates the raw payloads with Pandera and loads curated rows into
   `processed_data.commodity_prices`.

6. **Inspect results**
   ```bash
   psql -h localhost -p 5433 -U jessemutenyo -d tropi_data \
     -c "select * from processed_data.commodity_prices limit 10;"
   ```

## Streamlit Dashboard (optional)

Visualise curated data for stakeholder demos:
```bash
streamlit run streamlit_app.py
```

Ensure the same Postgres environment variables used for the pipelines are set in the shell before launching Streamlit. The app provides sidebar filters (commodity, price type, date range) and a trend chart backed by `processed_data.commodity_prices`.

## Repository Layout

```
docs/           # Architecture notes, data source register
pipelines/      # Ingestion scripts (API/CSV loaders)
etl/            # Transformation scripts (raw -> processed)
sql/            # Database schema setup scripts
logs/           # Runtime logs (captured by Python logging)
data/samples/   # Sample payloads / CSV fixtures
```

## Next Steps

- Flesh out `pipelines/commodity_prices.py` using FAOSTAT/World Bank data.
- Implement Pandera models for validation in `etl/`.
- Add cron/scheduler instructions once manual runs are stable.
