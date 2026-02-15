import sqlite3
import pandas as pd
from datetime import datetime

def extract_race_data():
    """
    Extract raw race data from fis_results and fis_race_details.
    """
    with sqlite3.connect("fis_results.db") as conn:
        conn.execute("ATTACH DATABASE 'fis_race_details.db' AS rd_db")
        query = """
        SELECT 
            fr.race_id,
            fr.fis_code,
            fr.name,
            fr.fis_points,
            fr.rank,
            rd.date,
            rd.discipline
        FROM fis_results fr
        JOIN rd_db.race_details rd ON fr.race_id = rd.race_id
        WHERE fr.fis_points IS NOT NULL
        """
        df = pd.read_sql_query(query, conn)
    # Convert date column to datetime format.
    df['date'] = pd.to_datetime(df['date'])
    # Ensure fis_points is numeric.
    df['fis_points'] = pd.to_numeric(df['fis_points'], errors='coerce')
    return df

def merge_with_zscore(df):
    """
    Merge raw race data with the precomputed race_z_score using race_id and fis_code.
    """
    with sqlite3.connect("athlete_fis_information_aggregate.db") as conn:
        z_df = pd.read_sql_query("SELECT race_id, fis_code, race_z_score FROM race_z_score", conn)
    df = df.merge(z_df, on=['race_id', 'fis_code'], how='left')
    return df

def process_hot_streaks(df):
    """
    Calculate momentum metrics using EWMA and EW STD for both race_z_score and fis_points.
    
    For each athlete and discipline group:
      - Compute EWMA and EW STD of race_z_score and fis_points using a span of 3.
      - Calculate momentum as the standardized difference from the EWMA.
    """
    # Merge in the precomputed race_z_score.
    df = merge_with_zscore(df)
    df['race_z_score'] = pd.to_numeric(df['race_z_score'], errors='coerce')
    
    # Sort data by athlete, discipline, and date.
    df = df.sort_values(by=['fis_code', 'discipline', 'date'])
    
    # Calculate momentum metrics for race_z_score.
    df['ewma_race_z'] = df.groupby(['fis_code', 'discipline'])['race_z_score'].transform(
        lambda x: x.ewm(span=3, adjust=False).mean()
    )
    df['ewstd_race_z'] = df.groupby(['fis_code', 'discipline'])['race_z_score'].transform(
        lambda x: x.ewm(span=3, adjust=False).std()
    )
    df['momentum_z'] = (df['race_z_score'] - df['ewma_race_z']) / df['ewstd_race_z']
    
    # Calculate momentum metrics for raw fis_points.
    df['ewma_fis'] = df.groupby(['fis_code', 'discipline'])['fis_points'].transform(
        lambda x: x.ewm(span=3, adjust=False).mean()
    )
    df['ewstd_fis'] = df.groupby(['fis_code', 'discipline'])['fis_points'].transform(
        lambda x: x.ewm(span=3, adjust=False).std()
    )
    df['momentum_fis'] = (df['fis_points'] - df['ewma_fis']) / df['ewstd_fis']
    
    # Also compute a simple rolling average of race_z_score as an additional metric.
    df['rolling_race_z'] = df.groupby(['fis_code', 'discipline'])['race_z_score'].transform(
        lambda x: x.rolling(window=3, min_periods=3).mean()
    )
    
    # Add timestamp and race count for tracking.
    df['last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    df['race_count'] = df.groupby(['fis_code', 'discipline'])['fis_points'].transform('count')
    
    # Return only rows where both momentum metrics are computed.
    return df[df['momentum_z'].notna() & df['momentum_fis'].notna()].copy()

def store_hot_streaks(df):
    """
    Store the hot streak and momentum metrics into the aggregate database.
    """
    with sqlite3.connect("athlete_fis_information_aggregate.db") as conn:
        df.to_sql("hot_streaks", conn, if_exists="replace", index=False)
        conn.commit()
    print("✅ 'hot_streaks' table updated with momentum metrics for both race z-scores and fis_points.")

def update_hot_streaks_etl():
    df = extract_race_data()
    hot_df = process_hot_streaks(df)
    store_hot_streaks(hot_df)

if __name__ == "__main__":
    update_hot_streaks_etl()
