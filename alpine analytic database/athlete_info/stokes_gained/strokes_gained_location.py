import sqlite3
import pandas as pd
from datetime import datetime

def extract_race_data():
    """
    Extract raw race data from fis_results.db and fis_race_details.db.
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
    df['date'] = pd.to_datetime(df['date'])
    df['fis_points'] = pd.to_numeric(df['fis_points'], errors='coerce')
    return df

def compute_strokes_gained(df):
    """
    Compute strokes gained metrics for each race:
      - Calculate average FIS points per race.
      - Compute points gained as: avg_fis_points - athlete's fis_points.
      - Merge in the precomputed race_z_score.
      - Append a timestamp.
    """
    # Calculate race-level average FIS points.
    race_avg = df.groupby('race_id').agg(avg_fis_points=('fis_points', 'mean')).reset_index()
    df = df.merge(race_avg, on='race_id', how='left')
    
    # Compute points gained.
    df['points_gained'] = df['avg_fis_points'] - df['fis_points']
    
    # Merge in the precomputed race_z_score.
    with sqlite3.connect("athlete_fis_information_aggregate.db") as conn:
        z_df = pd.read_sql_query("SELECT race_id, fis_code, race_z_score FROM race_z_score", conn)
    df = df.merge(z_df, on=['race_id', 'fis_code'], how='left')
    
    df['last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return df

def compute_strokes_gained_person_location(df):
    """
    Group strokes gained data per person, per discipline, and per location/homologation.
    For each athlete (fis_code, name) on each course (homologation_number, location)
    within a given discipline, compute summary statistics:
      - Race count.
      - Average and std deviation of points_gained.
      - Average and std deviation of race_z_score.
    """
    grouped = df.groupby(['fis_code', 'name', 'discipline', 'homologation_number', 'location']).agg(
        race_count=('race_id', 'count'),
        mean_points_gained=('points_gained', 'mean'),
        std_points_gained=('points_gained', 'std'),
        mean_race_z_score=('race_z_score', 'mean'),
        std_race_z_score=('race_z_score', 'std')
    ).reset_index()
    
    grouped['last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return grouped

def store_strokes_gained_person_location(df):
    """
    Store the per person per location strokes gained summary into the aggregate database
    under the table 'strokes_gained_location'.
    """
    with sqlite3.connect("athlete_fis_information_aggregate.db") as conn:
        df.to_sql("strokes_gained_location", conn, if_exists="replace", index=False)
        conn.commit()
    print("✅ 'strokes_gained_location' table created in athlete_fis_information_aggregate.db.")

def update_strokes_gained_person_location_etl():
    raw_df = extract_race_data()
    sg_df = compute_strokes_gained(raw_df)
    person_loc_df = compute_strokes_gained_person_location(sg_df)
    store_strokes_gained_person_location(person_loc_df)

if __name__ == "__main__":
    update_strokes_gained_person_location_etl()
