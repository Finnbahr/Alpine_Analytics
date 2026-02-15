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
    Process race data to compute performance consistency metrics:
      - Merge in precomputed race_z_score.
      - Flag DNFs and compute bounce-back races.
      - Compute maximum DNF streak per athlete per year.
      - Compute a bounce back z score (average race_z_score in bounce races).
      - Aggregate yearly metrics including:
           * Mean and std of FIS points and race_z_score.
           * Coefficient of Variation (CV) for both metrics.
           * DNF counts, rates, and maximum DNF streak.
           * Bounce-back score (average FIS points) and bounce back z score.
    """
    # Merge in the precomputed race_z_score.
    df = merge_with_zscore(df)
    
    # Extract year from race date.
    df['year'] = df['date'].dt.year
    df['fis_points'] = pd.to_numeric(df['fis_points'], errors='coerce')
    
    # Identify DNFs (assume any rank starting with 'DNF' is a DNF).
    df['rank_str'] = df['rank'].astype(str)
    df['dnf'] = df['rank_str'].str.upper().str.startswith('DNF')
    
    # Sort data by athlete, discipline, and date.
    df = df.sort_values(by=['fis_code', 'discipline', 'date'])
    
    # Bounce-back: a race is considered a bounce if the previous race was a DNF and current race is finished.
    df['prev_dnf'] = df.groupby(['fis_code', 'discipline'])['dnf'].shift(1)
    df['bounce_race'] = (df['prev_dnf'] == True) & (df['dnf'] == False)
    
    # Compute bounce-back metrics:
    # - bounce_back_score: average FIS points in bounce races.
    # - bounce_back_z_score: average race_z_score in bounce races.
    bounce_stats = (
        df[df['bounce_race']]
        .groupby(['fis_code', 'name', 'discipline'])
        .agg(
            bounce_back_score=('fis_points', 'mean'),
            bounce_back_z_score=('race_z_score', 'mean')
        )
        .reset_index()
    )
    
    # Compute maximum DNF streak per athlete for each discipline and year.
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

    df = df.groupby(['fis_code', 'discipline', 'year'], group_keys=False).apply(compute_dnf_streaks)
    
    # Aggregate yearly performance metrics.
    yearly = (
        df.groupby(['fis_code', 'name', 'discipline', 'year'])
        .agg(
            races=('fis_points', 'count'),
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
    yearly['cv_fis'] = yearly.apply(lambda row: round(row['std_fis'] / row['mean_fis'], 2)
                                    if row['mean_fis'] and row['mean_fis'] != 0 else None, axis=1)
    yearly['cv_race_z'] = yearly.apply(lambda row: round(row['std_race_z_score'] / row['mean_race_z_score'], 2)
                                       if row['mean_race_z_score'] and row['mean_race_z_score'] != 0 else None, axis=1)
    
    # Merge bounce-back stats into the yearly summary.
    result = pd.merge(yearly, bounce_stats, on=['fis_code', 'name', 'discipline'], how='left')
    result['last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    return result

def store_performance_consistency(df):
    """
    Store the aggregated performance consistency metrics into the aggregate DB.
    """
    with sqlite3.connect("athlete_fis_information_aggregate.db") as conn:
        df.to_sql("performance_consistency_yearly", conn, if_exists="replace", index=False)
        conn.commit()
    print("✅ 'performance_consistency_yearly' table updated with enhanced consistency metrics.")

def update_performance_consistency_etl():
    df = extract_race_data()
    consistency_df = process_performance_consistency(df)
    store_performance_consistency(consistency_df)

if __name__ == "__main__":
    update_performance_consistency_etl()
