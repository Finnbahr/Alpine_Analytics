import sqlite3
import pandas as pd
import math
import numpy as np
from datetime import datetime
import logging

# ---------------------------
# Configuration Parameters
# ---------------------------
# Weights for the Hill Difficulty Index (HDI) calculation.
WEIGHT_WINNING_TIME = 0.20
WEIGHT_GATE_COUNT   = 0.10
WEIGHT_START_ALT    = 0.10
WEIGHT_VERTICAL_DROP= 0.20
WEIGHT_DNF_RATE     = 0.40

# Quantile thresholds for normalization.
LOWER_QUANTILE = 0.05
UPPER_QUANTILE = 0.95

# ---------------------------
# Logging Configuration
# ---------------------------
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# ---------------------------
# Helper Functions
# ---------------------------
def time_to_seconds(time_str):
    """
    Convert a race time string (e.g. "1:12.34" or "12.34") to total seconds as a float.
    If the string is empty or only whitespace, return None.
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

def normalize_series(s, lower_quantile=LOWER_QUANTILE, upper_quantile=UPPER_QUANTILE):
    """
    Clip the series to the specified quantiles and normalize to a 0-100 scale.
    """
    try:
        low = s.quantile(lower_quantile)
        high = s.quantile(upper_quantile)
        s_clipped = s.clip(lower=low, upper=high)
        if high - low > 0:
            return 100 * (s_clipped - low) / (high - low)
        else:
            return pd.Series(50, index=s.index)
    except Exception as e:
        logging.error("Error normalizing series: %s", e)
        return s

def minutes_to_time_str(minutes):
    """
    Convert decimal minutes to "m:ss.xx" format.
    """
    if minutes is None or (isinstance(minutes, float) and math.isnan(minutes)):
        return ""
    total_seconds = minutes * 60
    m = int(total_seconds // 60)
    s = total_seconds - m * 60
    return f"{m}:{s:05.2f}"

# ---------------------------
# Step 1: Extract & Aggregate Raw Data
# ---------------------------
# SQL query to aggregate hill metrics from raw data.
QUERY = """
WITH race_metrics AS (
  SELECT 
    rd.race_id,
    rd.location,
    rd.country,
    rd.discipline,
    rd.homologation_number,
    rd.start_altitude,
    -- Convert winning time (from the first-place finisher) to minutes.
    (SELECT time_to_sec(final_time)
     FROM fis_results 
     WHERE race_id = rd.race_id AND rank = '1'
     LIMIT 1) / 60.0 AS winning_time_min,
    CAST(rd.first_run_number_of_gates AS REAL) AS gate_count,
    CAST(rd.vertical_drop AS REAL) AS vertical_drop,
    -- Calculate DNF rate for the race.
    (SELECT AVG(CASE WHEN rank IN ('DNF1','DSQ1','DNF','DSQ','DNF2','DSQ2') THEN 1.0 ELSE 0 END)
     FROM fis_results 
     WHERE race_id = rd.race_id) AS dnf_rate
  FROM rd_db.race_details rd
  WHERE EXISTS (
    SELECT 1 FROM fis_results 
    WHERE race_id = rd.race_id AND rank = '1'
  )
)
SELECT 
  location,
  country,
  discipline,
  homologation_number,
  COUNT(*) AS race_count,
  AVG(winning_time_min) AS avg_winning_time_min,
  AVG(gate_count) AS avg_gate_count,
  AVG(start_altitude) AS avg_start_altitude,
  AVG(vertical_drop) AS avg_vertical_drop,
  AVG(dnf_rate) AS avg_dnf_rate
