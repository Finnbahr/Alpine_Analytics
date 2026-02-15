import sqlite3
import pandas as pd
from datetime import datetime

def load_race_and_hill_data():
    """
    Load raw race data from fis_results and fis_race_details,
    merge with hill/course data from event_fis_info_aggregate,
    and then join the precomputed race_z_score from the aggregate DB.
    """
    # Load raw race data.
    with sqlite3.connect("fis_results.db") as conn:
        conn.execute("ATTACH DATABASE 'fis_race_details.db' AS rd_db")
        race_query = """
        SELECT 
            fr.race_id,
            fr.fis_code,
            fr.name,
            fr.fis_points,
            fr.bib,
            rd.date,
            rd.discipline,
            rd.location,
            rd.homologation_number
        FROM fis_results fr
        JOIN rd_db.race_details rd ON fr.race_id = rd.race_id
        WHERE fr.fis_points IS NOT NULL
        """
        race_df = pd.read_sql_query(race_query, conn)
    
    race_df['date'] = pd.to_datetime(race_df['date'])
    
    # Merge with hill/course data.
    with sqlite3.connect("event_fis_info_aggregate.db") as conn2:
        hill_df = pd.read_sql_query("SELECT * FROM basic_hill_info", conn2)
    full_df = race_df.merge(
        hill_df,
        on=['location', 'discipline', 'homologation_number'],
        how='left'
    )
    
    # Join with the precomputed race_z_score table using both race_id and fis_code.
    with sqlite3.connect("athlete_fis_information_aggregate.db") as conn3:
        z_df = pd.read_sql_query("SELECT race_id, fis_code, race_z_score FROM race_z_score", conn3)
    full_df = full_df.merge(z_df, on=['race_id', 'fis_code'], how='left')
    
    # Rename the joined z-score column to match later usage.
    full_df.rename(columns={'race_z_score': 'z_score_fis_points'}, inplace=True)
    
    return full_df

def compute_trait_bins_and_deltas(df, bin_count=5):
    """
    Compute rolling performance delta and bin traits, using the precomputed z_score_fis_points.
    """
    df = df.sort_values(by=['fis_code', 'discipline', 'date'])
    df['fis_points'] = pd.to_numeric(df['fis_points'], errors='coerce')
    df['bib'] = pd.to_numeric(df['bib'], errors='coerce')
    
    # Use precomputed z-score instead of recalculating it.
    # df['z_score_fis_points'] = df.groupby('race_id')['fis_points'].transform(
    #     lambda x: (x.mean() - x) / x.std(ddof=0) if x.std(ddof=0) != 0 else 0
    # )
    
    # Rolling performance delta per athlete and discipline.
    def calc_running_delta(group):
        group['prior_avg'] = group['fis_points'].expanding().mean().shift(1)
        group['performance_delta'] = group['prior_avg'] - group['fis_points']
        return group

    df = df.groupby(['fis_code', 'discipline'], group_keys=False).apply(calc_running_delta)
    df = df[df['performance_delta'].notna()]
    df['mean_bib'] = df['bib']

    # Define traits and their corresponding raw columns.
    traits = {
        'mean_gate_count': 'gate_count',
        'mean_start_altitude': 'start_altitude',
        'mean_vertical_drop': 'vertical_drop',
        'mean_winning_time': 'winning_time',
        'mean_dnf_rate': 'dnf_rate',
        'mean_bib': 'bib'
    }

    results = []
    for trait_col, trait_label in traits.items():
        if trait_col not in df.columns:
            continue

        binned = df.copy()
        binned['trait'] = trait_label
        binned['trait_value'] = pd.to_numeric(binned[trait_col], errors='coerce')
        binned = binned.dropna(subset=['trait_value'])

        try:
            binned['trait_bin'] = pd.qcut(binned['trait_value'], q=bin_count, duplicates='drop').astype(str)
        except ValueError:
            continue

        summary = (
            binned.groupby(['fis_code', 'name', 'discipline', 'trait', 'trait_bin'], observed=True)
            .agg(
                avg_performance_delta=('performance_delta', 'mean'),
                avg_z_score=('z_score_fis_points', 'mean'),
                race_count=('performance_delta', 'count')
            )
            .reset_index()
        )
        results.append(summary)

    if results:
        final_df = pd.concat(results, ignore_index=True)
        final_df['avg_performance_delta'] = final_df['avg_performance_delta'].round(2)
        final_df['avg_z_score'] = final_df['avg_z_score'].round(2)
        final_df['last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return final_df
    else:
        return pd.DataFrame()

def store_course_trait(df):
    """
    Store the trait binning results into the aggregate DB.
    """
    with sqlite3.connect("athlete_fis_information_aggregate.db") as conn:
        df.to_sql("course_trait", conn, if_exists="replace", index=False)
        conn.commit()
    print("✅ 'course_trait' table created with binned traits and performance deltas.")

def update_course_trait_etl():
    df = load_race_and_hill_data()
    trait_df = compute_trait_bins_and_deltas(df)
    store_course_trait(trait_df)

if __name__ == "__main__":
    update_course_trait_etl()
