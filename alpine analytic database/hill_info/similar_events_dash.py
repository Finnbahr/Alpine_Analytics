import dash
from dash import dcc, html, dash_table, Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
import sqlite3
import base64
import numpy as np
from dash.exceptions import PreventUpdate

# --------------------------------------------------
# 1. Load Data
# --------------------------------------------------
def load_hill_data():
    """
    Connect to event_fis_info_aggregate.db and load the basic_hill_info table.
    Expects columns like:
      discipline, country, location, homologation_number,
      mean_winning_time_min (or mean_winning_time),
      mean_gate_count, mean_start_altitude, mean_vertical_drop,
      mean_dnf_rate, mean_fis_points, etc.
    """
    conn = sqlite3.connect("event_fis_info_aggregate.db")
    df = pd.read_sql_query("SELECT * FROM basic_hill_info", conn)
    conn.close()
    return df

df_hill = load_hill_data()

# Decide which winning time column to use.
if 'mean_winning_time_min' in df_hill.columns:
    win_time_col = 'mean_winning_time_min'
elif 'mean_winning_time' in df_hill.columns:
    win_time_col = 'mean_winning_time'
else:
    win_time_col = None  # fallback if neither exists

# Build the list of potential columns for the similarity metric.
potential_metrics = [
    win_time_col,           # might be None
    'mean_gate_count',
    'mean_start_altitude',
    'mean_vertical_drop',
    'mean_dnf_rate',
    'mean_fis_points'
]
# Filter out any that don't exist or are None.
similarity_metrics = [m for m in potential_metrics if m and m in df_hill.columns]

# We'll display these columns plus similarity_score in the final table (if they exist).
display_columns = [
    'discipline', 'country', 'location', 'homologation_number'
]
display_columns += similarity_metrics  # only add existing ones
display_columns.append('similarity_score')

# --------------------------------------------------
# 2. Similarity Function
# --------------------------------------------------
def compute_similarity(ref_row, cand_row, tolerance=0.5):
    """
    For each metric in similarity_metrics, compute absolute percentage difference:
        diff = |cand - ref| / |ref|
    If any diff > tolerance, return np.inf (exclude).
    Otherwise, return the sum of diffs (lower = more similar).
    """
    total_diff = 0
    for m in similarity_metrics:
        ref_val = ref_row.get(m, None)
        cand_val = cand_row.get(m, None)
        if ref_val is None or ref_val == 0:
            # If reference is zero or missing, skip this metric.
            continue
        diff = abs(cand_val - ref_val) / abs(ref_val)
        if diff > tolerance:
            return np.inf
        total_diff += diff
    return total_diff

# --------------------------------------------------
# 3. Dash App Setup
# --------------------------------------------------
external_stylesheets = [dbc.themes.CYBORG]
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server

# Encode the logo image for the header.
with open('alpine_analytics_logo.png', 'rb') as f:
    encoded_logo = base64.b64encode(f.read()).decode('ascii')

# Prepare discipline options
discipline_opts = [{'label': d, 'value': d} for d in sorted(df_hill['discipline'].dropna().unique())]

