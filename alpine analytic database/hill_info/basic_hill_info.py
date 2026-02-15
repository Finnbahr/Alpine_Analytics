import sqlite3
import pandas as pd
import math
import numpy as np
from datetime import datetime
import logging

# ---------------------------
# Configuration Parameters
# ---------------------------
RAW_DB = "fis_results.db"
DETAILS_DB = "fis_race_details.db"
AGG_DB = "event_fis_info_aggregate.db"
OUTPUT_TABLE = "basic_hill_info"
ROUND_PRECISION = 2
ETL_VERSION = "v1.1"

# ---------------------------
# Logging Configuration
# ---------------------------
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# ---------------------------
# Helper Function
# ---------------------------
def time_to_seconds(time_str):
    """
    Convert a race time string (e.g. "1:12.34" or "12.34") to total seconds as a float.
    Returns None if input is empty or cannot be converted.
    """
    try:
        if not time_str or time_str.strip() == "":
            return None
        time_str = time_str.strip()
        if ':' in time_str:
            parts = time_str.split(':')
            minutes = float(parts[0])
            seconds = float(parts[1])
            return minutes * 60 + seconds
        else:
            return float(time_str)
    except Exception as e:
        logging.error("Error converting time '%s': %s", time_str, e)
        return None

# ---------------------------
# Data Extraction
# ---------------------------
def extract_race_data(raw_db=RAW_DB, details_db=DETAILS_DB):
    """
    Connect to the raw databases (fis_results.db and fis_race_details.db)
    and extract race-level data.
    Returns a DataFrame with key fields.
    """
    try:
        conn = sqlite3.connect(raw_db)
        conn.execute(f"ATTACH DATABASE '{details_db}' AS rd_db")
        conn.create_function("time_to_sec", 1, time_to_seconds)
        query = """
        WITH race_data AS (
          SELECT 
            rd.race_id,
            rd.location,
            rd.country,
            rd.discipline,
            rd.homologation_number,
            CAST(rd.vertical_drop AS REAL) AS vertical_drop,
            CAST(rd.start_altitude AS REAL) AS start_altitude,
            CAST(rd.first_run_number_of_gates AS REAL) AS gate_count,
            (SELECT time_to_sec(final_time)
             FROM fis_results 
             WHERE race_id = rd.race_id AND rank = '1'
             LIMIT 1) / 60.0 AS winning_time_min,
            (SELECT CAST(fis_points AS REAL)
             FROM fis_results 
             WHERE race_id = rd.race_id AND rank = '1'
             LIMIT 1) AS winning_fis_points,
            (SELECT AVG(CASE WHEN rank IN ('DNF1','DSQ1','DNF','DSQ','DNF2','DSQ2') THEN 1.0 ELSE 0 END)
             FROM fis_results 
             WHERE race_id = rd.race_id) AS dnf_rate,
            (SELECT COUNT(*) FROM fis_results WHERE race_id = rd.race_id) AS starters_count
          FROM rd_db.race_details rd
          WHERE EXISTS (
            SELECT 1 FROM fis_results 
            WHERE race_id = rd.race_id AND rank = '1'
          )
        )
        SELECT * FROM race_data;
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        logging.info("Race data extracted successfully.")
        return df
    except Exception as e:
        logging.error("Error extracting race data: %s", e)
        raise

# ---------------------------
# Data Aggregation & Enhanced Metrics
# ---------------------------
def aggregate_basic_hill_info(df, precision=ROUND_PRECISION):
    """
    Group the race-level data by location, homologation_number, discipline, and country.
    Compute summary statistics for each group and add additional metrics:
      - Calculate min, max, mean, median, std, and coefficient of variation (CV) for selected numeric fields.
    Returns a DataFrame ready for loading.
    """
    try:
        agg = df.groupby(["location", "homologation_number", "discipline", "country"]).agg(
            race_count = pd.NamedAgg(column="race_id", aggfunc="count"),
            # Vertical drop
            min_vertical_drop = pd.NamedAgg(column="vertical_drop", aggfunc="min"),
            max_vertical_drop = pd.NamedAgg(column="vertical_drop", aggfunc="max"),
            mean_vertical_drop = pd.NamedAgg(column="vertical_drop", aggfunc="mean"),
            median_vertical_drop = pd.NamedAgg(column="vertical_drop", aggfunc="median"),
            std_vertical_drop = pd.NamedAgg(column="vertical_drop", aggfunc="std"),
            cv_vertical_drop = pd.NamedAgg(column="vertical_drop", aggfunc=lambda x: np.round(x.std()/x.mean(), 2) if x.mean() != 0 else None),
            # Starting altitude
            min_start_altitude = pd.NamedAgg(column="start_altitude", aggfunc="min"),
            max_start_altitude = pd.NamedAgg(column="start_altitude", aggfunc="max"),
            mean_start_altitude = pd.NamedAgg(column="start_altitude", aggfunc="mean"),
            median_start_altitude = pd.NamedAgg(column="start_altitude", aggfunc="median"),
            std_start_altitude = pd.NamedAgg(column="start_altitude", aggfunc="std"),
            cv_start_altitude = pd.NamedAgg(column="start_altitude", aggfunc=lambda x: np.round(x.std()/x.mean(), 2) if x.mean() != 0 else None),
            # Gate count
            min_gate_count = pd.NamedAgg(column="gate_count", aggfunc="min"),
            max_gate_count = pd.NamedAgg(column="gate_count", aggfunc="max"),
            mean_gate_count = pd.NamedAgg(column="gate_count", aggfunc="mean"),
            median_gate_count = pd.NamedAgg(column="gate_count", aggfunc="median"),
            std_gate_count = pd.NamedAgg(column="gate_count", aggfunc="std"),
            cv_gate_count = pd.NamedAgg(column="gate_count", aggfunc=lambda x: np.round(x.std()/x.mean(), 2) if x.mean() != 0 else None),
            # Winning time (in minutes; for the winner only)
            min_winning_time = pd.NamedAgg(column="winning_time_min", aggfunc="min"),
            max_winning_time = pd.NamedAgg(column="winning_time_min", aggfunc="max"),
            mean_winning_time = pd.NamedAgg(column="winning_time_min", aggfunc="mean"),
            median_winning_time = pd.NamedAgg(column="winning_time_min", aggfunc="median"),
            std_winning_time = pd.NamedAgg(column="winning_time_min", aggfunc="std"),
            cv_winning_time = pd.NamedAgg(column="winning_time_min", aggfunc=lambda x: np.round(x.std()/x.mean(), 2) if x.mean() != 0 else None),
            # Winning fis points (for the winner only)
            min_fis_points = pd.NamedAgg(column="winning_fis_points", aggfunc="min"),
            max_fis_points = pd.NamedAgg(column="winning_fis_points", aggfunc="max"),
            mean_fis_points = pd.NamedAgg(column="winning_fis_points", aggfunc="mean"),
            median_fis_points = pd.NamedAgg(column="winning_fis_points", aggfunc="median"),
            std_fis_points = pd.NamedAgg(column="winning_fis_points", aggfunc="std"),
            cv_fis_points = pd.NamedAgg(column="winning_fis_points", aggfunc=lambda x: np.round(x.std()/x.mean(), 2) if x.mean() != 0 else None),
            # DNF rate
            min_dnf_rate = pd.NamedAgg(column="dnf_rate", aggfunc="min"),
            max_dnf_rate = pd.NamedAgg(column="dnf_rate", aggfunc="max"),
            mean_dnf_rate = pd.NamedAgg(column="dnf_rate", aggfunc="mean"),
            median_dnf_rate = pd.NamedAgg(column="dnf_rate", aggfunc="median"),
            std_dnf_rate = pd.NamedAgg(column="dnf_rate", aggfunc="std"),
            cv_dnf_rate = pd.NamedAgg(column="dnf_rate", aggfunc=lambda x: np.round(x.std()/x.mean(), 2) if x.mean() != 0 else None),
            # Starters count
            min_starters = pd.NamedAgg(column="starters_count", aggfunc="min"),
            max_starters = pd.NamedAgg(column="starters_count", aggfunc="max"),
            mean_starters = pd.NamedAgg(column="starters_count", aggfunc="mean"),
            median_starters = pd.NamedAgg(column="starters_count", aggfunc="median"),
            std_starters = pd.NamedAgg(column="starters_count", aggfunc="std"),
            cv_starters = pd.NamedAgg(column="starters_count", aggfunc=lambda x: np.round(x.std()/x.mean(), 2) if x.mean() != 0 else None)
        ).reset_index()
        
        # Round all numeric columns to specified precision.
        numeric_cols = agg.select_dtypes(include=['float64', 'int64']).columns
        agg[numeric_cols] = agg[numeric_cols].round(precision)
        
        # Add ETL version and timestamp.
        agg['etl_version'] = ETL_VERSION
        agg['last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        logging.info("Basic hill info aggregated successfully.")
        return agg
    except Exception as e:
        logging.error("Error during aggregation: %s", e)
        raise

# ---------------------------
# Data Storage
# ---------------------------
def store_basic_hill_info(df, agg_db=AGG_DB, output_table=OUTPUT_TABLE):
    """
    Connect to the aggregate database and store the aggregated DataFrame into a table.
    """
    try:
        conn = sqlite3.connect(agg_db)
        df.to_sql(output_table, conn, if_exists="replace", index=False)
        conn.commit()
        conn.close()
        logging.info("Basic hill info stored successfully in table '%s' in database '%s'.", output_table, agg_db)
    except Exception as e:
        logging.error("Error storing basic hill info: %s", e)
        raise

# ---------------------------
# Main Execution
# ---------------------------
def update_basic_hill_info():
    """
    Main ETL process: Extract raw race data, aggregate basic hill info with enhanced metrics,
    and store the results in the aggregate database.
    """
    try:
        df_raw = extract_race_data()
        df_agg = aggregate_basic_hill_info(df_raw)
        store_basic_hill_info(df_agg)
        logging.info("ETL process completed successfully.")
    except Exception as e:
        logging.error("ETL process failed: %s", e)
        raise

if __name__ == '__main__':
    update_basic_hill_info()
