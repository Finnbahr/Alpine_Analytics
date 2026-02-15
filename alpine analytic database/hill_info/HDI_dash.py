import dash
from dash import dcc, html, dash_table, Input, Output
import plotly.express as px
import pandas as pd
import sqlite3

# ---------------------------
# Data Loading Function
# ---------------------------
def load_hdi_data(db_path="event_fis_info_aggregate.db", table_name="hdi"):
    """
    Connect to the aggregate database and load the HDI table.
    Returns a DataFrame with the HDI data.
    """
    try:
        conn = sqlite3.connect(db_path)
        df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
        conn.close()
        return df
    except Exception as e:
        print("Error loading HDI data:", e)
        return pd.DataFrame()

# Load HDI data from the aggregate database.
df_hdi = load_hdi_data()

# If needed, ensure the numeric columns are of proper type.
# (You may also add additional cleaning here.)
for col in ["race_count", "winning_time_norm", "gate_count_norm", "start_altitude_norm",
            "vertical_drop_norm", "dnf_rate_norm", "hill_difficulty_index"]:
    if col in df_hdi.columns:
        df_hdi[col] = pd.to_numeric(df_hdi[col], errors="coerce")

# Prepare filter dropdown options.
discipline_options = [{'label': d, 'value': d} for d in sorted(df_hdi['discipline'].dropna().unique())]
country_options = [{'label': c, 'value': c} for c in sorted(df_hdi['country'].dropna().unique())]
location_options = [{'label': loc, 'value': loc} for loc in sorted(df_hdi['location'].dropna().unique())]

# ---------------------------
# Dash App Setup
# ---------------------------
app = dash.Dash(__name__)
server = app.server

app.layout = html.Div([
    html.H1("Hill Difficulty Index Dashboard"),
    html.Div([
        html.Div([
            html.Label("Select Discipline:"),
            dcc.Dropdown(
                id='discipline-dropdown',
                options=discipline_options,
                multi=True,
                placeholder="Select discipline(s)..."
            )
        ], style={'width': '300px', 'display': 'inline-block', 'marginRight': '20px'}),
        html.Div([
            html.Label("Select Country:"),
            dcc.Dropdown(
                id='country-dropdown',
                options=country_options,
                multi=True,
                placeholder="Select country(s)..."
            )
        ], style={'width': '300px', 'display': 'inline-block', 'marginRight': '20px'}),
        html.Div([
            html.Label("Select Location:"),
            dcc.Dropdown(
                id='location-dropdown',
                options=location_options,
                multi=True,
                placeholder="Select location(s)..."
            )
        ], style={'width': '300px', 'display': 'inline-block'})
    ], style={'padding': '20px', 'backgroundColor': '#f9f9f9'}),
    html.Br(),
    dcc.Graph(id='hdi-scatter'),
    html.Br(),
    html.H3("HDI Metrics Table"),
    dash_table.DataTable(
        id='hdi-table',
        columns=[{"name": col, "id": col} for col in df_hdi.columns],
        data=df_hdi.to_dict('records'),
        page_size=10,
        style_table={'overflowX': 'auto'},
        style_cell={'textAlign': 'center'}
    )
])

@app.callback(
    [Output('hdi-scatter', 'figure'),
     Output('hdi-table', 'data')],
    [Input('discipline-dropdown', 'value'),
     Input('country-dropdown', 'value'),
     Input('location-dropdown', 'value')]
)
def update_dashboard(selected_disciplines, selected_countries, selected_locations):
    filtered_df = df_hdi.copy()
    if selected_disciplines:
        filtered_df = filtered_df[filtered_df['discipline'].isin(selected_disciplines)]
    if selected_countries:
        filtered_df = filtered_df[filtered_df['country'].isin(selected_countries)]
    if selected_locations:
        filtered_df = filtered_df[filtered_df['location'].isin(selected_locations)]
    
    # Create a scatter plot: x = Hill Difficulty Index, y = Race Count.
    fig = px.scatter(filtered_df, x='hill_difficulty_index', y='race_count', color='location',
                     hover_data=['country', 'discipline', 'homologation_number'],
                     title="Hill Difficulty Index vs. Race Count",
                     template="plotly_white")
    
    # Optionally, update marker properties.
    fig.update_traces(marker=dict(size=12, line=dict(width=1, color='DarkSlateGrey')))
    
    table_data = filtered_df.to_dict('records')
    return fig, table_data

if __name__ == '__main__':
    app.run_server(debug=True)