app.layout = dbc.Container([
    # Header Row
    dbc.Row([
        dbc.Col([
            html.H1("Similar Hills Dashboard", style={'margin': '0'}),
            html.H3("Find hills with similar event characteristics", style={'margin': '0'})
        ], width=8),
        dbc.Col(html.Img(src='data:image/png;base64,{}'.format(encoded_logo),
                         style={'height': '100px', 'width': 'auto'}),
                width=4, style={'textAlign': 'right'})
    ], className="mb-4"),
    html.Hr(style={'borderColor': 'white'}),

    # Filters: Discipline, Country, Location, Homologation
    dbc.Row([
        dbc.Col([
            html.Label("Select Discipline:", style={'color': 'white'}),
            dcc.Dropdown(
                id='discipline-dropdown',
                options=discipline_opts,
                value=discipline_opts[0]['value'] if discipline_opts else None,
                clearable=False,
                style={'width': '100%'}
            )
        ], width=3),
        dbc.Col([
            html.Label("Select Country:", style={'color': 'white'}),
            dcc.Dropdown(id='country-dropdown', options=[], value=None, clearable=False, style={'width': '100%'})
        ], width=3),
        dbc.Col([
            html.Label("Select Reference Location:", style={'color': 'white'}),
            dcc.Dropdown(id='location-dropdown', options=[], value=None, clearable=False, style={'width': '100%'})
        ], width=3),
        dbc.Col([
            html.Label("Select Homologation #:", style={'color': 'white'}),
            dcc.Dropdown(id='homologation-dropdown', options=[], value=None, clearable=False, style={'width': '100%'})
        ], width=3)
    ], className="mb-4"),

    dbc.Row([
        dbc.Col(html.Button("Find 10 Most Similar Hills", id="find-button", n_clicks=0,
                            style={'fontSize': '1.2em', 'padding': '10px 20px'}),
                width={"size": 4, "offset": 4})
    ], className="mb-4", style={'textAlign': 'center'}),

    # Reference Hill Info
    dbc.Row([
        dbc.Col(html.Div(id='reference-info', style={
            'padding': '10px', 'backgroundColor': 'lightgray', 'borderRadius': '5px'
        }))
    ], className="mb-4"),

    # Results Table
    dbc.Row([
        dbc.Col(dash_table.DataTable(
            id='results-table',
            columns=[{"name": c, "id": c} for c in display_columns if c in df_hill.columns or c == 'similarity_score'],
            data=[],
            page_size=10,
            style_table={'overflowX': 'auto'},
            style_cell={'textAlign': 'center', 'color': 'black'},
            style_header={'fontWeight': 'bold', 'backgroundColor': 'lightgray'}
        ), width=12)
    ], className="mb-4"),

    # Export Button
    dbc.Row([
        dbc.Col(html.Button("Export Results to CSV", id="export-button", n_clicks=0,
                            style={'fontSize': '1.1em', 'padding': '10px 20px'}),
                width={"size": 4, "offset": 4})
    ], className="mb-4", style={'textAlign': 'center'}),
    dcc.Download(id="download-dataframe-csv")

], fluid=True, style={'backgroundColor': 'slategray', 'color': 'white', 'padding': '20px'})

# --------------------------------------------------
# 4. Callbacks for Cascading Dropdowns
# --------------------------------------------------
@app.callback(
    [Output('country-dropdown', 'options'),
     Output('country-dropdown', 'value')],
    [Input('discipline-dropdown', 'value')]
)
def update_country(selected_disc):
    if not selected_disc:
        raise PreventUpdate
    dff = df_hill[df_hill['discipline'] == selected_disc]
    countries = sorted(dff['country'].dropna().unique())
    if not countries:
        return [], None
    opts = [{'label': c, 'value': c} for c in countries]
    return opts, opts[0]['value']

@app.callback(
    [Output('location-dropdown', 'options'),
     Output('location-dropdown', 'value')],
    [Input('discipline-dropdown', 'value'),
     Input('country-dropdown', 'value')]
)
def update_location(selected_disc, selected_country):
    if not selected_disc or not selected_country:
        raise PreventUpdate
    dff = df_hill[(df_hill['discipline'] == selected_disc) & (df_hill['country'] == selected_country)]
    locs = sorted(dff['location'].dropna().unique())
    if not locs:
        return [], None
    opts = [{'label': loc, 'value': loc} for loc in locs]
    return opts, opts[0]['value']

@app.callback(
    [Output('homologation-dropdown', 'options'),
     Output('homologation-dropdown', 'value')],
    [Input('discipline-dropdown', 'value'),
     Input('country-dropdown', 'value'),
     Input('location-dropdown', 'value')]
)
def update_homologation(selected_disc, selected_country, selected_loc):
    if not (selected_disc and selected_country and selected_loc):
        raise PreventUpdate
    dff = df_hill[(df_hill['discipline'] == selected_disc) &
                  (df_hill['country'] == selected_country) &
                  (df_hill['location'] == selected_loc)]
    homos = sorted(dff['homologation_number'].dropna().unique())
    if not homos:
        return [], None
    opts = [{'label': str(h), 'value': str(h)} for h in homos]
    return opts, opts[0]['value']

