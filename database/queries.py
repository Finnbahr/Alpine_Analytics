"""
Database query utilities
"""

from .connection import get_connection


def execute_query(query, params=None, database='raw', autocommit=False):
    """
    Execute a query that doesn't return results (INSERT, UPDATE, DELETE)

    Args:
        query: SQL query string
        params: Query parameters (tuple or dict)
        database: 'raw' or 'aggregate'
        autocommit: Enable autocommit mode

    Returns:
        int: Number of rows affected
    """
    with get_connection(database, autocommit=autocommit) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rowcount = cursor.rowcount
        cursor.close()
        return rowcount


def fetch_one(query, params=None, database='raw'):
    """
    Execute a query and fetch one row

    Args:
        query: SQL query string
        params: Query parameters (tuple or dict)
        database: 'raw' or 'aggregate'

    Returns:
        tuple: Single row result or None
    """
    with get_connection(database) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        result = cursor.fetchone()
        cursor.close()
        return result


def fetch_all(query, params=None, database='raw'):
    """
    Execute a query and fetch all rows

    Args:
        query: SQL query string
        params: Query parameters (tuple or dict)
        database: 'raw' or 'aggregate'

    Returns:
        list: List of tuples (rows)
    """
    with get_connection(database) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        results = cursor.fetchall()
        cursor.close()
        return results


def execute_many(query, params_list, database='raw', autocommit=False):
    """
    Execute a query multiple times with different parameters (batch insert)

    Args:
        query: SQL query string
        params_list: List of parameter tuples
        database: 'raw' or 'aggregate'
        autocommit: Enable autocommit mode

    Returns:
        int: Number of rows affected
    """
    with get_connection(database, autocommit=autocommit) as conn:
        cursor = conn.cursor()
        cursor.executemany(query, params_list)
        rowcount = cursor.rowcount
        cursor.close()
        return rowcount


def fetch_dataframe(query, params=None, database='raw'):
    """
    Execute a query and return results as a pandas DataFrame

    Args:
        query: SQL query string
        params: Query parameters (tuple or dict)
        database: 'raw' or 'aggregate'

    Returns:
        pd.DataFrame: Query results as DataFrame
    """
    import pandas as pd
    from .connection import get_connection

    with get_connection(database) as conn:
        df = pd.read_sql_query(query, conn, params=params)
        return df


def get_table_info(schema, table, database='raw'):
    """
    Get information about a table's structure

    Args:
        schema: Schema name (e.g., 'raw')
        table: Table name
        database: 'raw' or 'aggregate'

    Returns:
        list: List of (column_name, data_type, is_nullable) tuples
    """
    query = """
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_schema = %s AND table_name = %s
        ORDER BY ordinal_position
    """
    return fetch_all(query, (schema, table), database=database)


def table_exists(schema, table, database='raw'):
    """
    Check if a table exists

    Args:
        schema: Schema name
        table: Table name
        database: 'raw' or 'aggregate'

    Returns:
        bool: True if table exists
    """
    query = """
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema = %s AND table_name = %s
        )
    """
    result = fetch_one(query, (schema, table), database=database)
    return result[0] if result else False
