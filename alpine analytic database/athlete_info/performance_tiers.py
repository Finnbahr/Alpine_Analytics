import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime

def extract_race_data():
    """
    Connect to fis_results.db and attach fis_race_details.db,
    then extract fields needed for performance tiers aggregation.
    """
    with sqlite3.connect("fis_results.db") as conn:
        conn.execute("ATTACH DATABASE 'fis_race_details.db' AS rd_db")
        query = """
        SELECT 
          fr.fis_code,
          fr.name,
          fr.fis_points,
          rd.date,
          rd.discipline
        FROM fis_results fr
        JOIN rd_db.race_details rd ON fr.race_id = rd.race_id
        WHERE fr.fis_points IS NOT NULL
        """
        df = pd.read_sql_query(query, conn)
    df['date'] = pd.to_datetime(df['date'])
    return df

def assign_performance_tiers(df):
    """
    Calculate career performance tiers on a logarithmic scale.
    For each athlete (grouped by fis_code, name, discipline, and year):
      - Compute the average FIS points.
      - Apply a natural logarithm transformation to average FIS points.
      - Rank these log-transformed values to get a percentile.
      - Use pd.cut to assign tiers based on percentile bins.
    """
    df['fis_points'] = pd.to_numeric(df['fis_points'], errors='coerce')
    df = df.dropna(subset=['fis_points'])
    
    # Aggregate average FIS points per athlete, discipline, and year.
    grouped = (
        df.groupby(['fis_code', 'name', 'discipline', df['date'].dt.year.rename('year')])
          .agg(
              race_count=('fis_points', 'count'),
              avg_fis_points=('fis_points', 'mean')
          )
          .reset_index()
    )
    
    # Apply logarithmic transformation.
    grouped['log_avg_fis_points'] = np.log(grouped['avg_fis_points'])
    
    # Rank the log-transformed values and get the percentile.
    grouped['tier_percentile'] = grouped['log_avg_fis_points'].rank(pct=True)
    
    # Assign tiers based on the percentile.
    grouped['tier'] = pd.cut(
        grouped['tier_percentile'],
        bins=[0, 0.1, 0.3, 0.7, 1.0],
        labels=["Tier 1 (Elite)", "Tier 2 (Contender)", "Tier 3 (Middle Pack)", "Tier 4 (Developing)"]
    )
    
    grouped['last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return grouped.drop(columns='tier_percentile')

def store_performance_tiers(df):
    """
    Store the performance tiers DataFrame into the aggregate database.
    """
    with sqlite3.connect("athlete_fis_information_aggregate.db") as conn:
        df.to_sql("performance_tiers", conn, if_exists="replace", index=False)
        conn.commit()
    print("✅ 'performance_tiers' table created in athlete_fis_information_aggregate.db.")

def update_performance_tiers_etl():
    df = extract_race_data()
    tiered_df = assign_performance_tiers(df)
    store_performance_tiers(tiered_df)

if __name__ == "__main__":
    update_performance_tiers_etl()
