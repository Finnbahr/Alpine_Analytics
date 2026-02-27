"""
Alpine Analytics — Database connection helpers.

Locally: reads credentials from .env in this folder.
Production: reads from Streamlit secrets (st.secrets) or environment variables.
"""

import os
import pandas as pd
from sqlalchemy import create_engine, text

# Try loading .env for local development
try:
    from dotenv import load_dotenv
    _HERE = os.path.dirname(os.path.abspath(__file__))
    _ETL_DIR = os.path.join(_HERE, "..", "Alpine Analytics")
    if os.path.exists(os.path.join(_HERE, ".env")):
        load_dotenv(os.path.join(_HERE, ".env"))
    elif os.path.exists(os.path.join(_ETL_DIR, ".env")):
        load_dotenv(os.path.join(_ETL_DIR, ".env"))
except ImportError:
    pass


def _connection_url() -> str:
    # Streamlit Cloud: read from st.secrets if available
    try:
        import streamlit as st
        s = st.secrets["database"]
        return (
            f"postgresql+psycopg2://{s['DB_USER']}:{s['DB_PASSWORD']}"
            f"@{s['DB_HOST']}:{s.get('DB_PORT', 5432)}"
            f"/{s['DB_NAME']}"
        )
    except Exception:
        pass

    # Local / Railway env vars
    return (
        f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
        f"@{os.getenv('DB_HOST', '127.0.0.1')}:{os.getenv('DB_PORT', 5433)}"
        f"/{os.getenv('RAW_DB_NAME', os.getenv('DB_NAME', 'alpine_analytics'))}"
    )


def get_engine():
    return create_engine(_connection_url(), pool_pre_ping=True)


def query(sql: str, params: dict | None = None) -> pd.DataFrame:
    """Run a SELECT and return a DataFrame. Use :name placeholders for params."""
    engine = get_engine()
    with engine.connect() as conn:
        return pd.read_sql_query(text(sql), conn, params=params)
