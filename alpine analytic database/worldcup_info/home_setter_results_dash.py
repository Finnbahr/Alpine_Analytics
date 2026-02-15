import dash
from dash import dcc, html, dash_table, Input, Output
import pandas as pd
import sqlite3
import math
import plotly.express as px

# ---------------------------
# Helper Functions
# ---------------------------
def time_to_seconds(time_str):
    """
    Convert a race time string (e.g. "1:12.34" or "12.34") to total seconds as a float.
    If the string includes a colon, interpret the part before the colon as minutes.
    """
    try:
        time_str = time_str.strip()
        if ':' in time_str:
            parts = time_str.split(':')
            minutes = float(parts[0])
            seconds = float(parts[1])
            return minutes * 60 + seconds
        else:
            return float(time_str)
    except Exception:
        return None

def normalize_series(s, lower_quantile=0.05, upper_quantile=0.95):
    """
    Clip the series to the lower and upper quantiles, then normalize to a 0-100 scale.
    """
    low = s.quantile(lower_quantile)
    high = s.quantile(upper_quantile)
    s_clipped = s.clip(lower=low, upper=high)
    if high - low > 0:
        return 100 * (s_clipped - low) / (high - low)
    else:
        return pd.Series(50, index=s.index)

def minutes_to_time_str(minutes):
    """
    Convert decimal minutes into "m:ss.xx" format.
    """
    if minutes is None or (isinstance(minutes, float) and math.isnan(minutes)):
        return ""
    total_seconds = minutes * 60
    m = int(total_seconds // 60)
    s = total_seconds - m * 60
    return f"{m}:{s:05.2f}"

# ---------------------------
# Database Connection & Data Loading
# ---------------------------
results_db_path = r"C:\Users\Finnbahr.malcolm\fis_results.db"
details_db_path = r"C:\Users\Finnbahr.malcolm\fis_race_details.db"

# Updated SQL Query:
# - Filters for race types 'World Cup' and 'Audi FIS Ski World Cup'
# - Retrieves first_run_course_setter_country and, for points, an effective second-run setter:
#   If the discipline is 'Super G' or 'Downhill', then effective_second_setter_country = first_run_course_setter_country;
#   Otherwise, it uses rd.second_run_course_setter_country.
query = """
WITH base AS (
  SELECT 
    fr.race_id,
    fr.fis_code,
    fr.name,
    rd.sex AS sex,
    fr.country AS competitor_country,
    CAST(fr.fis_points AS REAL) AS fis_points,
    CAST(fr.cup_points AS REAL) AS cup_points,
    CASE 
      WHEN fr.rank GLOB '[0-9]*' THEN CAST(fr.rank AS INTEGER)
      ELSE NULL
    END AS rank,
    fr.final_time,
    rd.discipline AS disc,
    rd.date,
    rd.first_run_course_setter_country AS first_setter_country,
    CASE 
      WHEN rd.discipline IN ('Super G', 'Downhill') THEN rd.first_run_course_setter_country
      ELSE rd.second_run_course_setter_country
    END AS effective_second_setter_country
  FROM fis_results fr
  JOIN rd_db.race_details rd ON fr.race_id = rd.race_id
  WHERE rd.race_type IN ('World Cup','Audi FIS Ski World Cup')
    AND rd.first_run_course_setter_country <> ''
    AND fr.final_time IS NOT NULL AND fr.final_time <> ''
),
with_metrics AS (
  SELECT *,
         UPPER(TRIM(competitor_country)) AS comp_country,
         UPPER(TRIM(first_setter_country)) AS first_setter_norm,
         UPPER(TRIM(effective_second_setter_country)) AS effective_second_setter_norm,
         -- For Top30: use first_run setter.
         CASE 
           WHEN UPPER(TRIM(competitor_country)) = UPPER(TRIM(first_setter_country)) THEN 'Home'
           ELSE 'Away'
         END AS home_flag_first,
         -- For points: use effective setter (depends on discipline).
         CASE 
           WHEN UPPER(TRIM(competitor_country)) = UPPER(TRIM(effective_second_setter_country)) THEN 'Home'
           ELSE 'Away'
         END AS home_flag_effective,
         CASE 
           WHEN rank IS NOT NULL AND rank <= 30 THEN 1
           ELSE 0
         END AS qualifies_top30,
         CAST(final_time AS REAL) AS final_time_sec
  FROM base
),
-- Aggregate Top30 counts (first run only)
race_group_top30 AS (
  SELECT 
    race_id,
    comp_country,
    sex,
    disc,
    home_flag_first,
    COUNT(*) AS competitor_count,
    SUM(qualifies_top30) AS top30_count
  FROM with_metrics
  GROUP BY race_id, comp_country, sex, disc, home_flag_first
),
agg_top30 AS (
  SELECT 
    comp_country,
    sex,
    disc,
    home_flag_first,
    COUNT(race_id) AS race_count,
    AVG(top30_count) AS avg_top30_count
  FROM race_group_top30
  GROUP BY comp_country, sex, disc, home_flag_first
),
-- Aggregate FIS and Cup points (using effective setter)
race_group_points AS (
  SELECT 
    race_id,
    comp_country,
    sex,
    disc,
    home_flag_effective,
    AVG(fis_points) AS avg_fis_points,
    AVG(cup_points) AS avg_cup_points
  FROM with_metrics
  GROUP BY race_id, comp_country, sex, disc, home_flag_effective
),
agg_points AS (
  SELECT 
    comp_country,
    sex,
    disc,
    home_flag_effective,
    COUNT(race_id) AS race_count,
    AVG(avg_fis_points) AS avg_fis_points,
    AVG(avg_cup_points) AS avg_cup_points
  FROM race_group_points
  GROUP BY comp_country, sex, disc, home_flag_effective
)
-- Join the Home and Away aggregates.
SELECT 
  h.comp_country AS competitor_country,
  h.sex AS sex,
  h.disc AS discipline,
  h.race_count AS top30_race_count_home,
  h.avg_top30_count AS home_avg_top30_count,
  a.race_count AS top30_race_count_away,
  a.avg_top30_count AS away_avg_top30_count,
  p_home.avg_fis_points AS home_avg_fis_points,
  p_away.avg_fis_points AS away_avg_fis_points,
  p_home.avg_cup_points AS home_avg_cup_points,
  p_away.avg_cup_points AS away_avg_cup_points,
  CASE 
    WHEN a.avg_top30_count <> 0 THEN ((h.avg_top30_count - a.avg_top30_count) / a.avg_top30_count) * 100
    ELSE NULL
  END AS pct_top30_pct_diff,
  CASE 
    WHEN p_away.avg_fis_points <> 0 THEN ((p_home.avg_fis_points - p_away.avg_fis_points) / p_away.avg_fis_points) * 100
    ELSE NULL
  END AS fis_points_pct_diff,
  CASE 
    WHEN p_away.avg_cup_points <> 0 THEN ((p_home.avg_cup_points - p_away.avg_cup_points) / p_away.avg_cup_points) * 100
    ELSE NULL
  END AS cup_points_pct_diff
FROM 
  (SELECT * FROM agg_top30 WHERE home_flag_first = 'Home') h
JOIN 
  (SELECT * FROM agg_top30 WHERE home_flag_first = 'Away') a
    ON h.comp_country = a.comp_country AND h.sex = a.sex AND h.disc = a.disc
JOIN 
  (SELECT * FROM agg_points WHERE home_flag_effective = 'Home') p_home
    ON h.comp_country = p_home.comp_country AND h.sex = p_home.sex AND h.disc = p_home.disc
JOIN 
  (SELECT * FROM agg_points WHERE home_flag_effective = 'Away') p_away
    ON h.comp_country = p_away.comp_country AND h.sex = p_away.sex AND h.disc = p_away.disc
ORDER BY competitor_country, sex, discipline;
"""

def load_data():
    conn = sqlite3.connect(results_db_path)
    conn.execute("ATTACH DATABASE ? AS rd_db", (details_db_path,))
    df = pd.read_sql_query(query, conn)
    conn.close()
    # Round numeric columns to 2 decimals.
    numeric_cols = df.select_dtypes(include=['number']).columns
    df[numeric_cols] = df[numeric_cols].round(2)
    return df

df = load_data()

# ---------------------------
# Dash App Setup
# ---------------------------
app = dash.Dash(__name__)
server = app.server

# Build dropdown options.
discipline_options = [{'label': d, 'value': d} for d in sorted(df['discipline'].unique())]
country_options = [{'label': c, 'value': c} for c in sorted(df['competitor_country'].unique())]
sex_options = [{'label': "Men's", 'value': "Men's"}, {'label': "Women's", 'value': "Women's"}]
metric_options = [
    {'label': "Top30 Difference (%)", 'value': 'pct_top30_pct_diff'},
    {'label': "FIS Points Difference (%)", 'value': 'fis_points_pct_diff'},
    {'label': "Cup Points Difference (%)", 'value': 'cup_points_pct_diff'}
]

app.layout = html.Div([
    html.H1("Nation Performance Comparison Dashboard (Setter's Country)"),
    html.Div([
        html.Div([
            html.Label("Select Discipline:"),
            dcc.Dropdown(
                id='discipline-dropdown',
                options=discipline_options,
                multi=True,
                placeholder="Select discipline(s)..."
            )
        ], style={'width': '300px', 'display': 'inline-block'}),
        html.Div([
            html.Label("Select Competitor Country:"),
            dcc.Dropdown(
                id='country-dropdown',
                options=country_options,
                multi=True,
                placeholder="Select competitor country(ies)..."
            )
        ], style={'width': '300px', 'display': 'inline-block', 'marginLeft': '20px'}),
        html.Div([
            html.Label("Select Sex:"),
            dcc.Dropdown(
                id='sex-dropdown',
                options=sex_options,
                value=["Men's", "Women's"],
                multi=True,
                placeholder="Select gender(s)..."
            )
        ], style={'width': '300px', 'display': 'inline-block', 'marginLeft': '20px'}),
        html.Div([
            html.Label("Select Metric:"),
            dcc.Dropdown(
                id='metric-dropdown',
                options=metric_options,
                value='pct_top30_pct_diff',
                clearable=False
            )
        ], style={'width': '300px', 'display': 'inline-block', 'marginLeft': '20px'})
    ]),
    html.Br(),
    dcc.Graph(id='faceted-chart'),
    html.Br(),
    html.H3("Performance Metrics Table"),
    dash_table.DataTable(
        id='data-table',
        columns=[{"name": col, "id": col} for col in df.columns],
        data=df.to_dict('records'),
        page_size=10,
        style_table={'overflowX': 'auto'}
    )
])

@app.callback(
    Output('faceted-chart', 'figure'),
    Output('data-table', 'data'),
    Input('discipline-dropdown', 'value'),
    Input('country-dropdown', 'value'),
    Input('sex-dropdown', 'value'),
    Input('metric-dropdown', 'value')
)
def update_dashboard(selected_disciplines, selected_countries, selected_sexes, selected_metric):
    filtered = df.copy()
    if selected_disciplines:
        filtered = filtered[filtered['discipline'].isin(selected_disciplines)]
    if selected_countries:
        filtered = filtered[filtered['competitor_country'].isin(selected_countries)]
    if selected_sexes:
        filtered = filtered[filtered['sex'].isin(selected_sexes)]
    
    if filtered.empty:
        return {}, []
    
    facet_col = 'discipline' if (not selected_disciplines or len(selected_disciplines) > 1) else None
    facet_row = 'sex'
    
    fig = px.bar(filtered, x='competitor_country', y=selected_metric,
                 facet_row=facet_row, facet_col=facet_col,
                 color='competitor_country',
                 text=selected_metric,
                 title=f"Home vs. Away Difference in {selected_metric}")
    
    fig.update_layout(showlegend=False)
    fig.update_traces(texttemplate='%{text:.2f}', textposition='auto')
    
    table_data = filtered.sort_values(['competitor_country', 'discipline']).to_dict('records')
    return fig, table_data

if __name__ == '__main__':
    app.run_server(debug=True)
