"""
Run Daily Incremental Update - Update Only New Races

This script runs incremental updates for all analytics modules, processing only
races added since the last update (or since a specified date).

Usage:
    python3 run_daily_update.py                     # Auto-detect new races
    python3 run_daily_update.py --from-date 2026-02-01  # Update from specific date
    python3 run_daily_update.py --days 7            # Update last 7 days

Advantages over full refresh:
- Much faster (minutes vs hours)
- Lower database load
- Can run daily without performance impact

Dependencies:
- Requires race_z_score module to support incremental mode
- Other modules will be updated incrementally as implemented
"""

import subprocess
import sys
import argparse
from datetime import datetime, timedelta
import logging
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Modules that support incremental updates (in dependency order)
# Phase 1: Foundation modules
INCREMENTAL_MODULES_PHASE1 = [
    ('analytics/athlete/z_score.py', 'Race Z-Score'),
    ('analytics/athlete/strokes_gained.py', 'Strokes Gained'),
]

# Phase 2: Modules that depend on Phase 1
# TODO: Add more modules as they're updated to support incremental mode
INCREMENTAL_MODULES_PHASE2 = [
    # ('analytics/athlete/hot_streak.py', 'Hot Streak'),
    # ('analytics/athlete/performance_tiers.py', 'Performance Tiers'),
]


def get_latest_race_date():
    """
    Query database to find the most recent race date.

    Returns:
        str: Date string (YYYY-MM-DD) of the most recent race
    """
    logger.info("Finding latest race date in database...")
    try:
        from database import fetch_dataframe
        query = "SELECT MAX(date) as latest FROM raw.race_details"
        df = fetch_dataframe(query, database='raw')
        latest = df['latest'].iloc[0]
        if latest:
            logger.info(f"Latest race in database: {latest}")
            return str(latest)
        else:
            logger.warning("No races found in database")
            return None
    except Exception as e:
        logger.error(f"Failed to query latest race date: {e}")
        return None


def run_module_incremental(module_path, module_name, from_date):
    """
    Run a single ETL module in incremental mode.

    Args:
        module_path: Path to the Python module
        module_name: Display name for the module
        from_date: Date string (YYYY-MM-DD) to process from

    Returns:
        bool: True if successful, False otherwise
    """
    logger.info(f"{'=' * 70}")
    logger.info(f"Running (incremental): {module_name}")
    logger.info(f"From date: {from_date}")
    logger.info(f"{'=' * 70}")

    try:
        result = subprocess.run(
            ['python3', module_path, '--incremental', '--from-date', from_date],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout per module
        )

        if result.returncode == 0:
            logger.info(f"✅ {module_name} completed successfully")
            # Print last few lines of output
            if result.stdout:
                lines = result.stdout.strip().split('\n')
                for line in lines[-5:]:
                    logger.info(f"   {line}")
            return True
        else:
            logger.error(f"❌ {module_name} failed with exit code {result.returncode}")
            if result.stderr:
                logger.error(f"Error output:\n{result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        logger.error(f"❌ {module_name} timed out after 5 minutes")
        return False
    except Exception as e:
        logger.error(f"❌ {module_name} failed with exception: {e}")
        return False


def run_daily_update(from_date=None, days=None):
    """
    Run incremental updates for all supported modules.

    Args:
        from_date: Optional date string (YYYY-MM-DD) to update from
        days: Optional number of days back to update from
    """
    start_time = datetime.now()

    logger.info(f"\n{'#' * 70}")
    logger.info(f"# DAILY INCREMENTAL UPDATE - STARTING AT {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"{'#' * 70}\n")

    # Determine from_date
    if days:
        from_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        logger.info(f"Updating last {days} days (from {from_date})")
    elif not from_date:
        # Auto-detect: update from latest race date in DB
        latest = get_latest_race_date()
        if latest:
            # Go back 1 day from latest to catch any updates to recent races
            from_date = (datetime.strptime(latest, '%Y-%m-%d') - timedelta(days=1)).strftime('%Y-%m-%d')
            logger.info(f"Auto-detected update from: {from_date}")
        else:
            logger.error("Could not determine from_date - aborting")
            return False

    # Run Phase 1 modules (foundation)
    logger.info(f"\n{'#' * 70}")
    logger.info(f"# PHASE 1: Foundation Modules")
    logger.info(f"{'#' * 70}\n")

    phase1_success = 0
    for module_path, module_name in INCREMENTAL_MODULES_PHASE1:
        if run_module_incremental(module_path, module_name, from_date):
            phase1_success += 1

    logger.info(f"\nPhase 1 Summary: {phase1_success}/{len(INCREMENTAL_MODULES_PHASE1)} modules succeeded\n")

    # Run Phase 2 modules (if any are implemented)
    if INCREMENTAL_MODULES_PHASE2:
        logger.info(f"\n{'#' * 70}")
        logger.info(f"# PHASE 2: Dependent Modules")
        logger.info(f"{'#' * 70}\n")

        phase2_success = 0
        for module_path, module_name in INCREMENTAL_MODULES_PHASE2:
            if run_module_incremental(module_path, module_name, from_date):
                phase2_success += 1

        logger.info(f"\nPhase 2 Summary: {phase2_success}/{len(INCREMENTAL_MODULES_PHASE2)} modules succeeded\n")
    else:
        logger.info("\nPhase 2: No modules implemented yet\n")
        phase2_success = 0

    # Final summary
    end_time = datetime.now()
    duration = end_time - start_time
    total_modules = len(INCREMENTAL_MODULES_PHASE1) + len(INCREMENTAL_MODULES_PHASE2)
    total_success = phase1_success + phase2_success

    logger.info(f"\n{'#' * 70}")
    logger.info(f"# DAILY INCREMENTAL UPDATE COMPLETE")
    logger.info(f"# Duration: {duration}")
    logger.info(f"# Success: {total_success}/{total_modules} modules")
    logger.info(f"# Updated data from: {from_date}")
    logger.info(f"{'#' * 70}\n")

    if total_success == total_modules:
        logger.info("🎉 All incremental updates completed successfully!")
        return True
    else:
        logger.warning(f"⚠️  {total_modules - total_success} module(s) failed")
        return False


def main():
    """
    Main entry point with CLI argument parsing.
    """
    parser = argparse.ArgumentParser(
        description='Run Daily Incremental ETL Updates',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 run_daily_update.py                    # Auto-detect new races
  python3 run_daily_update.py --from-date 2026-02-01  # Update from specific date
  python3 run_daily_update.py --days 7           # Update last 7 days
        """
    )

    parser.add_argument(
        '--from-date',
        type=str,
        help='Update races from this date forward (YYYY-MM-DD)'
    )

    parser.add_argument(
        '--days',
        type=int,
        help='Update races from last N days'
    )

    args = parser.parse_args()

    # Validate arguments
    if args.from_date and args.days:
        logger.error("Cannot specify both --from-date and --days")
        sys.exit(1)

    # Run daily update
    success = run_daily_update(from_date=args.from_date, days=args.days)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
