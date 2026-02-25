"""
Database connection utilities.
"""

import logging
import psycopg2
from typing import Dict, List, Optional
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager

from app.config import settings

logger = logging.getLogger(__name__)


@contextmanager
def get_connection():
    """
    Get database connection as context manager.

    Yields:
        psycopg2 connection
    """
    conn = None
    try:
        conn = psycopg2.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            database=settings.DB_NAME
        )
        yield conn
    finally:
        if conn:
            conn.close()


def test_connection() -> bool:
    """
    Test database connection.

    Returns:
        bool: True if connection successful, False otherwise
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
        logger.info("✅ Database connection successful")
        return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False


def execute_query(query: str, params: dict = None) -> List[Dict]:
    """
    Execute a SQL query and return results as list of dicts.

    Args:
        query: SQL query string
        params: Query parameters (optional)

    Returns:
        list: List of dictionaries with query results
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(query, params)
            results = cursor.fetchall()
            cursor.close()
            # Convert RealDictRow to regular dict
            return [dict(row) for row in results] if results else []
    except Exception as e:
        logger.error(f"Query execution failed: {e}")
        raise


def execute_query_single(query: str, params: dict = None) -> Optional[Dict]:
    """
    Execute a SQL query and return single result as dict.

    Args:
        query: SQL query string
        params: Query parameters (optional)

    Returns:
        dict or None: Single result dictionary or None if no results
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(query, params)
            result = cursor.fetchone()
            cursor.close()
            # Convert RealDictRow to regular dict
            return dict(result) if result else None
    except Exception as e:
        logger.error(f"Query execution failed: {e}")
        raise