FROM race_metrics
GROUP BY location, country, discipline, homologation_number
ORDER BY location, country, discipline, homologation_number;
"""

def extract_raw_metrics(db_path="fis_results.db", details_db="fis_race_details.db"):
    """
    Connect to the raw database (fis_results.db), attach fis_race_details.db, register helper functions,
    execute the query, and load the results into a DataFrame.
    """
    try:
        conn = sqlite3.connect(db_path)
        conn.execute(f"ATTACH DATABASE '{details_db}' AS rd_db")
        conn.create_function("time_to_sec", 1, time_to_seconds)
        df = pd.read_sql_query(QUERY, conn)
        conn.close()
        logging.info("Raw metrics extracted successfully.")
        return df
    except Exception as e:
        logging.error("Error extracting raw metrics: %s", e)
        raise

# ---------------------------
# Step 2: Compute Normalized Metrics and HDI
# ---------------------------
def compute_hdi(df,
                weight_wt=WEIGHT_WINNING_TIME,
                weight_gate=WEIGHT_GATE_COUNT,
                weight_start=WEIGHT_START_ALT,
                weight_vdrop=WEIGHT_VERTICAL_DROP,
                weight_dnf=WEIGHT_DNF_RATE):
    """
    Normalize hill metrics within each discipline and compute Hill Difficulty Index (HDI).
    
    Parameters:
      - df: DataFrame with raw aggregated metrics.
      - weight_wt: Weight for winning time.
      - weight_gate: Weight for gate count.
      - weight_start: Weight for starting altitude.
      - weight_vdrop: Weight for vertical drop.
      - weight_dnf: Weight for DNF rate.
    
    Returns:
      DataFrame with normalized metrics and computed HDI.
    """
    try:
        # Normalize each metric within each discipline.
        df['winning_time_norm'] = df.groupby('discipline')['avg_winning_time_min'].transform(normalize_series)
        df['gate_count_norm'] = df.groupby('discipline')['avg_gate_count'].transform(normalize_series)
        df['start_altitude_norm'] = df.groupby('discipline')['avg_start_altitude'].transform(normalize_series)
        df['vertical_drop_norm'] = df.groupby('discipline')['avg_vertical_drop'].transform(normalize_series)
        df['dnf_rate_norm'] = df.groupby('discipline')['avg_dnf_rate'].transform(normalize_series)
        
        # Round normalized columns to 2 decimals.
        for col in ['winning_time_norm', 'gate_count_norm', 'start_altitude_norm', 'vertical_drop_norm', 'dnf_rate_norm']:
            df[col] = df[col].round(2)
        
        # Compute Hill Difficulty Index (HDI) using the provided weights.
        df['hill_difficulty_index'] = (
            weight_wt * df['winning_time_norm'] +
            weight_gate * df['gate_count_norm'] +
            weight_start * df['start_altitude_norm'] +
            weight_vdrop * df['vertical_drop_norm'] +
            weight_dnf * df['dnf_rate_norm']
        ).round(2)
        
        # Convert avg_winning_time_min to formatted time string.
        df['avg_winning_time'] = df['avg_winning_time_min'].apply(minutes_to_time_str)
        
        # Round the raw average metrics.
        for col in ['avg_gate_count', 'avg_start_altitude', 'avg_vertical_drop', 'avg_dnf_rate']:
            df[col] = df[col].round(2)
        
        # Select desired columns.
        desired_columns = [
            'location', 
            'country', 
            'discipline', 
            'homologation_number', 
            'race_count', 
            'avg_winning_time', 
            'winning_time_norm',
            'avg_gate_count', 
            'gate_count_norm',
            'avg_start_altitude', 
            'start_altitude_norm',
            'avg_vertical_drop', 
            'vertical_drop_norm',
            'avg_dnf_rate', 
            'dnf_rate_norm',
            'hill_difficulty_index'
        ]
        logging.info("HDI computed successfully.")
        return df[desired_columns]
    except Exception as e:
        logging.error("Error computing HDI: %s", e)
        raise

# ---------------------------
# Step 3: Load the HDI Table into the Aggregate Database
# ---------------------------
def update_hdi_table(db_output="event_fis_info_aggregate.db"):
    """
    Extract raw metrics, compute normalized metrics and HDI, add timestamp, and store the HDI table into the aggregate database.
    """
    try:
        df_raw = extract_raw_metrics()
        df_hdi = compute_hdi(df_raw)
        df_hdi['last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        conn = sqlite3.connect(db_output)
        df_hdi.to_sql("hdi", conn, if_exists="replace", index=False)
        conn.commit()
        conn.close()
        
        logging.info("HDI table updated successfully in '%s' at %s.", db_output, datetime.now())
    except Exception as e:
        logging.error("Error updating HDI table: %s", e)
        raise

# ---------------------------
# Main Execution
# ---------------------------
if __name__ == '__main__':
    update_hdi_table()
