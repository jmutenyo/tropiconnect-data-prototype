import os
from functools import lru_cache

from sqlalchemy import create_engine


@lru_cache(maxsize=1)
def get_engine():
    """Return a cached SQLAlchemy engine built from environment variables."""
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD", "postgres")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "tropiconnect")

    url = f"postgresql+psycopg://{user}:{password}@{host}:{port}/{db}"
    return create_engine(url, future=True)
