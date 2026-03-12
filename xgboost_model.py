"""
xgboost_model.py — Alpine Analytics XGBoost race predictor.

Trains a gradient-boosted tree model on all available race history for a given
discipline / sex / race_type combination and returns a ranked prediction for
an uploaded start list.

Public API
----------
load_history(discipline, sex, race_type)  -> pd.DataFrame
    Load and feature-engineer all race results from the DB.

train(discipline, sex, race_type)         -> (XGBRegressor, float)
    Train on full history. Returns (model, fp_max).

predict(model, fp_max, hist_df, start_list, venue, race_month) -> pd.DataFrame
    Build per-athlete features and return a ranked predictions DataFrame.

FEATURES : list[str]
    Ordered list of feature column names used for training and prediction.

XGB_PARAMS : dict
    Hyperparameters used for all models.

Backtested accuracy (World Cup, finishers only, 2021+ test set):
    Discipline     | Races (M/W) | Rho (M/W)       | Winner % (M/W)
    ---------------|-------------|-----------------|---------------
    Slalom         | 60 / 53     | 0.917 / 0.917   | 75% / 94%
    Giant Slalom   | 48 / 50     | 0.950 / 0.975   | 94% / 62%
    Super G        | 41 / 48     | 0.953 / 0.958   | 81% / 83%
    Downhill       | 52 / 47     | 0.912 / 0.946   | 77% / 68%
"""

import numpy as np
import pandas as pd
import xgboost as xgb
from sqlalchemy import text
from database import get_engine

# ── Feature list (order matters — must match training) ─────────────────────────
FEATURES: list[str] = [
    "fis_points",       # current FIS ranking score (lower = better)
    "bib",              # start number
    "roll5_mean_z",     # mean z-score over last 5 races
    "roll10_mean_z",    # mean z-score over last 10 races
    "roll5_std_z",      # z-score variability over last 5 races
    "roll5_dnf_rate",   # DNF/DSQ rate over last 5 starts
    "n_career",         # total prior starts in this discipline
    "days_since",       # days since previous race
    "venue_mean_z",     # personal historical mean z at this venue
    "venue_n",          # prior starts at this venue
    "month",            # calendar month of the race
]

# ── Hyperparameters ────────────────────────────────────────────────────────────
XGB_PARAMS: dict = dict(
    n_estimators    = 500,
    max_depth       = 4,
    learning_rate   = 0.05,
    subsample       = 0.8,
    colsample_bytree= 0.8,
    min_child_weight= 3,
    random_state    = 42,
    n_jobs          = -1,
    verbosity       = 0,
)


# ── Data loading ───────────────────────────────────────────────────────────────
def load_history(
    discipline: str,
    sex: str,
    race_type: str = "World Cup",
) -> pd.DataFrame:
    """
    Load all race results for the given discipline/sex/race_type from the DB
    and compute rolling features (no data leakage — shift(1) throughout).

    Returns a DataFrame with one row per athlete-race entry. Feature columns
    are fully imputed (no NaN). The column `race_z_score` is the training
    target (NULL for DNF entries).
    """
    engine = get_engine()
    q = text("""
        SELECT
            fr.fis_code::text              AS fis_code,
            fr.race_id,
            rz.race_z_score::float         AS race_z_score,
            rd.date,
            rd.location,
            rd.race_type,
            fr.bib::int                    AS bib,
            fr.fis_points::float           AS fis_points,
            fr.rank                        AS rank_str
        FROM raw.fis_results fr
        JOIN raw.race_details rd ON rd.race_id = fr.race_id
        LEFT JOIN race_aggregate.race_z_score rz
               ON rz.race_id = fr.race_id AND rz.fis_code = fr.fis_code
        WHERE rd.discipline = :disc
          AND rd.race_type  = :race_type
          AND rd.sex        = :sex
        ORDER BY rd.date ASC, fr.race_id, fr.fis_code
    """)
    with engine.connect() as conn:
        df = pd.read_sql(q, conn, params={
            "disc": discipline, "sex": sex, "race_type": race_type,
        })

    df["date"]   = pd.to_datetime(df["date"])
    df["is_dnf"] = df["rank_str"].astype(str).str.upper().str.startswith(
        ("DNF", "DSQ", "DNS")
    )

    # Rolling features — shift(1) prevents leakage into current race
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

    # Imputation — cascaded so no NaN remains in any FEATURE column
    df["fis_points"] = df["fis_points"].fillna(df["fis_points"].median())
    df["bib"] = df.groupby("race_id")["bib"].transform(
        lambda x: x.fillna(x.median()).fillna(30)
    )

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


# ── Training ───────────────────────────────────────────────────────────────────
def train(
    discipline: str,
    sex: str,
    race_type: str = "World Cup",
) -> tuple:
    """
    Train XGBoost on all available history for the given discipline/sex/race_type.

    Returns
    -------
    model  : xgb.XGBRegressor  (fitted)
    fp_max : float              (95th-percentile FIS points — needed for cold-start imputation)

    Raises ValueError if fewer than 50 training rows are available.
    """
    df    = load_history(discipline, sex, race_type)
    train = df[df["race_z_score"].notna()].copy()
    if len(train) < 50:
        raise ValueError(
            f"Insufficient training data for {discipline} / {sex} / {race_type} "
            f"({len(train)} rows, need ≥ 50)."
        )
    fp_max = max(float(df["fis_points"].quantile(0.95)), 1.0)
    model  = xgb.XGBRegressor(**XGB_PARAMS)
    model.fit(train[FEATURES].values, train["race_z_score"].values)
    return model, fp_max