# --------------------------------------------------
# 5. Compute and Display Similar Hills
# --------------------------------------------------
@app.callback(
    [Output('reference-info', 'children'),
     Output('results-table', 'data')],
    [Input('discipline-dropdown', 'value'),
     Input('country-dropdown', 'value'),
     Input('location-dropdown', 'value'),
     Input('homologation-dropdown', 'value'),
     Input("find-button", "n_clicks")]
)
def find_similar_hills(selected_disc, selected_country, selected_loc, selected_homo, n_clicks):
    if n_clicks == 0:
        return "No reference hill selected yet.", []
    if not (selected_disc and selected_country and selected_loc and selected_homo):
        raise PreventUpdate
    
    ref_df = df_hill[(df_hill['discipline'] == selected_disc) &
                     (df_hill['country'] == selected_country) &
                     (df_hill['location'] == selected_loc) &
                     (df_hill['homologation_number'].astype(str) == selected_homo)]
    if ref_df.empty:
        return "Reference hill not found.", []
    
    ref_row = ref_df.iloc[0]
    
    # Build reference hill info.
    # We'll use .get(key, 'N/A') so that if the column is missing or NaN, we display "N/A".
    def format_val(key):
        val = ref_row.get(key, "N/A")
        return val if pd.notnull(val) else "N/A"
    
    ref_info = html.Div([
        html.H4("Reference Hill", style={'color': 'black'}),
        html.P(f"Location: {format_val('location')}", style={'color': 'black'}),
        html.P(f"Homologation #: {format_val('homologation_number')}", style={'color': 'black'}),
        html.P(f"Discipline: {format_val('discipline')}", style={'color': 'black'}),
        html.P(f"Country: {format_val('country')}", style={'color': 'black'}),
        html.P(f"Mean Winning Time: {format_val(win_time_col)}", style={'color': 'black'}),
        html.P(f"Mean Gate Count: {format_val('mean_gate_count')}", style={'color': 'black'}),
        html.P(f"Mean Start Altitude: {format_val('mean_start_altitude')}", style={'color': 'black'}),
        html.P(f"Mean Vertical Drop: {format_val('mean_vertical_drop')}", style={'color': 'black'}),
        html.P(f"Mean DNF Rate: {format_val('mean_dnf_rate')}", style={'color': 'black'}),
        html.P(f"Mean FIS Points: {format_val('mean_fis_points')}", style={'color': 'black'})
    ], style={'backgroundColor': 'lightgray', 'padding': '10px', 'borderRadius': '5px'})
    
    # Filter the DataFrame to the same discipline and country, excluding the reference hill.
    dff = df_hill[(df_hill['discipline'] == selected_disc) &
                  (df_hill['country'] == selected_country)].copy()
    dff = dff[~((dff['location'] == ref_row['location']) &
                (dff['homologation_number'].astype(str) == selected_homo))]
    
    # Compute similarity for each candidate.
    def similarity_score(row):
        return compute_similarity(ref_row, row, tolerance=0.5)
    
    dff['similarity_score'] = dff.apply(similarity_score, axis=1)
    # Keep only finite scores (meaning all metrics within ±5%).
    dff = dff[dff['similarity_score'] != np.inf]
    # Sort ascending and take up to 10.
    dff = dff.sort_values(by='similarity_score').head(10)
    dff['similarity_score'] = dff['similarity_score'].round(2)
    
    # Show only the columns we want in the final table, if they exist.
    existing_cols = [c for c in display_columns if c in dff.columns]
    dff = dff[existing_cols]
    
    return ref_info, dff.to_dict('records')

# --------------------------------------------------
# 6. Export Data as CSV
# --------------------------------------------------
@app.callback(
    Output("download-dataframe-csv", "data"),
    Input("export-button", "n_clicks"),
    [State('discipline-dropdown', 'value'),
     State('country-dropdown', 'value'),
     State('location-dropdown', 'value'),
     State('homologation-dropdown', 'value')],
    prevent_initial_call=True
)
def export_csv(n_clicks, selected_disc, selected_country, selected_loc, selected_homo):
    if not (selected_disc and selected_country and selected_loc and selected_homo):
        raise PreventUpdate
    
    ref_df = df_hill[(df_hill['discipline'] == selected_disc) &
                     (df_hill['country'] == selected_country) &
                     (df_hill['location'] == selected_loc) &
                     (df_hill['homologation_number'].astype(str) == selected_homo)]
    if ref_df.empty:
        raise PreventUpdate
    
    ref_row = ref_df.iloc[0]
    
    dff = df_hill[(df_hill['discipline'] == selected_disc) &
                  (df_hill['country'] == selected_country)].copy()
    dff = dff[~((dff['location'] == ref_row['location']) &
                (dff['homologation_number'].astype(str) == selected_homo))]
    
    def similarity_score(row):
        return compute_similarity(ref_row, row, tolerance=0.5)
    
    dff['similarity_score'] = dff.apply(similarity_score, axis=1)
    dff = dff[dff['similarity_score'] != np.inf]
    dff = dff.sort_values(by='similarity_score').head(10)
    dff['similarity_score'] = dff['similarity_score'].round(2)
    
    existing_cols = [c for c in display_columns if c in dff.columns]
    dff = dff[existing_cols]
    
    return dcc.send_data_frame(dff.to_csv, "similar_hills.csv", index=False)

if __name__ == '__main__':
    app.run_server(debug=True)
