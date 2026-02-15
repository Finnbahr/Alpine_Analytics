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
            fr.bib,
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
    df['bib'] = pd.to_numeric(df['bib'], errors='coerce')
    return df

def merge_with_zscore(df):
    """
    Merge raw race data with the precomputed race_z_score from the aggregate DB,
    matching on both race_id and fis_code.
    """
    with sqlite3.connect("athlete_fis_information_aggregate.db") as conn:
        z_df = pd.read_sql_query("SELECT race_id, fis_code, race_z_score FROM race_z_score", conn)
    return df.merge(z_df, on=['race_id', 'fis_code'], how='left')

def compute_bib_relative_metrics(df, bib_range=5):
    """
    For each race, compute local averages for FIS points and race_z_score among competitors 
    with similar bib numbers (within ±bib_range), then calculate:
      - bib_strokes_gained = local_avg_fis_points - athlete's fis_points.
      - bib_zscore_delta = athlete's race_z_score - local_avg_race_z_score.
    """
    # Merge in precomputed race_z_score.
    df = merge_with_zscore(df)
    all_records = []
    
    for race_id, group in df.groupby('race_id'):
        # Sort competitors by bib within the race.
        group = group.sort_values(by='bib').reset_index(drop=True)
        for idx, row in group.iterrows():
            if pd.isna(row['bib']):
                continue
            bib = row['bib']
            # Identify nearby competitors within ±bib_range (excluding the athlete).
            nearby = group[(group['bib'] >= bib - bib_range) & 
                           (group['bib'] <= bib + bib_range) & 
                           (group['fis_code'] != row['fis_code'])]
            # Compute local averages.
            local_avg_fis = nearby['fis_points'].mean() if not nearby.empty else None
            local_avg_z = nearby['race_z_score'].mean() if not nearby.empty else None
            
            # Calculate differences.
            points_gained = local_avg_fis - row['fis_points'] if pd.notna(local_avg_fis) and pd.notna(row['fis_points']) else None
            zscore_delta = row['race_z_score'] - local_avg_z if pd.notna(local_avg_z) and pd.notna(row['race_z_score']) else None
            
            new_row = row.to_dict()
            new_row['local_avg_fis_points'] = local_avg_fis
            new_row['bib_strokes_gained'] = points_gained
            new_row['local_avg_race_z_score'] = local_avg_z
            new_row['bib_zscore_delta'] = zscore_delta
            new_row['last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            all_records.append(new_row)
    
    return pd.DataFrame(all_records)

def aggregate_bib_relative_by_person(df):
    """
    Group the bib relative metrics per person, per discipline, per homologation number, and location.
    Compute summary statistics:
      - Race count.
      - Mean and std deviation of bib_strokes_gained.
      - Mean and std deviation of race_z_score.
      - Mean and std deviation of bib_zscore_delta.
    """
    grouped = df.groupby(['fis_code', 'name', 'discipline', 'homologation_number', 'location']).agg(
        race_count=('race_id', 'count'),
        mean_points_gained=('bib_strokes_gained', 'mean'),
        std_points_gained=('bib_strokes_gained', 'std'),
        mean_race_z_score=('race_z_score', 'mean'),
        std_race_z_score=('race_z_score', 'std'),
        mean_bib_zscore_delta=('bib_zscore_delta', 'mean'),
        std_bib_zscore_delta=('bib_zscore_delta', 'std')
    ).reset_index()
    
    grouped['last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return grouped

def store_bib_relative_aggregated(df):
    """
    Store the aggregated bib relative performance metrics into the aggregate database
    under the table 'bib_relative_performance'.
    """
    with sqlite3.connect("athlete_fis_information_aggregate.db") as conn:
        df.to_sql("strokes_gained_bib_relative_location", conn, if_exists="replace", index=False)
        conn.commit()
    print("✅ 'strokes_gained_bib_relative_location' table created in athlete_fis_information_aggregate.db.")

def update_bib_relative_performance_etl():
    raw_df = extract_race_data()
    bib_rel_df = compute_bib_relative_metrics(raw_df, bib_range=5)
    agg_df = aggregate_bib_relative_by_person(bib_rel_df)
    store_bib_relative_aggregated(agg_df)

if __name__ == "__main__":
    update_bib_relative_performance_etl()
