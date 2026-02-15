import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime
import logging

# Set up basic logging.
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def extract_race_data(db_path='fis_results.db', details_db='fis_race_details.db'):
    try:
        conn = sqlite3.connect(db_path)
        conn.execute(f"ATTACH DATABASE '{details_db}' AS rd_db")
        query = """
        SELECT 
            fr.fis_code,
            fr.name,
            fr.fis_points,
            fr.rank,
            rd.date,
            rd.location,
            rd.country,
            rd.homologation_number,
            rd.discipline
        FROM fis_results fr
        JOIN rd_db.race_details rd ON fr.race_id = rd.race_id
        WHERE fr.fis_points IS NOT NULL
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        logging.info("Race data extracted successfully.")
        return df
    except Exception as e:
        logging.error("Error extracting race data: %s", e)
        raise

def compute_hill_favorability(df, min_skier_count=10, ci_multiplier=1.96):
    try:
        df['date'] = pd.to_datetime(df['date'])
        df['fis_points'] = pd.to_numeric(df['fis_points'], errors='coerce')
        df = df.sort_values(by=['fis_code', 'discipline', 'date'])
        
        # Calculate rolling prior average and performance delta for each skier.
        def rolling_delta(group):
            group['prior_avg'] = group['fis_points'].expanding().mean().shift(1)
            group['performance_delta'] = group['prior_avg'] - group['fis_points']
            return group
        
        df = df.groupby(['fis_code', 'discipline'], group_keys=False).apply(rolling_delta)
        df = df[df['performance_delta'].notna()]
        
        # Group by hill (location, country, homologation_number, discipline)
        hill_group = (
            df.groupby(['location', 'country', 'homologation_number', 'discipline'])
              .agg(
                  avg_performance_delta=('performance_delta', 'mean'),
                  std_performance_delta=('performance_delta', 'std'),
                  skier_count=('fis_code', 'count')
              )
              .reset_index()
        )
        
        # Filter out hills with too few racers.
        hill_group = hill_group[hill_group['skier_count'] >= min_skier_count]
        
        # Calculate 95% confidence intervals.
        hill_group['ci_lower'] = hill_group['avg_performance_delta'] - ci_multiplier * (hill_group['std_performance_delta'] / np.sqrt(hill_group['skier_count']))
        hill_group['ci_upper'] = hill_group['avg_performance_delta'] + ci_multiplier * (hill_group['std_performance_delta'] / np.sqrt(hill_group['skier_count']))
        
        # Round key metrics.
        for col in ['avg_performance_delta', 'std_performance_delta', 'ci_lower', 'ci_upper']:
            hill_group[col] = hill_group[col].round(3)
        
        hill_group['last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logging.info("Hill favorability metrics computed successfully.")
        return hill_group
    except Exception as e:
        logging.error("Error computing hill favorability: %s", e)
        raise

def store_hill_favorability(df, output_db='event_fis_info_aggregate.db'):
    try:
        conn = sqlite3.connect(output_db)
        df.to_sql("hill_favorability_analysis", conn, if_exists="replace", index=False)
        conn.commit()
        conn.close()
        logging.info("Hill favorability analysis stored successfully.")
    except Exception as e:
        logging.error("Error storing hill favorability: %s", e)
        raise

def update_hill_favorability_etl():
    df = extract_race_data()
    favorability_df = compute_hill_favorability(df)
    store_hill_favorability(favorability_df)

if __name__ == "__main__":
    update_hill_favorability_etl()
