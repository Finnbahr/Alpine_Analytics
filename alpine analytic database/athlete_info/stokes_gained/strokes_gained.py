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
            rd.date,
            rd.location,
            rd.homologation_number,
            rd.discipline
        FROM fis_results fr
        JOIN rd_db.race_details rd ON fr.race_id = rd.race_id
        WHERE fr.fis_points IS NOT NULL
        """
        df = pd.read_sql_query(query, conn)
    # Ensure date is datetime and fis_points is numeric.
    df['date'] = pd.to_datetime(df['date'])
    df['fis_points'] = pd.to_numeric(df['fis_points'], errors='coerce')
    return df

def compute_strokes_gained(df):
    """
    Compute strokes gained performance metrics.
      - Calculate the average FIS points per race.
      - Compute points gained: the difference between the race average and the competitor's FIS points.
      - Join with the precomputed race_z_score (matched on race_id and fis_code) rather than recalculating it.
      - Append a timestamp.
    """
    # Calculate average FIS points per race.
    race_avg = (
        df.groupby('race_id')
          .agg(avg_fis_points=('fis_points', 'mean'))
          .reset_index()
    )
    # Merge the race average back into the main DataFrame.
    df = df.merge(race_avg, on='race_id', how='left')
    # Compute points gained: how much better the competitor did than the average.
    df['points_gained'] = df['avg_fis_points'] - df['fis_points']
    
    # Instead of recalculating race_z_score, join the precomputed value.
    with sqlite3.connect("athlete_fis_information_aggregate.db") as conn:
        z_df = pd.read_sql_query(
            "SELECT race_id, fis_code, race_z_score FROM race_z_score", conn)
    df = df.merge(z_df, on=['race_id', 'fis_code'], how='left')
    
    # Add a timestamp.
    df['last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    return df

def store_strokes_gained(df):
    """
    Store the strokes gained performance metrics into the aggregate database.
    """
    with sqlite3.connect("athlete_fis_information_aggregate.db") as conn:
        df.to_sql("strokes_gained", conn, if_exists="replace", index=False)
        conn.commit()
    print("✅ 'strokes_gained' table updated with precomputed race_z_score and strokes gained metrics.")

def update_strokes_gained_etl():
    df = extract_race_data()
    sg_df = compute_strokes_gained(df)
    store_strokes_gained(sg_df)

if __name__ == "__main__":
    update_strokes_gained_etl()
