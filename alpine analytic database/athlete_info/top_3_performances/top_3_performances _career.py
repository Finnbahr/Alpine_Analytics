import sqlite3
import pandas as pd
from datetime import datetime

def extract_full_race_data():
    """
    Extract full race data from fis_results.db and fis_race_details.db.
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

def merge_race_zscore(df):
    """
    Merge the precomputed race_z_score from the aggregate database,
    matching on both race_id and fis_code.
    """
    with sqlite3.connect("athlete_fis_information_aggregate.db") as conn:
        z_df = pd.read_sql_query("SELECT race_id, fis_code, race_z_score FROM race_z_score", conn)
    return df.merge(z_df, on=['race_id', 'fis_code'], how='left')

def compute_top_3_performances(df):
    """
    Compute the top 3 performances per athlete and discipline using the precomputed race_z_score.
    Higher race_z_score indicates a better performance.
    """
    # Merge in the precomputed race_z_score.
    df = merge_race_zscore(df)
    
    # Filter out records with no valid race_z_score.
    df = df[df['race_z_score'].notna()]
    
    # Sort by athlete, discipline, and race date.
    df = df.sort_values(by=['fis_code', 'discipline', 'date'])
    
    # For each athlete and discipline, select the top 3 races with the highest race_z_score.
    top3_df = (
        df.sort_values(by='race_z_score', ascending=False)
          .groupby(['fis_code', 'discipline'])
          .head(3)
          .reset_index(drop=True)
    )
    
    return top3_df

def store_top_3_performances(df):
    """
    Store the top 3 performances DataFrame into the aggregate database.
    """
    with sqlite3.connect("athlete_fis_information_aggregate.db") as conn:
        df['last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        df.to_sql("top_3_performances_career", conn, if_exists="replace", index=False)
        conn.commit()
    print("✅ 'top_3_performances_career' table updated in the aggregate database.")

def update_top_3_performance_etl():
    df = extract_full_race_data()
    top3_df = compute_top_3_performances(df)
    store_top_3_performances(top3_df)

if __name__ == "__main__":
    update_top_3_performance_etl()