# ── Prediction ─────────────────────────────────────────────────────────────────
def _athlete_features(
    hist_df: pd.DataFrame,
    fis_code: str,
    bib: int,
    venue: str,
    race_month: int,
    fallback_fis_points: float,
    fp_max: float,
) -> dict:
    """
    Build one feature row for a single athlete as of today.

    Uses all available race history (no shift — we want to include their most
    recent completed race when building the prediction for their next race).
    """
    ath      = hist_df[hist_df["fis_code"] == fis_code]
    finished = ath[ath["race_z_score"].notna()].sort_values("date")

    if len(finished) == 0:
        # Cold start — proxy from FIS points
        fis_pts   = fallback_fis_points if not np.isnan(fallback_fis_points) else fp_max
        fis_proxy = float(np.clip(1.0 - 2.0 * (fis_pts / max(fp_max, 1.0)), -1.5, 1.5))
        return {
            "fis_points": fis_pts, "bib": float(bib),
            "roll5_mean_z": fis_proxy, "roll10_mean_z": fis_proxy,
            "roll5_std_z": 0.6, "roll5_dnf_rate": 0.08,
            "n_career": 0.0, "days_since": 30.0,
            "venue_mean_z": fis_proxy, "venue_n": 0.0,
            "month": float(race_month),
        }

    zs          = finished["race_z_score"].values
    dnfs        = ath.sort_values("date")["is_dnf"].values
    last_date   = finished["date"].iloc[-1]
    days_since  = max(0, (pd.Timestamp.today() - last_date).days)
    fis_pts     = float(ath.sort_values("date")["fis_points"].iloc[-1])

    roll5_z   = float(np.mean(zs[-5:]))
    roll10_z  = float(np.mean(zs[-10:]))
    roll5_std = float(np.std(zs[-5:], ddof=1)) if len(zs) >= 2 else 0.6
    roll5_dnf = float(np.mean(dnfs[-5:])) if len(dnfs) >= 1 else 0.08

    venue_hist   = finished[finished["location"].str.strip().str.lower() == venue.strip().lower()]
    venue_mean_z = float(venue_hist["race_z_score"].mean()) if len(venue_hist) > 0 else roll10_z
    venue_n      = float(len(venue_hist))

    return {
        "fis_points":     fis_pts,
        "bib":            float(bib),
        "roll5_mean_z":   roll5_z,
        "roll10_mean_z":  roll10_z,
        "roll5_std_z":    max(roll5_std, 0.0),
        "roll5_dnf_rate": roll5_dnf,
        "n_career":       float(len(zs)),
        "days_since":     float(days_since),
        "venue_mean_z":   venue_mean_z,
        "venue_n":        venue_n,
        "month":          float(race_month),
    }


def predict(
    model,
    fp_max: float,
    hist_df: pd.DataFrame,
    start_list: pd.DataFrame,
    venue: str,
    race_month: int,
) -> pd.DataFrame:
    """
    Generate a ranked prediction for every athlete in start_list.

    Parameters
    ----------
    model       : fitted XGBRegressor from train()
    fp_max      : 95th-pct FIS points from train() — used for cold-start imputation
    hist_df     : race history DataFrame from load_history()
    start_list  : DataFrame with columns: bib (int), fis_code (str), name (str),
                  and optionally fis_points (float) for cold-start athletes
    venue       : location name matching raw.race_details.location
    race_month  : calendar month of the race (1–12)

    Returns
    -------
    DataFrame sorted by pred_z descending (rank 1 = predicted winner), with columns:
        rank, bib, fis_code, name, pred_z,
        roll5_mean_z, roll10_mean_z, roll5_std_z, roll5_dnf_rate,
        n_career, days_since, venue_mean_z, venue_n, fis_points
    """
    rows = []
    for _, sl_row in start_list.iterrows():
        fis_code = str(sl_row["fis_code"]).strip()
        feats    = _athlete_features(
            hist_df             = hist_df,
            fis_code            = fis_code,
            bib                 = int(sl_row["bib"]),
            venue               = venue,
            race_month          = race_month,
            fallback_fis_points = float(sl_row.get("fis_points", float("nan"))),
            fp_max              = fp_max,
        )
        feats["fis_code"] = fis_code
        feats["name"]     = str(sl_row.get("name", fis_code))
        rows.append(feats)

    pred_df = pd.DataFrame(rows)
    pred_df["pred_z"] = model.predict(pred_df[FEATURES].values)
    pred_df = pred_df.sort_values("pred_z", ascending=False).reset_index(drop=True)
    pred_df.insert(0, "rank", range(1, len(pred_df) + 1))

    col_order = [
        "rank", "bib", "fis_code", "name", "pred_z",
        "roll5_mean_z", "roll10_mean_z", "roll5_std_z", "roll5_dnf_rate",
        "n_career", "days_since", "venue_mean_z", "venue_n", "fis_points",
    ]
    return pred_df[[c for c in col_order if c in pred_df.columns]]


# ── Venue list helper ──────────────────────────────────────────────────────────
def list_venues(discipline: str, sex: str, race_type: str = "World Cup") -> list[str]:
    """Return sorted list of venue names for the given discipline/sex/race_type."""
    engine = get_engine()
    q = text("""
        SELECT DISTINCT location
        FROM raw.race_details
        WHERE discipline = :disc AND race_type = :race_type AND sex = :sex
        ORDER BY location
    """)
    with engine.connect() as conn:
        df = pd.read_sql(q, conn, params={
            "disc": discipline, "race_type": race_type, "sex": sex,
        })
    return df["location"].tolist()
