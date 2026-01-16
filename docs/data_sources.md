# Data Source Register

| Source | Domain | Access Type | Update Frequency | License/Cost | Notes |
| --- | --- | --- | --- | --- | --- |
| World Bank Pink Sheet | Commodity pricing | Monthly CSV (HTTP) | Monthly | Open data (CC BY 4.0) | Historical commodity prices (USD). Use for baseline pricing curves. |
| FAOSTAT Price Statistics | Commodity pricing | Bulk CSV download | Annual refresh | Open data | Regional agricultural price indicators; requires manual export or FAOSTAT API. |
| NASA POWER | Climate & weather | REST API (JSON/CSV) | Daily/hourly | Open data | Temperature, precipitation, solar radiation; supports location-specific queries. |
| Meteostat | Climate & weather | REST API (JSON) | Hourly/daily | CC BY 4.0 | Supplement NASA for station-level weather; requires attribution. |
| Internal Client CSVs | Production & sales | Secure file upload | As provided | Proprietary | Client-supplied production volumes, distribution metrics; ensure NDA compliance. |

## Tracking Fields

- `source_name`: canonical identifier used in scripts and tables  
- `data_type`: API, CSV, JSON, etc.  
- `frequency`: expected ingest cadence  
- `ownership`: `external` vs `client`  
- `auth`: API key, token, or none  
- `status`: planned, active, deprecated  

Extend this document as new feeds are onboarded. Store sample payloads in `data/samples/` for quick reference during development.
