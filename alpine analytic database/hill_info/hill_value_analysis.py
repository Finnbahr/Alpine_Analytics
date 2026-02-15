import sqlite3
import pandas as pd
from datetime import datetime

def extract_race_data():
    conn = sqlite3.connect("fis_results.db")
    conn.execute("ATTACH DATABASE 'fis_race_details.db' AS rd_db")

    query = """
    SELECT 
        fr.fis_code,
        fr.name,
        fr.fis_points,
        fr.rank,
        rd.date,
        rd.location,
        rd.homologation_number,
        rd.discipline
    FROM fis_results fr
    JOIN rd_db.race_details rd ON fr.race_id = rd.race_id
    WHERE fr.fis_points IS NOT NULL
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def compute_hill_favorability(df):
    df['date'] = pd.to_datetime(df['date'])
    df['fis_points'] = pd.to_numeric(df['fis_points'], errors='coerce')
    df = df.sort_values(by=['fis_code', 'discipline', 'date'])

    # Calculate rolling average before each race
    def rolling_delta(group):
        group['prior_avg'] = group['fis_points'].expanding().mean().shift(1)
        group['performance_delta'] = group['prior_avg'] - group['fis_points']
        return group

    df = df.groupby(['fis_code', 'discipline'], group_keys=False).apply(rolling_delta)
    
    # Remove rows where we can't compute a prior average
    df = df[df['performance_delta'].notna()]

    # Group by hill and calculate average overperformance
    hill_group = (
        df.groupby(['location', 'homologation_number', 'discipline'])
          .agg(
              avg_performance_delta=('performance_delta', 'mean'),
              skier_count=('fis_code', 'count')
          )
          .reset_index()
    )

    hill_group['avg_performance_delta'] = hill_group['avg_performance_delta'].round(2)
    hill_group['last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return hill_group

def store_hill_favorability(df):
    conn = sqlite3.connect("event_fis_info_aggregate.db")
    df.to_sql("hill_favorability_analysis", conn, if_exists="replace", index=False)
    conn.commit()
    conn.close()
    print("✅ 'hill_favorability_analysis' table created in event_fis_info_aggregate.db.")

def update_hill_favorability_etl():
    df = extract_race_data()
    favorability_df = compute_hill_favorability(df)
    store_hill_favorability(favorability_df)

if __name__ == "__main__":
    update_hill_favorability_etl()
