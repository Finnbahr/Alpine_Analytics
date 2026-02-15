import sqlite3
import pandas as pd
from datetime import datetime

def extract_race_data():
    """
    Extract raw race data from fis_results and fis_race_details, including:
      - race_id, fis_code, name, fis_points, bib, date, location, homologation_number, discipline, and race_type.
    Converts date to datetime and ensures numeric columns are properly cast.
    """
    with sqlite3.connect("fis_results.db") as conn:
        conn.execute("ATTACH DATABASE 'fis_race_details.db' AS rd_db")
        query = """
        SELECT 
            fr.race_id,
            fr.fis_code,
            fr.name,
            fr.fis_points,
            fr.bib,
            rd.date,
            rd.location,
            rd.homologation_number,
            rd.discipline,
            rd.race_type
        FROM fis_results fr
        JOIN rd_db.race_details rd ON fr.race_id = rd.race_id
        WHERE fr.fis_points IS NOT NULL
        """
        df = pd.read_sql_query(query, conn)
    df['date'] = pd.to_datetime(df['date'])
    df['fis_points'] = pd.to_numeric(df['fis_points'], errors='coerce')
    df['bib'] = pd.to_numeric(df['bib'], errors='coerce')
    return df

def merge_with_zscore(df):
    """
    Merge raw race data with the precomputed race_z_score from the aggregate database,
    matching on both race_id and fis_code.
    """
    with sqlite3.connect("athlete_fis_information_aggregate.db") as conn:
        z_df = pd.read_sql_query("SELECT race_id, fis_code, race_z_score FROM race_z_score", conn)
    return df.merge(z_df, on=['race_id', 'fis_code'], how='left')

def compute_strokes_gained_bib_relative(df, bib_range=5):
    """
    For each race, calculate both:
      - The strokes gained relative to nearby competitors based on FIS points.
      - The local z-score delta (difference between the athlete’s race_z_score and the local average race_z_score).
    
    Process:
      1. Merge the precomputed race_z_score.
      2. For each race, sort competitors by bib.
      3. For each athlete, identify nearby competitors within ±bib_range (excluding the athlete).
      4. Compute:
         - local_avg_fis_points and then bib_strokes_gained = local_avg_fis_points - athlete's fis_points.
         - local_avg_race_z_score and then bib_zscore_delta = athlete's race_z_score - local_avg_race_z_score.
      5. Add a timestamp.
    """
    # Merge in precomputed race_z_score.
    df = merge_with_zscore(df)
    
    all_records = []
    
    for race_id, group in df.groupby('race_id'):
        # Sort competitors within the race by bib number.
        group = group.sort_values(by='bib').reset_index(drop=True)
        
        for idx, row in group.iterrows():
            if pd.isna(row['bib']):
                continue
            
            bib = row['bib']
            # Identify nearby competitors within the specified bib_range (excluding the athlete).
            nearby = group[(group['bib'] >= bib - bib_range) & 
                           (group['bib'] <= bib + bib_range) & 
                           (group['fis_code'] != row['fis_code'])]
            
            # Compute local average FIS points.
            local_avg_fis = nearby['fis_points'].mean() if not nearby.empty else None
            # Compute local average race_z_score.
            local_avg_z = nearby['race_z_score'].mean() if not nearby.empty else None
            
            # Calculate differences.
            points_gained = local_avg_fis - row['fis_points'] if pd.notna(local_avg_fis) and pd.notna(row['fis_points']) else None
            # Updated calculation: athlete's race_z_score minus local average race_z_score.
            zscore_delta = row['race_z_score'] - local_avg_z if pd.notna(local_avg_z) and pd.notna(row['race_z_score']) else None
            
            new_row = row.to_dict()
            new_row['local_avg_fis_points'] = local_avg_fis
            new_row['bib_strokes_gained'] = points_gained
            new_row['local_avg_race_z_score'] = local_avg_z
            new_row['bib_zscore_delta'] = zscore_delta
            new_row['last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            all_records.append(new_row)
    
    return pd.DataFrame(all_records)

def store_strokes_gained_bib_relative(df):
    """
    Store the computed strokes gained (bib relative) results into the aggregate database.
    """
    with sqlite3.connect("athlete_fis_information_aggregate.db") as conn:
        df.to_sql("strokes_gained_bib_relative", conn, if_exists="replace", index=False)
        conn.commit()
    print("✅ 'strokes_gained_bib_relative' table created in athlete_fis_information_aggregate.db")

def update_strokes_gained_bib_relative_etl():
    df = extract_race_data()
    sg_df = compute_strokes_gained_bib_relative(df, bib_range=5)
    store_strokes_gained_bib_relative(sg_df)

if __name__ == "__main__":
    update_strokes_gained_bib_relative_etl()
