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

# Use your existing query (which aggregates Home vs. Away performance by competitor country, discipline, and sex)
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
    rd.race_type,
    rd.date,
    rd.first_run_course_setter,
    rd.country AS host_country
  FROM fis_results fr
  JOIN rd_db.race_details rd ON fr.race_id = rd.race_id
  WHERE rd.race_type IN ('World Cup','Audi FIS Ski World Cup')
    AND rd.first_run_course_setter <> ''
    AND fr.final_time IS NOT NULL AND fr.final_time <> ''
),
with_metrics AS (
  SELECT *,
         UPPER(TRIM(competitor_country)) AS comp_country,
         UPPER(TRIM(host_country)) AS host_country_norm,
         CASE 
           WHEN UPPER(TRIM(competitor_country)) = UPPER(TRIM(host_country)) THEN 'Home'
           ELSE 'Away'
         END AS home_flag
  FROM base
),
race_group AS (
  SELECT 
    race_id,
    comp_country,
    sex,
    disc,
    home_flag,
    COUNT(*) AS competitor_count,
    SUM(CASE WHEN rank IS NOT NULL AND rank <= 30 THEN 1 ELSE 0 END) AS top30_count,
    AVG(CASE WHEN rank IS NOT NULL AND rank <= 30 THEN 1.0 ELSE 0 END) AS pct_top30,
    AVG(fis_points) AS avg_fis_points,
    AVG(cup_points) AS avg_cup_points
  FROM with_metrics
  GROUP BY race_id, comp_country, sex, disc, home_flag
),
agg AS (
  SELECT 
    comp_country,
    sex,
    disc,
    home_flag,
    COUNT(DISTINCT race_id) AS race_count,
    AVG(top30_count) AS avg_top30_count,
    AVG(avg_fis_points) AS avg_fis_points,
    AVG(avg_cup_points) AS avg_cup_points,
    AVG(pct_top30) AS avg_pct_top30
  FROM race_group
  GROUP BY comp_country, sex, disc, home_flag
)
SELECT 
  h.comp_country AS competitor_country,
  h.sex AS sex,
  h.disc AS discipline,
  h.race_count AS home_race_count,
  h.avg_top30_count AS home_avg_top30_count,
  a.race_count AS away_race_count,
  a.avg_top30_count AS away_avg_top30_count,
  h.avg_fis_points AS home_avg_fis_points,
  a.avg_fis_points AS away_avg_fis_points,
  h.avg_cup_points AS home_avg_cup_points,
  a.avg_cup_points AS away_avg_cup_points,
  CASE 
    WHEN a.avg_top30_count <> 0 THEN ((h.avg_top30_count - a.avg_top30_count) / a.avg_top30_count) * 100
    ELSE NULL
  END AS pct_top30_pct_diff,
  CASE 
    WHEN a.avg_fis_points <> 0 THEN ((h.avg_fis_points - a.avg_fis_points) / a.avg_fis_points) * 100
    ELSE NULL
  END AS fis_points_pct_diff,
  CASE 
    WHEN a.avg_cup_points <> 0 THEN ((h.avg_cup_points - a.avg_cup_points) / a.avg_cup_points) * 100
    ELSE NULL
  END AS cup_points_pct_diff
FROM agg h
JOIN agg a ON h.comp_country = a.comp_country AND h.sex = a.sex AND h.disc = a.disc
WHERE h.home_flag = 'Home' AND a.home_flag = 'Away'
ORDER BY competitor_country, sex, discipline;
"""

def load_data():
    conn = sqlite3.connect('fis_results.db')
    conn.execute("ATTACH DATABASE '{}' AS rd_db".format(details_db_path))
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

# New dropdown for metric selection.
metric_options = [
    {'label': "Top30 Count Difference (%)", 'value': 'pct_top30_pct_diff'},
    {'label': "FIS Points Difference (%)", 'value': 'fis_points_pct_diff'},
    {'label': "Cup Points Difference (%)", 'value': 'cup_points_pct_diff'}
]

app.layout = html.Div([
    html.H1("Home vs. Away Performance Comparison by Nation"),
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
                value='fis_points_pct_diff',  # default metric
                clearable=False
            )
        ], style={'width': '300px', 'display': 'inline-block', 'marginLeft': '20px'})
    ]),
    html.Br(),
    html.Div([
        dcc.Graph(id='faceted-chart')
    ]),
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
    
    # Create a faceted bar chart:
    # Facet by discipline (columns) and sex (rows), x-axis: competitor_country, y-axis: selected metric.
    fig = px.bar(filtered, x='competitor_country', y=selected_metric,
                 facet_row='sex', facet_col='discipline',
                 color='competitor_country',
                 title=f"Home vs. Away Difference in {selected_metric}",
                 text=selected_metric)
    
    # Force bar color mapping: Men's in blue, Women's in pink.
    # Since competitor_country might be many different colors, you might use facet_row to indicate sex.
    # Alternatively, you can override each facet separately if needed.
    
    fig.update_layout(showlegend=False)
    # Update text to display rounded values.
    fig.update_traces(texttemplate='%{text:.2f}', textposition='auto')
    
    table_data = filtered.sort_values(['competitor_country', 'discipline']).to_dict('records')
    return fig, table_data

if __name__ == '__main__':
    app.run_server(debug=True)
