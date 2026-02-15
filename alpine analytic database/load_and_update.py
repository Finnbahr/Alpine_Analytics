"""
Load and Update - Complete Weekly ETL Workflow

This script handles the complete workflow:
1. Load new race data into PostgreSQL (raw tables)
2. Identify which race_ids were added
3. Run incremental analytics updates for only those races

Usage:
    # Load CSV files and run incremental updates
    python3 load_and_update.py --race-details path/to/race_details.csv --results path/to/fis_results.csv

    # Skip analytics update (just load data)
    python3 load_and_update.py --race-details file.csv --results file.csv --skip-analytics

    # Run analytics for specific race IDs
    python3 load_and_update.py --race-ids 12345,12346,12347
"""

import sys
import os
import argparse
import logging
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_engine_connection():
    """Create PostgreSQL engine connection."""
    return create_engine(
        f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@"
        f"{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('RAW_DB_NAME')}"
    )


def get_existing_race_ids(engine):
    """
    Get set of race_ids that already exist in the database.

    Returns:
        set: Set of existing race_ids
    """
    logger.info("Querying existing race_ids...")
    with engine.connect() as conn:
        result = conn.execute(text("SELECT DISTINCT race_id FROM raw.race_details"))
        existing = {row[0] for row in result}
    logger.info(f"Found {len(existing):,} existing race_ids")
    return existing


def load_race_details(csv_path, engine):
    """
    Load race details CSV into raw.race_details table.

    Args:
        csv_path: Path to race_details CSV file
        engine: SQLAlchemy engine

    Returns:
        set: Set of newly added race_ids
    """
    logger.info(f"Loading race details from {csv_path}...")

    # Read CSV
    df = pd.read_csv(csv_path)
    logger.info(f"Read {len(df):,} race details from CSV")

    # Get existing race_ids to identify new ones
    existing_ids = get_existing_race_ids(engine)
    all_race_ids = set(df['race_id'].unique())
    new_race_ids = all_race_ids - existing_ids

    if not new_race_ids:
        logger.info("No new races to load (all already exist)")
        return set()

    logger.info(f"Found {len(new_race_ids):,} new races to load")

    # Filter to only new races
    df_new = df[df['race_id'].isin(new_race_ids)].copy()

    # Ensure schema exists
    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS raw"))

    # Load to database
    with engine.begin() as conn:
        df_new.to_sql(
            'race_details',
            con=conn,
            schema='raw',
            if_exists='append',
            index=False,
            method='multi',
            chunksize=5000
        )

    logger.info(f"✅ Loaded {len(df_new):,} new race details")
    return new_race_ids


def load_fis_results(csv_path, engine, race_ids_filter=None):
    """
    Load FIS results CSV into raw.fis_results table.

    Args:
        csv_path: Path to fis_results CSV file
        engine: SQLAlchemy engine
        race_ids_filter: Optional set of race_ids to filter to

    Returns:
        int: Number of results loaded
    """
    logger.info(f"Loading FIS results from {csv_path}...")

    # Read CSV
    df = pd.read_csv(csv_path)
    logger.info(f"Read {len(df):,} results from CSV")

    # Filter to specific race_ids if provided
    if race_ids_filter:
        df = df[df['race_id'].isin(race_ids_filter)].copy()
        logger.info(f"Filtered to {len(df):,} results for {len(race_ids_filter):,} new races")

    if df.empty:
        logger.info("No new results to load")
        return 0

    # Ensure schema exists
    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS raw"))

    # Load to database
    with engine.begin() as conn:
        df.to_sql(
            'fis_results',
            con=conn,
            schema='raw',
            if_exists='append',
            index=False,
            method='multi',
            chunksize=10000
        )

    logger.info(f"✅ Loaded {len(df):,} FIS results")
    return len(df)


