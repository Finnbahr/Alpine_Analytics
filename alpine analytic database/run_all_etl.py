"""
Run All ETL Pipelines - Complete Data Refresh

This script runs all analytics ETL pipelines in the correct dependency order.
Use this to refresh all analytics tables from the raw data.

Usage:
    python3 run_all_etl.py                    # Run all modules
    python3 run_all_etl.py --phase 1          # Run only Phase 1
    python3 run_all_etl.py --module z_score   # Run specific module

Dependency Order:
    Phase 1 (Foundation) → Phase 2 (First-level) → Phase 3 (Advanced)
"""

import subprocess
import sys
import argparse
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define all modules in dependency order
MODULES = {
    'phase1': [
        ('analytics/athlete/z_score.py', 'Race Z-Score'),
        ('analytics/athlete/performance_tiers.py', 'Performance Tiers'),
        ('analytics/course/basic_stats.py', 'Course Basic Stats'),
        ('analytics/course/difficulty_index.py', 'Hill Difficulty Index'),
    ],
    'phase2': [
        ('analytics/athlete/strokes_gained.py', 'Strokes Gained'),
        ('analytics/athlete/strokes_gained_bib.py', 'Strokes Gained (Bib-Relative)'),
        ('analytics/athlete/hot_streak.py', 'Hot Streak'),
        ('analytics/athlete/basic_stats.py', 'Basic Athlete Stats'),
        ('analytics/athlete/consistency.py', 'Performance Consistency'),
        ('analytics/athlete/top_performances.py', 'Top Performances'),
    ],
    'phase3': [
        # Course modules
        ('analytics/course/location_performance.py', 'Location Performance'),
        ('analytics/course/favorability.py', 'Course Favorability'),
        ('analytics/course/best_courses.py', 'Best Courses'),
        ('analytics/course/similar_courses.py', 'Similar Courses'),
        ('analytics/course/bib_location_performance.py', 'Bib Location Performance'),
        # Athlete modules
        ('analytics/athlete/course_regression.py', 'Course Regression'),
        ('analytics/athlete/course_traits.py', 'Course Traits'),
        # World Cup modules
        ('analytics/worldcup/home_advantage.py', 'Home Advantage'),
        ('analytics/worldcup/setter_advantage.py', 'Setter Advantage'),
    ]
}


def run_module(module_path, module_name):
    """
    Run a single ETL module.

    Args:
        module_path: Path to the Python module
        module_name: Display name for the module

    Returns:
        bool: True if successful, False otherwise
    """
    logger.info(f"{'=' * 70}")
    logger.info(f"Running: {module_name}")
    logger.info(f"Module: {module_path}")
    logger.info(f"{'=' * 70}")

    try:
        result = subprocess.run(
            ['python3', module_path],
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout per module
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
        logger.error(f"❌ {module_name} timed out after 10 minutes")
        return False
    except Exception as e:
        logger.error(f"❌ {module_name} failed with exception: {e}")
        return False


def run_phase(phase_name):
    """
    Run all modules in a specific phase.

    Args:
        phase_name: Phase name (phase1, phase2, phase3)

    Returns:
        tuple: (success_count, total_count)
    """
    if phase_name not in MODULES:
        logger.error(f"Unknown phase: {phase_name}")
        return 0, 0

    modules = MODULES[phase_name]
    success_count = 0

    logger.info(f"\n{'#' * 70}")
    logger.info(f"# STARTING {phase_name.upper()}: {len(modules)} modules")
    logger.info(f"{'#' * 70}\n")

    for module_path, module_name in modules:
        if run_module(module_path, module_name):
            success_count += 1
        else:
            logger.warning(f"⚠️  Continuing despite failure in {module_name}")

    logger.info(f"\n{phase_name.upper()} Summary: {success_count}/{len(modules)} modules succeeded\n")

    return success_count, len(modules)


def run_all():
    """
    Run all ETL modules in all phases.

    Returns:
        bool: True if all modules succeeded, False otherwise
    """
    start_time = datetime.now()
    logger.info(f"\n{'#' * 70}")
    logger.info(f"# FULL ETL PIPELINE - STARTING AT {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"{'#' * 70}\n")

    total_success = 0
    total_modules = 0

    # Run each phase in order
    for phase in ['phase1', 'phase2', 'phase3']:
        success, total = run_phase(phase)
        total_success += success
        total_modules += total

    end_time = datetime.now()
    duration = end_time - start_time

    logger.info(f"\n{'#' * 70}")
    logger.info(f"# FULL ETL PIPELINE COMPLETE")
    logger.info(f"# Duration: {duration}")
    logger.info(f"# Success: {total_success}/{total_modules} modules")
    logger.info(f"{'#' * 70}\n")

    if total_success == total_modules:
        logger.info("🎉 All modules completed successfully!")
        return True
    else:
        logger.warning(f"⚠️  {total_modules - total_success} module(s) failed")
        return False


def main():
    """
    Main entry point with CLI argument parsing.
    """
    parser = argparse.ArgumentParser(
        description='Run FIS Alpine Analytics ETL Pipelines',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 run_all_etl.py                    # Run all modules
  python3 run_all_etl.py --phase 1          # Run Phase 1 only
  python3 run_all_etl.py --phase 2          # Run Phase 2 only
  python3 run_all_etl.py --module z_score   # Run specific module
        """
    )

    parser.add_argument(
        '--phase',
        type=int,
        choices=[1, 2, 3],
        help='Run specific phase only (1, 2, or 3)'
    )

    parser.add_argument(
        '--module',
        type=str,
        help='Run specific module by name (e.g., z_score, hot_streak)'
    )

    args = parser.parse_args()

    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()

    # Run based on arguments
    if args.module:
        # Find and run specific module
        module_found = False
        for phase_modules in MODULES.values():
            for module_path, module_name in phase_modules:
                if args.module in module_path:
                    run_module(module_path, module_name)
                    module_found = True
                    break
            if module_found:
                break
        if not module_found:
            logger.error(f"Module '{args.module}' not found")
            sys.exit(1)

    elif args.phase:
        # Run specific phase
        phase_name = f'phase{args.phase}'
        success, total = run_phase(phase_name)
        sys.exit(0 if success == total else 1)

    else:
        # Run all phases
        success = run_all()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
