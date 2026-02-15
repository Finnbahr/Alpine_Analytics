import sqlite3
import pandas as pd
from datetime import datetime

def load_raw_race_data():
    """
    Connect to the source databases and extract raw race data needed
    for computing the race-level z-score.
    """
    with sqlite3.connect("fis_results.db") as conn:
        conn.execute("ATTACH DATABASE 'fis_race_details.db' AS rd_db")
        query = """
        SELECT 
            fr.race_id,
            fr.fis_code,
            fr.name,
            fr.fis_points
        FROM fis_results fr
        JOIN rd_db.race_details rd ON fr.race_id = rd.race_id
        WHERE fr.fis_points IS NOT NULL
        """
        df = pd.read_sql_query(query, conn)
    return df

def compute_race_z_score(df):
    """
    Compute the race-level z-score for each competitor in each race.
    z-score is defined as: (mean(fis_points) - fis_points) / std(fis_points)
    For races with zero standard deviation, the z-score is set to 0.
    """
    # Convert fis_points to numeric.
    df['fis_points'] = pd.to_numeric(df['fis_points'], errors='coerce')
    
    # Compute the z-score within each race group.
    df['race_z_score'] = df.groupby('race_id')['fis_points'].transform(
        lambda x: (x.mean() - x) / x.std(ddof=0) if x.std(ddof=0) > 0 else 0
    )
    return df

def store_race_z_score(df):
    """
    Select only the essential columns and store the results in the aggregate database.
    The final table will have: race_id, fis_code, name, race_z_score.
    """
    result_df = df[['race_id', 'fis_code', 'name', 'race_z_score']]
    
    with sqlite3.connect("athlete_fis_information_aggregate.db") as conn:
        result_df.to_sql("race_z_score", conn, if_exists="replace", index=False)
        conn.commit()
    print("✅ 'race_z_score' table created with race_id, fis_code, name, and race_z_score.")

def update_race_z_score_etl():
    """
    ETL process: extract raw data, compute the z-score, and store the results.
    """
    df_raw = load_raw_race_data()
    df_with_z = compute_race_z_score(df_raw)
    store_race_z_score(df_with_z)

if __name__ == "__main__":
    update_race_z_score_etl()
