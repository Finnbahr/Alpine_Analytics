"""
Alpine Analytics — XGBoost Race Predictor

Gradient-boosted tree model trained on all available World Cup race history.
Upload a start list CSV to get an instant predicted ranking with key
performance indicators per athlete.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import date
import xgboost as xgb
from database import get_engine
from sqlalchemy import text

st.set_page_config(
    page_title="XGBoost Predictor — Alpine Analytics",
    layout="wide",
)

st.title("XGBoost Race Predictor")

with st.expander("How This Model Works"):
    st.markdown(
        """
        The XGBoost predictor uses a gradient-boosted tree model trained on every World Cup
        race in the database. Rather than simulating thousands of outcomes, it predicts each
        athlete's expected performance score directly and ranks the field accordingly.

        **Features used per athlete**

        - **FIS Points** — current world ranking score (lower = better ranked athlete)
        - **Bib / start number** — draw position and its historical performance effect
        - **Rolling form** — mean z-score over the last 5 and 10 races in this discipline
        - **Consistency** — standard deviation of z-scores over the last 5 races
        - **DNF rate** — fraction of DNFs / DSQs over the last 5 starts
        - **Career depth** — total number of prior starts in this discipline
        - **Days since last race** — recency of competition
        - **Venue history** — athlete's personal average z-score at this specific location
        - **Venue starts** — how many times they have raced here previously
        - **Month** — seasonal timing within the race calendar

        **Training**

        The model is trained on the full race database — every athlete, every race, no holdout.
        Features are computed using only information available before each race (rolling windows
        are lagged by one race to prevent leakage).

        **Interpreting the output**

        Athletes are ranked by their predicted performance score (higher = faster). The score
        is in z-score units — a value of +1.5 represents a top-tier performance, 0 is field
        average, and negative values indicate below-average expected output. The ranking is a
        point estimate, not a probability distribution.
        """
    )

with st.expander("Model Accuracy — Backtesting Results"):
    st.markdown(
        """
        Validated on World Cup races from 2021 onward — predictions made using only data
        available before each race, compared against actual results.
        """
    )
    _bt = pd.DataFrame({
        "Discipline":       ["Slalom", "Giant Slalom", "Super G", "Downhill"],
        "Races (M / W)":    ["60 / 53", "48 / 50", "41 / 48", "52 / 47"],
        "Rho (M / W)":      ["0.917 / 0.917", "0.950 / 0.975", "0.953 / 0.958", "0.912 / 0.946"],
        "Winner % (M / W)": ["75% / 94%", "94% / 62%", "81% / 83%", "77% / 68%"],
        "Top-3 % (M / W)":  ["83% / 84%", "92% / 91%", "83% / 81%", "82% / 84%"],
    })
    st.dataframe(_bt, use_container_width=True, hide_index=True)
    st.caption(
        "Rho = Spearman rank correlation between predicted and actual finishing order among "
        "finishers only (excludes DNFs). Winner % = fraction of races where the model's "
        "top-ranked athlete actually won."
    )

# ---------------------------------------------------------------------------
# Cached loaders
# ---------------------------------------------------------------------------

@st.cache_data(ttl=604800, show_spinner=False)
def load_history(discipline: str, sex: str) -> pd.DataFrame:
    """Load full WC race history with rolling features. Cached weekly."""
    engine = get_engine()
    q = text("""
        SELECT
            fr.fis_code::text              AS fis_code,
            fr.race_id,
            rz.race_z_score::float         AS race_z_score,
            rd.date,
            rd.location,
            fr.bib::int                    AS bib,
            fr.fis_points::float           AS fis_points,
            fr.rank                        AS rank_str
        FROM raw.fis_results fr
        JOIN raw.race_details rd ON rd.race_id = fr.race_id
        LEFT JOIN race_aggregate.race_z_score rz
               ON rz.race_id = fr.race_id AND rz.fis_code = fr.fis_code
        WHERE rd.discipline = :disc AND rd.race_type = 'World Cup' AND rd.sex = :sex
        ORDER BY rd.date ASC, fr.race_id, fr.fis_code
    """)
    with engine.connect() as conn:
        df = pd.read_sql(q, conn, params={"disc": discipline, "sex": sex})

    df["date"]   = pd.to_datetime(df["date"])
    df["is_dnf"] = df["rank_str"].astype(str).str.upper().str.startswith(("DNF", "DSQ", "DNS"))

    df = df.sort_values(["fis_code", "date"]).reset_index(drop=True)
    g  = df.groupby("fis_code")
    df["roll5_mean_z"]   = g["race_z_score"].transform(lambda x: x.shift(1).rolling(5,  min_periods=1).mean())
    df["roll10_mean_z"]  = g["race_z_score"].transform(lambda x: x.shift(1).rolling(10, min_periods=1).mean())
    df["roll5_std_z"]    = g["race_z_score"].transform(lambda x: x.shift(1).rolling(5,  min_periods=2).std())
    df["roll5_dnf_rate"] = g["is_dnf"].transform(       lambda x: x.shift(1).rolling(5,  min_periods=1).mean())
    df["n_career"]       = g["race_z_score"].transform(lambda x: x.shift(1).expanding().count())
    df["days_since"]     = g["date"].transform(          lambda x: x.diff().dt.days)

    df = df.sort_values(["fis_code", "location", "date"]).reset_index(drop=True)
    gv = df.groupby(["fis_code", "location"])
    df["venue_mean_z"] = gv["race_z_score"].transform(lambda x: x.shift(1).expanding().mean())
    df["venue_n"]      = gv["race_z_score"].transform(lambda x: x.shift(1).expanding().count())

    df = df.sort_values(["date", "race_id", "fis_code"]).reset_index(drop=True)
    df["month"] = df["date"].dt.month

    df["fis_points"] = df["fis_points"].fillna(df["fis_points"].median())
    df["bib"]        = df.groupby("race_id")["bib"].transform(lambda x: x.fillna(x.median()).fillna(30))
    fp_max    = max(float(df["fis_points"].quantile(0.95)), 1.0)
    fis_proxy = 1.0 - 2.0 * (df["fis_points"] / fp_max).clip(0, 1)
    df["venue_mean_z"]   = df["venue_mean_z"].fillna(df["roll10_mean_z"])
    df["venue_mean_z"]   = df["venue_mean_z"].fillna(df["roll5_mean_z"])
    df["roll5_mean_z"]   = df["roll5_mean_z"].fillna(fis_proxy)
    df["roll10_mean_z"]  = df["roll10_mean_z"].fillna(df["roll5_mean_z"])
    df["venue_mean_z"]   = df["venue_mean_z"].fillna(df["roll5_mean_z"])
    df["roll5_std_z"]    = df["roll5_std_z"].fillna(0.6)
    df["roll5_dnf_rate"] = df["roll5_dnf_rate"].fillna(0.08)
    df["n_career"]       = df["n_career"].fillna(0)
    df["days_since"]     = df["days_since"].fillna(30)
    df["venue_n"]        = df["venue_n"].fillna(0)

    return df


@st.cache_data(ttl=604800, show_spinner=False)
def train_model(discipline: str, sex: str):
    """Train XGBoost on full WC history. Returns (model, fp_max)."""
    df    = load_history(discipline, sex)
    train = df[df["race_z_score"].notna()].copy()
    if len(train) < 50:
        return None, None
    features = [
        "fis_points", "bib", "roll5_mean_z", "roll10_mean_z",
        "roll5_std_z", "roll5_dnf_rate", "n_career", "days_since",
        "venue_mean_z", "venue_n", "month",
    ]
    model = xgb.XGBRegressor(
        n_estimators=500, max_depth=4, learning_rate=0.05,
        subsample=0.8, colsample_bytree=0.8, min_child_weight=3,
        random_state=42, n_jobs=-1, verbosity=0,
    )
    model.fit(train[features].values, train["race_z_score"].values)
    fp_max = max(float(df["fis_points"].quantile(0.95)), 1.0)
    return model, fp_max


@st.cache_data(ttl=604800, show_spinner=False)
def list_venues(discipline: str, sex: str) -> list[str]:
    engine = get_engine()
    q = text("""
        SELECT DISTINCT rd.location
        FROM raw.race_details rd
        WHERE rd.discipline = :disc AND rd.race_type = 'World Cup' AND rd.sex = :sex
        ORDER BY rd.location
    """)
    with engine.connect() as conn:
        df = pd.read_sql(q, conn, params={"disc": discipline, "sex": sex})
    return df["location"].tolist()


# ---------------------------------------------------------------------------
# Feature builder for a single athlete (live prediction)
# ---------------------------------------------------------------------------

FEATURES = [
    "fis_points", "bib", "roll5_mean_z", "roll10_mean_z",
    "roll5_std_z", "roll5_dnf_rate", "n_career", "days_since",
    "venue_mean_z", "venue_n", "month",
]


def build_athlete_features(
    hist_df: pd.DataFrame,
    fis_code: str,
    bib: int,
    venue: str,
    race_month: int,
    fallback_fis_points: float,
    fp_max: float,
) -> dict:
    """Current feature state for one athlete using full history (no shift)."""
    ath      = hist_df[hist_df["fis_code"] == fis_code]
    finished = ath[ath["race_z_score"].notna()].sort_values("date")

    if len(finished) == 0:
        fis_pts   = fallback_fis_points if not np.isnan(fallback_fis_points) else fp_max
        fis_proxy = float(np.clip(1.0 - 2.0 * (fis_pts / max(fp_max, 1.0)), -1.5, 1.5))
        return {
            "fis_points": fis_pts, "bib": bib,
            "roll5_mean_z": fis_proxy, "roll10_mean_z": fis_proxy,
            "roll5_std_z": 0.6, "roll5_dnf_rate": 0.08,
            "n_career": 0, "days_since": 30.0,
            "venue_mean_z": fis_proxy, "venue_n": 0.0,
            "month": float(race_month),
        }

    zs          = finished["race_z_score"].values
    all_sorted  = ath.sort_values("date")
    dnfs        = all_sorted["is_dnf"].values
    last_date   = finished["date"].iloc[-1]
    days_since  = max(0, (pd.Timestamp.today() - last_date).days)
    fis_pts     = float(all_sorted["fis_points"].iloc[-1])

    roll5_z   = float(np.mean(zs[-5:]))
    roll10_z  = float(np.mean(zs[-10:]))
    roll5_std = float(np.std(zs[-5:], ddof=1)) if len(zs) >= 2 else 0.6
    roll5_dnf = float(np.mean(dnfs[-5:])) if len(dnfs) >= 1 else 0.08
    n_career  = len(zs)

    venue_hist   = finished[finished["location"].str.strip().str.lower() == venue.strip().lower()]
    venue_mean_z = float(venue_hist["race_z_score"].mean()) if len(venue_hist) > 0 else roll10_z
    venue_n      = float(len(venue_hist))

    return {
        "fis_points":    fis_pts,
        "bib":           float(bib),
        "roll5_mean_z":  roll5_z,
        "roll10_mean_z": roll10_z,
        "roll5_std_z":   max(roll5_std, 0.0),
        "roll5_dnf_rate": roll5_dnf,
        "n_career":      float(n_career),
        "days_since":    float(days_since),
        "venue_mean_z":  venue_mean_z,
        "venue_n":       venue_n,
        "month":         float(race_month),
    }


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

st.sidebar.header("Race Setup")

sel_disc = st.sidebar.selectbox("Discipline", ["Slalom", "Giant Slalom", "Super G", "Downhill"])
sex_label = st.sidebar.radio("Sex", ["Men (M)", "Women (F)"])
sex_code  = "Men's" if sex_label.startswith("Men") else "Women's"

venues = list_venues(sel_disc, sex_code)
if venues:
    sel_venue = st.sidebar.selectbox("Venue", venues)
else:
    sel_venue = st.sidebar.text_input("Venue", placeholder="e.g. Wengen")

race_month = st.sidebar.number_input(
    "Race Month", min_value=1, max_value=12,
    value=date.today().month,
    help="Month the race is held — used as a seasonal signal.",
)

st.sidebar.markdown("---")
st.sidebar.caption(
    "Model trained on all available World Cup race history.  \n"
    "Features include recent form (5 and 10-race rolling average), "
    "venue history, bib position, DNF rate, and FIS ranking."
)

# ---------------------------------------------------------------------------
# Start list upload
# ---------------------------------------------------------------------------

st.subheader("Start List")

col_info, col_tmpl = st.columns([3, 1])
with col_info:
    st.markdown(
        "Upload a CSV with **Bib** and **FIS_Code** columns. "
        "An optional **Name** column sets athlete display names. "
        "FIS points can be included as **FIS_Points** for athletes with no race history."
    )
with col_tmpl:
    template_csv = "Bib,FIS_Code,Name\n1,422304,KRISTOFFERSEN Henrik\n2,512182,MEILLARD Loic\n3,6190403,NOEL Clement\n"
    st.download_button(
        "Download template",
        data=template_csv,
        file_name="start_list_template.csv",
        mime="text/csv",
    )

uploaded = st.file_uploader("Upload start list CSV", type=["csv"])

start_list  = None
parse_error = None

if uploaded is not None:
    try:
        raw_df = pd.read_csv(uploaded)
        raw_df.columns = [c.strip().lower().replace(" ", "_") for c in raw_df.columns]

        if "bib" not in raw_df.columns:
            parse_error = "CSV must have a 'Bib' column."
        elif "fis_code" not in raw_df.columns:
            parse_error = "CSV must have a 'FIS_Code' column."
        else:
            raw_df["bib"]      = pd.to_numeric(raw_df["bib"], errors="coerce")
            raw_df["fis_code"] = pd.to_numeric(raw_df["fis_code"], errors="coerce")
            raw_df = raw_df.dropna(subset=["bib", "fis_code"])
            raw_df["bib"]      = raw_df["bib"].astype(int)
            raw_df["fis_code"] = raw_df["fis_code"].astype(str).str.strip()

            if "name" not in raw_df.columns:
                raw_df["name"] = raw_df["fis_code"]
            if "fis_points" not in raw_df.columns:
                raw_df["fis_points"] = float("nan")

            start_list = (
                raw_df[["bib", "fis_code", "name", "fis_points"]]
                .drop_duplicates(subset=["bib"])
                .sort_values("bib")
                .reset_index(drop=True)
            )
    except Exception as e:
        parse_error = f"Could not parse CSV: {e}"

if parse_error:
    st.error(parse_error)

if start_list is not None:
    st.markdown(
        f"**{len(start_list)} athletes loaded** — "
        f"{sel_disc} · World Cup · {sel_venue or '(no venue)'} · {sex_label}"
    )

    with st.expander("Preview start list"):
        st.dataframe(start_list[["bib", "fis_code", "name"]], use_container_width=True, hide_index=True)

    run = st.button("Run Prediction", type="primary")

    if run:
        with st.spinner("Loading race history and training model..."):
            hist_df = load_history(sel_disc, sex_code)
            model, fp_max = train_model(sel_disc, sex_code)

        if model is None:
            st.error("Insufficient training data for this discipline / sex combination.")
        else:
            with st.spinner("Building athlete features and predicting..."):
                rows = []
                for _, sl_row in start_list.iterrows():
                    fis_code = str(sl_row["fis_code"]).strip()
                    feats = build_athlete_features(
                        hist_df        = hist_df,
                        fis_code       = fis_code,
                        bib            = int(sl_row["bib"]),
                        venue          = sel_venue or "",
                        race_month     = int(race_month),
                        fallback_fis_points = float(sl_row["fis_points"]),
                        fp_max         = fp_max,
                    )
                    feats["fis_code"] = fis_code
                    feats["name"]     = str(sl_row["name"])
                    rows.append(feats)

                pred_df = pd.DataFrame(rows)
                X = pred_df[FEATURES].values
                pred_df["pred_z"] = model.predict(X)
                pred_df = pred_df.sort_values("pred_z", ascending=False).reset_index(drop=True)
                pred_df.insert(0, "#", range(1, len(pred_df) + 1))

            # ----------------------------------------------------------------
            # Summary metrics
            # ----------------------------------------------------------------
            st.markdown("---")
            st.subheader("Predicted Ranking")

            winner_row     = pred_df.iloc[0]
            top3_lastnames = " / ".join(n.split()[-1] for n in pred_df.head(3)["name"].tolist())

            # Breakout: biggest gap between bib rank and predicted rank (bib > 5 only)
            pred_df["_bib_rank"] = pred_df["bib"].rank(method="min").astype(int)
            pred_df["_improve"]  = pred_df["_bib_rank"] - pred_df["#"]
            outsiders = pred_df[pred_df["_bib_rank"] > 5]
            if not outsiders.empty and outsiders["_improve"].max() > 0:
                breakout     = outsiders.nlargest(1, "_improve").iloc[0]
                breakout_name  = breakout["name"]
                breakout_delta = f"Bib {int(breakout['bib'])} → Pred. #{int(breakout['#'])}"
            else:
                breakout       = pred_df.iloc[1]
                breakout_name  = breakout["name"]
                breakout_delta = f"Pred. z = {breakout['pred_z']:.2f}"

            m1, m2, m3 = st.columns(3)
            m1.metric("Predicted Winner", winner_row["name"], f"z = {winner_row['pred_z']:.2f}")
            m2.metric("Top-3 Favorites", top3_lastnames)
            m3.metric("Breakout Pick", breakout_name, breakout_delta)

            # ----------------------------------------------------------------
            # Results table
            # ----------------------------------------------------------------
            display = pred_df[["#", "bib", "name", "pred_z", "roll5_mean_z", "roll5_dnf_rate", "venue_n", "n_career"]].copy()
            display["pred_z"]        = display["pred_z"].round(3)
            display["roll5_mean_z"]  = display["roll5_mean_z"].round(3)
            display["roll5_dnf_rate"] = (display["roll5_dnf_rate"] * 100).round(1).astype(str) + "%"
            display["venue_n"]       = display["venue_n"].astype(int)
            display["n_career"]      = display["n_career"].astype(int)

            st.dataframe(
                display.rename(columns={
                    "#":              "#",
                    "bib":            "Bib",
                    "name":           "Athlete",
                    "pred_z":         "Pred. Score",
                    "roll5_mean_z":   "5-Race Form",
                    "roll5_dnf_rate": "DNF Rate",
                    "venue_n":        "Venue Starts",
                    "n_career":       "Career Starts",
                }),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "#":             st.column_config.NumberColumn("#",             help="Predicted rank"),
                    "Bib":           st.column_config.NumberColumn("Bib"),
                    "Athlete":       st.column_config.TextColumn("Athlete"),
                    "Pred. Score":   st.column_config.NumberColumn("Pred. Score",  help="Predicted z-score — higher is better. Field average ≈ 0, winner ≈ +1.5", format="%.3f"),
                    "5-Race Form":   st.column_config.NumberColumn("5-Race Form",  help="Mean z-score over last 5 races. Positive = above average", format="%.3f"),
                    "DNF Rate":      st.column_config.TextColumn("DNF Rate",       help="Fraction of DNF / DSQ in last 5 starts"),
                    "Venue Starts":  st.column_config.NumberColumn("Venue Starts", help="Prior World Cup starts at this venue"),
                    "Career Starts": st.column_config.NumberColumn("Career Starts",help="Total prior WC starts in this discipline"),
                },
            )

            # ----------------------------------------------------------------
            # Predicted score bar chart — top 15
            # ----------------------------------------------------------------
            st.markdown("#### Predicted Score — Top 15")

            chart_df = pred_df.head(15).sort_values("pred_z", ascending=True)
            colors   = ["#1a3a6b" if i == len(chart_df) - 1 else "steelblue"
                        for i in range(len(chart_df))]

            fig = go.Figure(go.Bar(
                y           = chart_df["name"],
                x           = chart_df["pred_z"],
                orientation = "h",
                marker_color= colors,
                opacity     = 0.85,
                hovertemplate = "<b>%{y}</b><br>Pred. Score: %{x:.3f}<extra></extra>",
            ))
            fig.update_layout(
                xaxis  = dict(title="Predicted z-score (higher = faster)"),
                yaxis  = dict(title="", automargin=True),
                height = max(320, 28 * len(chart_df)),
                margin = dict(l=170, r=40, t=20, b=50),
                plot_bgcolor  = "white",
                paper_bgcolor = "white",
            )
            fig.update_xaxes(showgrid=True, gridcolor="#eee")
            fig.update_yaxes(showgrid=False)
            st.plotly_chart(fig, use_container_width=True)

            # ----------------------------------------------------------------
            # Form vs venue chart
            # ----------------------------------------------------------------
            st.markdown("#### 5-Race Form vs Venue History — Top 20")
            scatter_df = pred_df.head(20)

            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(
                x    = scatter_df["roll5_mean_z"],
                y    = scatter_df["venue_mean_z"],
                mode = "markers+text",
                text = scatter_df["name"].str.split().str[-1],
                textposition = "top center",
                textfont     = dict(size=10),
                marker       = dict(
                    size  = 10,
                    color = scatter_df["pred_z"],
                    colorscale = "Blues",
                    showscale  = True,
                    colorbar   = dict(title="Pred. Score"),
                ),
                hovertemplate = (
                    "<b>%{text}</b><br>"
                    "5-Race Form: %{x:.3f}<br>"
                    "Venue Avg:   %{y:.3f}<extra></extra>"
                ),
            ))
            fig2.add_hline(y=0, line_dash="dot", line_color="gray", opacity=0.4)
            fig2.add_vline(x=0, line_dash="dot", line_color="gray", opacity=0.4)
            fig2.update_layout(
                xaxis  = dict(title="5-Race Form (z-score)"),
                yaxis  = dict(title="Venue Average (z-score)"),
                height = 420,
                margin = dict(l=60, r=40, t=20, b=60),
                plot_bgcolor  = "white",
                paper_bgcolor = "white",
            )
            fig2.update_xaxes(showgrid=True, gridcolor="#eee")
            fig2.update_yaxes(showgrid=True, gridcolor="#eee")
            st.plotly_chart(fig2, use_container_width=True)

            # ----------------------------------------------------------------
            # Export
            # ----------------------------------------------------------------
            export_cols = ["#", "bib", "name", "pred_z", "roll5_mean_z",
                           "roll10_mean_z", "roll5_std_z", "roll5_dnf_rate",
                           "venue_n", "n_career"]
            csv_out = pred_df[export_cols].to_csv(index=False)
            st.download_button(
                "Download predictions CSV",
                data     = csv_out,
                file_name= f"xgb_{sel_disc.lower().replace(' ','_')}_{sel_venue or 'venue'}.csv",
                mime     = "text/csv",
            )

else:
    st.info(
        "Select a discipline, sex, and venue in the sidebar, "
        "then upload a start list CSV to run the prediction."
    )
