import sqlite3
import pandas as pd
from datetime import datetime

def load_top_3_performances():
    """
    Load top 3 athlete performances from athlete_fis_information_aggregate.db.
    """
    conn = sqlite3.connect("athlete_fis_information_aggregate.db")
    df = pd.read_sql_query("SELECT * FROM top_3_performances_career", conn)
    conn.close()
    return df

def rank_locations_by_zscore(df):
    """
    Group by location + discipline + homologation_number and compute average z-scores.
    """
    grouped = (
        df.groupby(['location', 'discipline', 'homologation_number'])
          .agg(
              mean_z_score=('z_score', 'mean'),
              performance_count=('z_score', 'count')
          )
          .reset_index()
          .sort_values(by='mean_z_score', ascending=False)
    )

    # Rank from easiest (high z) to hardest (low z)
    grouped['rank'] = grouped['mean_z_score'].rank(method='dense', ascending=False).astype(int)

    return grouped

def store_location_zscore_ranking(grouped_df):
    """
    Save ranking into event_fis_info_aggregate.db as 'location_zscore_ranking'.
    """
    conn = sqlite3.connect("event_fis_info_aggregate.db")
    grouped_df['last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    grouped_df.to_sql("location_zscore_ranking", conn, if_exists="replace", index=False)
    conn.commit()
    conn.close()
    print("✅ 'location_zscore_ranking' table created in 'event_fis_info_aggregate.db'.")

def update_location_ranking_etl():
    df = load_top_3_performances()
    ranked_df = rank_locations_by_zscore(df)
    store_location_zscore_ranking(ranked_df)

if __name__ == "__main__":
    update_location_ranking_etl()