def run_incremental_analytics(race_ids, modules=None):
    """
    Run incremental analytics updates for specific race_ids.

    Args:
        race_ids: Set or list of race_ids to update
        modules: Optional list of module paths to run (default: all incremental modules)

    Returns:
        bool: True if all modules succeeded
    """
    if not race_ids:
        logger.warning("No race_ids provided - skipping analytics update")
        return True

    # Convert to list and get date range for those races
    race_id_list = list(race_ids)
    logger.info(f"Running analytics for {len(race_id_list):,} races...")

    # Query to get date range for these races
    from database import fetch_dataframe
    race_ids_str = ','.join([str(r) for r in race_id_list])
    query = f"""
        SELECT MIN(date) as min_date, MAX(date) as max_date
        FROM raw.race_details
        WHERE race_id IN ({race_ids_str})
    """
    df = fetch_dataframe(query, database='raw')
    min_date = df['min_date'].iloc[0]
    max_date = df['max_date'].iloc[0]

    logger.info(f"Date range: {min_date} to {max_date}")

    # Default modules (in dependency order)
    if modules is None:
        modules = [
            'analytics/athlete/z_score.py',
            'analytics/athlete/strokes_gained.py',
        ]

    # Run each module
    import subprocess
    success_count = 0
    for module_path in modules:
        module_name = os.path.basename(module_path).replace('.py', '')
        logger.info(f"Running {module_name}...")

        try:
            result = subprocess.run(
                ['python3', module_path, '--incremental', '--from-date', str(min_date)],
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode == 0:
                logger.info(f"✅ {module_name} completed successfully")
                success_count += 1
            else:
                logger.error(f"❌ {module_name} failed")
                if result.stderr:
                    logger.error(result.stderr)
        except Exception as e:
            logger.error(f"❌ {module_name} failed with exception: {e}")

    total = len(modules)
    logger.info(f"Analytics complete: {success_count}/{total} modules succeeded")
    return success_count == total


def load_and_update_workflow(race_details_csv=None, results_csv=None,
                             race_ids_manual=None, skip_analytics=False):
    """
    Main workflow: Load raw data and run incremental analytics.

    Args:
        race_details_csv: Path to race details CSV
        results_csv: Path to FIS results CSV
        race_ids_manual: Manual list of race_ids to update analytics for
        skip_analytics: If True, only load data without running analytics

    Returns:
        bool: True if successful
    """
    start_time = datetime.now()
    logger.info("=" * 70)
    logger.info("LOAD AND UPDATE WORKFLOW")
    logger.info("=" * 70)

    engine = create_engine_connection()
    new_race_ids = set()

    try:
        # Step 1: Load race details (if provided)
        if race_details_csv:
            new_race_ids = load_race_details(race_details_csv, engine)

        # Step 2: Load FIS results (if provided)
        if results_csv:
            load_fis_results(results_csv, engine, race_ids_filter=new_race_ids if new_race_ids else None)

        # Step 3: Use manual race_ids if provided
        if race_ids_manual:
            new_race_ids = set(race_ids_manual)
            logger.info(f"Using manually specified race_ids: {len(new_race_ids):,} races")

        # Step 4: Run incremental analytics (unless skipped)
        if skip_analytics:
            logger.info("Skipping analytics update (--skip-analytics specified)")
        elif new_race_ids:
            logger.info("=" * 70)
            logger.info("RUNNING INCREMENTAL ANALYTICS")
            logger.info("=" * 70)
            run_incremental_analytics(new_race_ids)
        else:
            logger.info("No new races loaded - skipping analytics")

        # Summary
        duration = datetime.now() - start_time
        logger.info("=" * 70)
        logger.info("✅ LOAD AND UPDATE COMPLETE")
        logger.info(f"Duration: {duration}")
        logger.info(f"New races loaded: {len(new_race_ids):,}")
        logger.info("=" * 70)

        return True

    except Exception as e:
        logger.error(f"Workflow failed: {e}", exc_info=True)
        return False


def main():
    """Main entry point with CLI argument parsing."""
    parser = argparse.ArgumentParser(
        description='Load new race data and run incremental analytics',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Load CSVs and run analytics
  python3 load_and_update.py --race-details data/race_details.csv --results data/fis_results.csv

  # Load data only (skip analytics)
  python3 load_and_update.py --race-details data/race_details.csv --results data/fis_results.csv --skip-analytics

  # Run analytics for specific race IDs
  python3 load_and_update.py --race-ids 12345,12346,12347
        """
    )

    parser.add_argument(
        '--race-details',
        type=str,
        help='Path to race_details CSV file'
    )

    parser.add_argument(
        '--results',
        type=str,
        help='Path to fis_results CSV file'
    )

    parser.add_argument(
        '--race-ids',
        type=str,
        help='Comma-separated list of race_ids to update analytics for'
    )

    parser.add_argument(
        '--skip-analytics',
        action='store_true',
        help='Skip running analytics updates (only load data)'
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.race_details and not args.results and not args.race_ids:
        parser.error("Must provide --race-details, --results, or --race-ids")

    # Parse race_ids if provided
    race_ids_manual = None
    if args.race_ids:
        race_ids_manual = [int(x.strip()) for x in args.race_ids.split(',')]

    # Run workflow
    success = load_and_update_workflow(
        race_details_csv=args.race_details,
        results_csv=args.results,
        race_ids_manual=race_ids_manual,
        skip_analytics=args.skip_analytics
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
