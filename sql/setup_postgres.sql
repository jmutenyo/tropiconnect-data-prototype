-- Create core schemas
create schema if not exists raw_data;
create schema if not exists processed_data;
create schema if not exists analytics;

-- Audit tables
create table if not exists raw_data.ingestion_runs (
    id serial primary key,
    source_name text not null,
    run_started_at timestamptz not null default now(),
    run_finished_at timestamptz,
    status text not null default 'running',
    rows_ingested bigint default 0,
    error_message text
);

create table if not exists processed_data.dataset_metadata (
    dataset_name text primary key,
    last_refreshed_at timestamptz,
    row_count bigint,
    notes text
);

create table if not exists raw_data.faostat_prices (
    id serial primary key,
    payload jsonb not null,
    created_at timestamptz not null default now()
);
