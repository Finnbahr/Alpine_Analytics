import sqlite3
import pandas as pd
from datetime import datetime

def extract_athlete_data():
    """
    Connect to fis_results.db and attach fis_race_details.db,
    then extract fields needed for career aggregation.
    """
    with sqlite3.connect("fis_results.db") as conn:
        conn.execute("ATTACH DATABASE 'fis_race_details.db' AS rd_db")
        query = """
        SELECT 
          fr.race_id,
          fr.fis_code,
          fr.name,
          fr.bib,
          fr.rank,
          fr.fis_points,
          rd.date,
          rd.discipline
        FROM fis_results fr
        JOIN rd_db.race_details rd ON fr.race_id = rd.race_id
        """
        df = pd.read_sql_query(query, conn)
    # Convert date to datetime (even though it is not used for grouping)
    df['date'] = pd.to_datetime(df['date'])
    return df

def merge_race_zscore(df):
    """
    Merge the precomputed race_z_score into the athlete data
    using race_id and fis_code as keys.
    """
    with sqlite3.connect("athlete_fis_information_aggregate.db") as conn:
        z_df = pd.read_sql_query("SELECT race_id, fis_code, race_z_score FROM race_z_score", conn)
    return df.merge(z_df, on=['race_id', 'fis_code'], how='left')

def process_athlete_data(df):
    """
    Process and aggregate the raw athlete data by fis_code, name, and discipline (career-level).
    Steps:
      1. Convert fis_points to numeric.
      2. For rows where rank starts with 'DNF', set fis_points to NaN.
      3. Convert bib to numeric and compute a new bib index for each race.
      4. Convert rank to numeric where possible.
      5. Create a DNF flag.
      6. Group the data by athlete and discipline and compute:
         - Race count.
         - Aggregated statistics for fis_points, bib_index, and rank.
         - DNF rate and count.
         - Aggregated (career-level) statistics for race_z_score.
    """
    # Convert fis_points to numeric.
    df['fis_points'] = pd.to_numeric(df['fis_points'], errors='coerce')
    
    # For rows where rank starts with "DNF", set fis_points to NaN.
    df.loc[df['rank'].str.upper().str.startswith("DNF"), 'fis_points'] = pd.NA
    
    # Convert bib to numeric.
    df['bib_num'] = pd.to_numeric(df['bib'], errors='coerce')
    
    # Compute a new bib index for each race so that the lowest bib becomes 1, 2, etc.
    df['bib_index'] = df.groupby('race_id')['bib_num'].rank(method='dense', ascending=True)
    
    # Convert rank to numeric where possible.
    df['rank_num'] = pd.to_numeric(df['rank'], errors='coerce')
    
    # Create a flag for DNFs.
    df['dnf_flag'] = df['rank'].str.upper().str.startswith("DNF")
    
    # Group by athlete (fis_code, name) and discipline (career-level aggregation).
    grouped = df.groupby(['fis_code', 'name', 'discipline'])
    
    agg_df = grouped.agg(
        race_count = ('race_id', 'count'),
        # FIS points statistics.
        min_fis_points = ('fis_points', 'min'),
        max_fis_points = ('fis_points', 'max'),
        mean_fis_points = ('fis_points', 'mean'),
        std_fis_points = ('fis_points', 'std'),
        # Bib index statistics.
        min_bib = ('bib_index', 'min'),
        max_bib = ('bib_index', 'max'),
        mean_bib = ('bib_index', 'mean'),
        std_bib = ('bib_index', 'std'),
        # Rank statistics.
        min_rank = ('rank_num', 'min'),
        max_rank = ('rank_num', 'max'),
        mean_rank = ('rank_num', 'mean'),
        std_rank = ('rank_num', 'std'),
        # DNF metrics.
        dnf_rate = ('dnf_flag', 'mean'),
        dnf_count = ('dnf_flag', 'sum'),
        # Race_z_score statistics (career-level).
        min_race_z_score = ('race_z_score', 'min'),
        max_race_z_score = ('race_z_score', 'max'),
        mean_race_z_score = ('race_z_score', 'mean'),
        std_race_z_score = ('race_z_score', 'std')
    ).reset_index()
    
    # Round numeric columns to two decimals.
    numeric_cols = agg_df.select_dtypes(include=['float64', 'int64']).columns
    agg_df[numeric_cols] = agg_df[numeric_cols].round(2)
    
    return agg_df

def update_basic_athlete_info():
    """
    Complete ETL process: extract data, merge race_z_score,
    process and aggregate career-level data, then store the enriched basic athlete info.
    """
    # Extract raw athlete data.
    df_raw = extract_athlete_data()
    # Merge in the precomputed race_z_score.
    df_raw = merge_race_zscore(df_raw)
    # Process and aggregate the data.
    df_agg = process_athlete_data(df_raw)
    # Add a timestamp.
    df_agg['last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Store the aggregated data into the aggregate database.
    agg_db = "athlete_fis_information_aggregate.db"
    with sqlite3.connect(agg_db) as conn:
        df_agg.to_sql("basic_athlete_info_career", conn, if_exists="replace", index=False)
        conn.commit()
    
    print(f"'basic_athlete_info_career' table updated in '{agg_db}' at {datetime.now()}.")

if __name__ == '__main__':
    update_basic_athlete_info()
