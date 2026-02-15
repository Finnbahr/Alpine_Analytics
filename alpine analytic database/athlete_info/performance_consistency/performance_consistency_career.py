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
            fr.rank,
            fr.fis_points,
            rd.date,
            rd.discipline
        FROM fis_results fr
        JOIN rd_db.race_details rd ON fr.race_id = rd.race_id
        """
        df = pd.read_sql_query(query, conn)
    df['date'] = pd.to_datetime(df['date'])
    return df

def merge_with_zscore(df):
    """
    Merge raw race data with the precomputed race_z_score from the aggregate DB,
    matching on both race_id and fis_code.
    """
    with sqlite3.connect("athlete_fis_information_aggregate.db") as conn:
        z_df = pd.read_sql_query("SELECT race_id, fis_code, race_z_score FROM race_z_score", conn)
    return df.merge(z_df, on=['race_id', 'fis_code'], how='left')

def process_performance_consistency(df):
    """
    Process race data to compute career-level performance consistency metrics:
      - Merge in precomputed race_z_score.
      - Convert fis_points to numeric.
      - Flag DNFs (rows where rank starts with 'DNF').
      - Sort races by date (per athlete and discipline).
      - Identify bounce-back races (where the previous race was a DNF but the current race was finished).
      - Compute bounce-back metrics: average FIS points and average race_z_score in bounce-back races.
      - Compute the maximum DNF streak for each athlete (across their career).
      - Aggregate career-level metrics for each athlete and discipline:
           * Race count.
           * Mean and std of FIS points and race_z_score.
           * Coefficient of Variation (CV) for both metrics.
           * DNF count and rate.
           * Maximum DNF streak.
           * Bounce-back metrics.
    """
    # Merge in the precomputed race_z_score.
    df = merge_with_zscore(df)
    
    # Ensure fis_points is numeric.
    df['fis_points'] = pd.to_numeric(df['fis_points'], errors='coerce')
    
    # Identify DNFs.
    df['rank_str'] = df['rank'].astype(str)
    df['dnf'] = df['rank_str'].str.upper().str.startswith('DNF')
    
    # Sort data by athlete, discipline, and date.
    df = df.sort_values(by=['fis_code', 'discipline', 'date'])
    
    # Bounce-back: a race is a bounce if the previous race was a DNF and the current race is finished.
    df['prev_dnf'] = df.groupby(['fis_code', 'discipline'])['dnf'].shift(1)
    df['bounce_race'] = (df['prev_dnf'] == True) & (df['dnf'] == False)
    
    # Bounce-back metrics.
    bounce_stats = (
        df[df['bounce_race']]
        .groupby(['fis_code', 'name', 'discipline'])
        .agg(
            bounce_back_score=('fis_points', 'mean'),
            bounce_back_z_score=('race_z_score', 'mean')
        )
        .reset_index()
    )
    
    # Compute maximum DNF streak for each athlete and discipline (career-level).
    def compute_dnf_streaks(group):
        max_streak = 0
        current_streak = 0
        for d in group['dnf']:
            if d:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 0
        group['max_dnf_streak'] = max_streak
        return group
    
    df = df.groupby(['fis_code', 'discipline'], group_keys=False).apply(compute_dnf_streaks)
    
    # Aggregate career-level metrics.
    career = (
        df.groupby(['fis_code', 'name', 'discipline'])
        .agg(
            races=('race_id', 'count'),
            mean_fis=('fis_points', 'mean'),
            std_fis=('fis_points', 'std'),
            mean_race_z_score=('race_z_score', 'mean'),
            std_race_z_score=('race_z_score', 'std'),
            dnf_count=('dnf', 'sum'),
            dnf_rate=('dnf', 'mean'),
            max_dnf_streak=('max_dnf_streak', 'max')
        )
        .reset_index()
    )
    
    # Calculate Coefficient of Variation (CV) for FIS points and race z-scores.
    career['cv_fis'] = career.apply(lambda row: round(row['std_fis'] / row['mean_fis'], 2)
                                    if row['mean_fis'] and row['mean_fis'] != 0 else None, axis=1)
    career['cv_race_z'] = career.apply(lambda row: round(row['std_race_z_score'] / row['mean_race_z_score'], 2)
                                       if row['mean_race_z_score'] and row['mean_race_z_score'] != 0 else None, axis=1)
    
    # Merge bounce-back stats into the career summary.
    career = career.merge(bounce_stats, on=['fis_code', 'name', 'discipline'], how='left')
    
    # Add a timestamp.
    career['last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return career

def update_performance_consistency_career():
    """
    Complete ETL process: extract race data, merge in race_z_score,
    process and aggregate career-level performance consistency metrics,
    and store the results in the aggregate database.
    """
    df_raw = extract_race_data()
    consistency_df = process_performance_consistency(df_raw)
    agg_db = "athlete_fis_information_aggregate.db"
    with sqlite3.connect(agg_db) as conn:
        consistency_df.to_sql("performance_consistency_career", conn, if_exists="replace", index=False)
        conn.commit()
    print(f"'performance_consistency_career' table updated in '{agg_db}' at {datetime.now()}.")

if __name__ == "__main__":
    update_performance_consistency_career()
