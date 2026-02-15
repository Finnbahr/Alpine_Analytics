"""
PostgreSQL database connection management
"""

import os
import psycopg2
from psycopg2 import pool
from dotenv import load_dotenv
from contextlib import contextmanager

# Load environment variables
load_dotenv()

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', '127.0.0.1'),
    'user': os.getenv('DB_USER', 'alpine_analytics'),
    'password': os.getenv('DB_PASSWORD'),
    'port': os.getenv('DB_PORT', '5433')
}

RAW_DB_NAME = os.getenv('RAW_DB_NAME', 'alpine_analytics')
AGGREGATE_DB_NAME = os.getenv('AGGREGATE_DB_NAME', 'fis_aggregate_data')

# Connection pools (lazy initialization)
_raw_pool = None
_aggregate_pool = None


def _get_pool(database_name, min_conn=1, max_conn=10):
    """Create a connection pool for the specified database"""
    return psycopg2.pool.ThreadedConnectionPool(
        min_conn,
        max_conn,
        **DB_CONFIG,
        database=database_name
    )


def get_raw_pool():
    """Get or create the raw database connection pool"""
    global _raw_pool
    if _raw_pool is None:
        _raw_pool = _get_pool(RAW_DB_NAME)
    return _raw_pool


def get_aggregate_pool():
    """Get or create the aggregate database connection pool"""
    global _aggregate_pool
    if _aggregate_pool is None:
        _aggregate_pool = _get_pool(AGGREGATE_DB_NAME)
    return _aggregate_pool


@contextmanager
def get_connection(database='raw', autocommit=False):
    """
    Context manager for database connections

    Args:
        database: 'raw' or 'aggregate'
        autocommit: Enable autocommit mode

    Usage:
        with get_connection('raw') as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM raw.fis_results LIMIT 10")
            results = cursor.fetchall()
    """
    pool = get_raw_pool() if database == 'raw' else get_aggregate_pool()
    conn = pool.getconn()

    if autocommit:
        conn.autocommit = True

    try:
        yield conn
        if not autocommit:
            conn.commit()
    except Exception as e:
        if not autocommit:
            conn.rollback()
        raise e
    finally:
        pool.putconn(conn)


def get_raw_connection(autocommit=False):
    """Get a connection to the raw database"""
    return get_connection(database='raw', autocommit=autocommit)


def get_aggregate_connection(autocommit=False):
    """Get a connection to the aggregate database"""
    return get_connection(database='aggregate', autocommit=autocommit)


def test_connection(database='raw', verbose=True):
    """
    Test database connection

    Args:
        database: 'raw' or 'aggregate'
        verbose: Print connection details

    Returns:
        bool: True if connection successful
    """
    try:
        with get_connection(database) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT current_database(), current_user, version()")
            db_name, user, version = cursor.fetchone()

            if verbose:
                print(f"✅ Connected to PostgreSQL")
                print(f"   Database: {db_name}")
                print(f"   User: {user}")
                print(f"   Version: {version.split(',')[0]}")

            cursor.close()
            return True

    except Exception as e:
        if verbose:
            print(f"❌ Connection failed: {e}")
        return False


def close_all_pools():
    """Close all connection pools"""
    global _raw_pool, _aggregate_pool

    if _raw_pool:
        _raw_pool.closeall()
        _raw_pool = None

    if _aggregate_pool:
        _aggregate_pool.closeall()
        _aggregate_pool = None


if __name__ == '__main__':
    # Test connections
    print("Testing database connections...\n")

    print("Raw database:")
    test_connection('raw')

    print("\nAggregate database:")
    test_connection('aggregate')

    close_all_pools()
