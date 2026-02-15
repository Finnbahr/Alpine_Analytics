"""
Complete Dash dashboard for a single athlete (FIS code 6532086)
with data export to **Excel (.xlsx)** and **PDF (.pdf)**.

Extra requirements (install once):
    pip install openpyxl reportlab
"""
import io
import sqlite3

import dash
from dash import dcc, html, dash_table, Input, Output, State
import pandas as pd
import plotly.express as px

# -------- PDF helpers (ReportLab) -------------------------------------------
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors

# ---------------------------------------------------------------------------
# 1. Data-loading utilities
# ---------------------------------------------------------------------------
def load_athlete_data() -> pd.DataFrame:
    """Return yearly aggregates for athlete 6532086 from SQLite DB."""
    with sqlite3.connect("athlete_fis_information_aggregate.db") as conn:
        df = pd.read_sql_query(
            "SELECT * FROM basic_athlete_info_yearly WHERE fis_code='6532086'",
            conn,
        )

    # House-keeping
    if "last_updated" in df.columns:
        df = df.drop(columns=["last_updated"])
    df["race_year"] = df["race_year"].astype(str)
    return df


def dataframe_to_pdf_bytes(df: pd.DataFrame) -> bytes:
    """Render `df` as a simple table and return the PDF as bytes."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter, leftMargin=18, rightMargin=18)

    data = [list(df.columns)] + df.astype(str).values.tolist()

    table = Table(data, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("BOX", (0, 0), (-1, -1), 0.25, colors.grey),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
            ]
        )
    )
    doc.build([table])
    out = buf.getvalue()
    buf.close()
    return out


# ---------------------------------------------------------------------------
# 2. Data & static option lists
# ---------------------------------------------------------------------------
df = load_athlete_data()
year_opts = [{"label": y, "value": y} for y in sorted(df["race_year"].unique())]
disc_opts = [
    {"label": d, "value": d} for d in sorted(df["discipline"].dropna().unique())
]

# ---------------------------------------------------------------------------
# 3. Dash app setup
# ---------------------------------------------------------------------------
external_css = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]
app = dash.Dash(__name__, external_stylesheets=external_css)
server = app.server

app.layout = html.Div(
    style={
        "maxWidth": "1200px",
        "margin": "auto",
        "backgroundColor": "slategray",
        "color": "white",
        "padding": "20px",
    },
    children=[
        # -------------------------- Filters --------------------------
        html.Div(
            [
                html.Div(
                    [
                        html.Label(
                            "Select Race Year(s):",
                            style={"color": "white", "fontWeight": "bold"},
                        ),
                        dcc.Dropdown(
                            id="year-dropdown",
                            options=year_opts,
                            value=[opt["value"] for opt in year_opts],
                            multi=True,
                        ),
                    ],
                    style={"width": "45%", "display": "inline-block", "padding": "10px"},
                ),
                html.Div(
                    [
                        html.Label(
                            "Select Discipline(s):",
                            style={"color": "white", "fontWeight": "bold"},
                        ),
                        dcc.Dropdown(
                            id="discipline-dropdown",
                            options=disc_opts,
                            value=[opt["value"] for opt in disc_opts],
                            multi=True,
                        ),
                    ],
                    style={"width": "45%", "display": "inline-block", "padding": "10px"},
                ),
            ]
        ),
        html.Hr(style={"borderColor": "white"}),
        # ---------------------- Chart / Table grid -------------------
        html.Div(
            id="charts-container",
            children=[
                # Template for six metric panels
                *[
                    html.Div(
                        [
                            html.H3(title, style={"color": "black"}),
                            dcc.Graph(id=f"graph{i}"),
                            dash_table.DataTable(
                                id=f"table{i}",
                                columns=[{"name": c, "id": c} for c in df.columns],
                                data=[],
                                page_size=5,
                                style_table={"overflowX": "auto"},
                                style_cell={"textAlign": "center", "color": "black"},
                                style_header={
                                    "fontWeight": "bold",
                                    "backgroundColor": "lightgray",
                                },
                            ),
                        ],
                        style={
                            "backgroundColor": "white",
                            "margin": "10px",
                            "padding": "10px",
                            "borderRadius": "5px",
                        },
                    )
                    for i, title in enumerate(
                        [
                            "Mean FIS Points Trend",
                            "Race Count Trend",
                            "DNF Rate Trend",
                            "Mean Starting Position (Bib) Trend",
                            "Mean Rank Trend",
                            "Std Deviation of FIS Points Trend",
                        ],
                        start=1,
                    )
                ]
            ],
        ),
        # --------------------------- Export buttons ------------------
        html.Div(
            [
                html.Button(
                    "Export to Excel",
                    id="btn-excel",
                    n_clicks=0,
                    style={"fontSize": "1.1em", "margin": "0 10px", "padding": "10px 20px"},
                ),
                dcc.Download(id="download-excel"),
                html.Button(
                    "Export to PDF",
                    id="btn-pdf",
                    n_clicks=0,
                    style={"fontSize": "1.1em", "margin": "0 10px", "padding": "10px 20px"},
                ),
                dcc.Download(id="download-pdf"),
            ],
            style={"textAlign": "center", "padding": "20px"},
        ),
    ],
)

# ---------------------------------------------------------------------------
# 4. Callbacks
# ---------------------------------------------------------------------------
@app.callback(
    [
        Output("graph1", "figure"),
        Output("table1", "data"),
        Output("graph2", "figure"),
        Output("table2", "data"),
        Output("graph3", "figure"),
        Output("table3", "data"),
        Output("graph4", "figure"),
        Output("table4", "data"),
        Output("graph5", "figure"),
        Output("table5", "data"),
        Output("graph6", "figure"),
        Output("table6", "data"),
    ],
    [Input("year-dropdown", "value"), Input("discipline-dropdown", "value")],
)
def update_dashboard(selected_years, selected_disciplines):
    # Filter
    filt = (
        df
        if not selected_years or not selected_disciplines
        else df[
            df["race_year"].isin(selected_years)
            & df["discipline"].isin(selected_disciplines)
        ]
    )

    # Helper to guard empty data
    def line_fig(y_col, title):
        if not filt.empty and y_col in filt.columns:
            return px.line(
                filt,
                x="race_year",
                y=y_col,
                color="discipline",
                markers=True,
                title=title,
            )
        return px.line(title="No data available")

    def bar_fig(y_col, title):
        if not filt.empty and y_col in filt.columns:
            return px.bar(
                filt,
                x="race_year",
                y=y_col,
                color="discipline",
                barmode="group",
                title=title,
            )
        return px.bar(title="No data available")

    figs = [
        line_fig("mean_fis_points", "Mean FIS Points Trend"),
        bar_fig("race_count", "Race Count Trend"),
        line_fig("dnf_rate", "DNF Rate Trend"),
        line_fig("mean_bib", "Mean Starting Position (Bib) Trend"),
        line_fig("mean_rank", "Mean Rank Trend"),
        line_fig("std_fis_points", "Std Deviation of FIS Points Trend"),
    ]

    tbl = filt.to_dict("records")
    # Interleave figures & table data for the 6 panels
    out = []
    for f in figs:
        out.extend([f, tbl])
    return out


@app.callback(
    Output("download-excel", "data"),
    Input("btn-excel", "n_clicks"),
    State("year-dropdown", "value"),
    State("discipline-dropdown", "value"),
    prevent_initial_call=True,
)
def export_excel(n_clicks, years, disciplines):
    filt = (
        df
        if not years or not disciplines
        else df[df["race_year"].isin(years) & df["discipline"].isin(disciplines)]
    )
    return dcc.send_data_frame(
        filt.to_excel,
        "filtered_athlete_data.xlsx",
        index=False,
        sheet_name="FilteredData",
    )


@app.callback(
    Output("download-pdf", "data"),
    Input("btn-pdf", "n_clicks"),
    State("year-dropdown", "value"),
    State("discipline-dropdown", "value"),
    prevent_initial_call=True,
)
def export_pdf(n_clicks, years, disciplines):
    filt = (
        df
        if not years or not disciplines
        else df[df["race_year"].isin(years) & df["discipline"].isin(disciplines)]
    )
    pdf_bytes = dataframe_to_pdf_bytes(filt)
    return dcc.send_bytes(pdf_bytes, filename="filtered_athlete_data.pdf")


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app.run_server(debug=True)
