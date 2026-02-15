import sqlite3
import pandas as pd
import dash
from dash import dcc, html, Input, Output
import plotly.express as px

def load_hot_streaks_data():
    """
    Load the hot streak data from the aggregate database.
    Assumes the table 'hot_streaks' includes the following columns:
      - name: Athlete's name.
      - date: Race date.
      - momentum_z: Standardized momentum (Z Momentum).
      - momentum_fis: Momentum based on raw FIS points.
    """
    with sqlite3.connect("athlete_fis_information_aggregate.db") as conn:
        df = pd.read_sql_query("""
            SELECT name, date, momentum_z, momentum_fis
            FROM hot_streaks
            WHERE momentum_z IS NOT NULL AND momentum_fis IS NOT NULL
        """, conn)
    df['date'] = pd.to_datetime(df['date'])
    return df

# Load data from hot_streaks table.
df_hot = load_hot_streaks_data()

# Get unique athlete names for the dropdown.
athlete_names = sorted(df_hot['name'].dropna().unique())

# Initialize the Dash app.
app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("Athlete Hot Streak Dashboard"),
    html.Div([
        html.Label("Select Athlete:"),
        dcc.Dropdown(
            id='athlete-dropdown',
            options=[{'label': name, 'value': name} for name in athlete_names],
            value=athlete_names[0] if athlete_names else None,
            style={'width': '300px'}
        )
    ], style={'padding': '10px'}),
    html.Div([
        dcc.Graph(id='z-momentum-graph'),
        dcc.Graph(id='fis-momentum-graph')
    ])
])

@app.callback(
    [Output('z-momentum-graph', 'figure'),
     Output('fis-momentum-graph', 'figure')],
    [Input('athlete-dropdown', 'value')]
)
def update_graphs(selected_name):
    filtered_df = df_hot[df_hot['name'] == selected_name].sort_values(by='date')
    
    # Create the Z Momentum graph.
    fig_z = px.scatter(filtered_df,
                       x='date',
                       y='momentum_z',
                       title=f"{selected_name} - Z Momentum Over Career",
                       labels={'date': 'Race Date', 'momentum_z': 'Z Momentum'},
                       color='momentum_z',
                       color_continuous_scale=px.colors.sequential.Viridis)
    fig_z.update_traces(mode='lines+markers')
    fig_z.update_layout(
        xaxis=dict(dtick="M1", tickformat="%b %Y"),
        margin=dict(l=60, r=60, t=60, b=60)
    )
    
    # Create the FIS Momentum graph.
    fig_fis = px.scatter(filtered_df,
                         x='date',
                         y='momentum_fis',
                         title=f"{selected_name} - FIS Momentum Over Career",
                         labels={'date': 'Race Date', 'momentum_fis': 'FIS Momentum'},
                         color='momentum_fis',
                         color_continuous_scale=px.colors.sequential.Plasma)
    fig_fis.update_traces(mode='lines+markers')
    fig_fis.update_layout(
        xaxis=dict(dtick="M1", tickformat="%b %Y"),
        margin=dict(l=60, r=60, t=60, b=60)
    )
    
    return fig_z, fig_fis

if __name__ == '__main__':
    app.run_server(debug=True)
