#!/usr/bin/env python3
# etl_race_z_score_pg_crossdb.py
# Reads from fis_raw_data.raw.fis_results and writes into fis_aggregate_data.race_z_score (destination DB)

import math
import logging
import pandas as pd
from sqlalchemy import create_engine, text

# --- SOURCE (raw) ---
SRC_USER = "postgres"
SRC_PW   = "Plymouthskiing1!"
SRC_HOST = "127.0.0.1"
SRC_PORT = 5433
SRC_DB   = "fis_raw_data"
SRC_DSN  = f"postgresql+psycopg2://{SRC_USER}:{SRC_PW}@{SRC_HOST}:{SRC_PORT}/{SRC_DB}"

# --- DESTINATION (aggregates) ---
DST_USER = "postgres"
DST_PW   = "Plymouthskiing1!"
DST_HOST = "127.0.0.1"
DST_PORT = 5433
DST_DB   = "fis_aggregate_data"   # <- change if you want a different DB name
DST_DSN  = f"postgresql+psycopg2://{DST_USER}:{DST_PW}@{DST_HOST}:{DST_PORT}/{DST_DB}"

SRC_SQL = """
select
  r.race_id,
  r.fis_code,
  r.name,
  nullif(r.fis_points, '')::numeric as fis_points
from raw.fis_results r
where r.fis_points is not null and r.fis_points <> ''
"""

DDL = """
create schema if not exists fis_aggregate_data;

create table if not exists fis_aggregate_data.race_z_score (
  race_id      bigint,
  fis_code     text,
  name         text,
  race_z_score double precision
);

create index if not exists ix_rzs_race on fis_aggregate_data.race_z_score (race_id);
create index if not exists ix_rzs_fis  on fis_aggregate_data.race_z_score (fis_code);
"""

def compute_zscores(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["race_id","fis_code","name","race_z_score"])
    def _z(s: pd.Series):
        std = s.std(ddof=0)
        if std is None or std == 0:
            return pd.Series([0.0]*len(s), index=s.index)
        m = s.mean()
        return (m - s) / std
    df["race_z_score"] = df.groupby("race_id", observed=True)["fis_points"].transform(_z)
    return df[["race_id","fis_code","name","race_z_score"]]

def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    src = create_engine(SRC_DSN, pool_pre_ping=True)
    dst = create_engine(DST_DSN, pool_pre_ping=True)

    with src.begin() as sconn:
        logging.info("Loading raw from fis_raw_data.raw.fis_results ...")
        raw = pd.read_sql(SRC_SQL, sconn)
        logging.info("Rows loaded: %d", len(raw))

    logging.info("Computing z-scores ...")
    out = compute_zscores(raw)

    with dst.begin() as dconn:
        logging.info("Ensuring destination schema/table exist in %s ...", DST_DB)
        for stmt in [x for x in DDL.split(";\n") if x.strip()]:
            dconn.exec_driver_sql(stmt)

        logging.info("Truncating fis_aggregate_data.race_z_score in %s ...", DST_DB)
        dconn.exec_driver_sql("truncate table fis_aggregate_data.race_z_score")

        if not out.empty:
            logging.info("Writing %d rows to %s ...", len(out), DST_DB)
            # ✅ KEY FIX: pass the SQLAlchemy connection (dconn), NOT dconn.connection
            out.to_sql(
                "race_z_score",
                con=dconn,                         # <--- FIXED
                schema="fis_aggregate_data",
                if_exists="append",
                index=False,
                method="multi",
                chunksize=20000,
            )
    logging.info("Done.")

if __name__ == "__main__":
    main()
