import sqlite3
import pandas as pd
from datetime import datetime
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score

def load_race_and_hill_data():
    """
    Load raw race data from fis_results and fis_race_details,
    merge with hill/course data from event_fis_info_aggregate,
    and then join the precomputed race_z_score from the aggregate DB.
    """
    # Load raw race data.
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
            rd.discipline,
            rd.location,
            rd.homologation_number
        FROM fis_results fr
        JOIN rd_db.race_details rd ON fr.race_id = rd.race_id
        WHERE fr.fis_points IS NOT NULL
        """
        race_df = pd.read_sql_query(query, conn)
    
    # Convert date to datetime.
    race_df['date'] = pd.to_datetime(race_df['date'])
    
    # Merge with hill/course data.
    with sqlite3.connect("event_fis_info_aggregate.db") as conn2:
        hill_df = pd.read_sql_query("SELECT * FROM basic_hill_info", conn2)
    full_df = race_df.merge(
        hill_df,
        on=['location', 'discipline', 'homologation_number'],
        how='left'
    )
    
    # Join with the precomputed race_z_score table.
    # Now we join on both race_id and fis_code to ensure a unique match.
    with sqlite3.connect("athlete_fis_information_aggregate.db") as conn3:
        z_df = pd.read_sql_query("SELECT race_id, fis_code, race_z_score FROM race_z_score", conn3)
    full_df = full_df.merge(z_df, on=['race_id', 'fis_code'], how='left')
    
    return full_df

def compute_course_regression(df, min_races=8):
    """
    For each athlete and discipline, run a linear regression using selected course features
    to predict the precomputed race_z_score.
    """
    df = df.sort_values(by=['fis_code', 'discipline', 'date'])
    df['fis_points'] = pd.to_numeric(df['fis_points'], errors='coerce')
    df['bib'] = pd.to_numeric(df['bib'], errors='coerce')
    df['mean_bib'] = df['bib']

    # Define course features.
    features = [
        'mean_gate_count',
        'mean_start_altitude',
        'mean_vertical_drop',
        'mean_winning_time',
        'mean_dnf_rate',
        'mean_bib'
    ]

    # Drop rows missing any feature or the target z-score.
    df = df.dropna(subset=features + ['race_z_score'])

    results = []
    # Group by athlete (fis_code, name) and discipline.
    for (fis_code, name, discipline), group in df.groupby(['fis_code', 'name', 'discipline']):
        if len(group) < min_races:
            continue

        X = group[features]
        y = group['race_z_score']

        # Safety check.
        if X.isnull().any().any() or y.isnull().any():
            continue

        model = LinearRegression().fit(X, y)
        y_pred = model.predict(X)
        r2 = r2_score(y, y_pred)

        for feature, coef in zip(features, model.coef_):
            results.append({
                'fis_code': fis_code,
                'name': name,
                'discipline': discipline,
                'trait': feature.replace("mean_", ""),
                'coefficient': round(coef, 4),
                'r_squared': round(r2, 4),
                'race_count': len(group),
                'last_updated': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

    return pd.DataFrame(results)

def store_course_regression(df):
    """
    Store the regression results into the aggregate DB.
    """
    with sqlite3.connect("athlete_fis_information_aggregate.db") as conn:
        df.to_sql("course_regression", conn, if_exists="replace", index=False)
        conn.commit()
    print("✅ 'course_regression' table updated using precomputed race_z_score as target.")

def update_course_regression_etl():
    df = load_race_and_hill_data()
    reg_df = compute_course_regression(df)
    store_course_regression(reg_df)

if __name__ == "__main__":
    update_course_regression_etl()
