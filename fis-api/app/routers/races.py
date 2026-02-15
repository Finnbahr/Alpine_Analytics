"""
Races API endpoints.
"""

from fastapi import APIRouter, HTTPException, Query, Path
from typing import Optional
from datetime import date
import logging

from app.database import execute_query, execute_query_single
from app.models import (
    RaceListResponse,
    RaceBasic,
    RaceDetails,
    RaceResultsResponse,
    RaceResult,
    PaginationMeta,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/races", response_model=RaceListResponse)
def list_races(
    discipline: Optional[str] = Query(None, description="Filter by discipline"),
    location: Optional[str] = Query(None, description="Search by location name"),
    country: Optional[str] = Query(None, description="Filter by country"),
    from_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    to_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """
    List races with optional filtering.

    - **discipline**: Filter by discipline
    - **location**: Search by location name (partial match)
    - **country**: Filter by country code
    - **from_date**: Start date for date range
    - **to_date**: End date for date range
    """
    logger.info(f"GET /races - discipline={discipline}, location={location}, from_date={from_date}")

    query = """
        SELECT
            race_id,
            date,
            location,
            country,
            discipline,
            race_type
        FROM raw.race_details
        WHERE 1=1
    """

    params = {"limit": limit, "offset": offset}

    if discipline:
        query += " AND discipline = %(discipline)s"
        params["discipline"] = discipline

    if location:
        query += " AND LOWER(location) LIKE LOWER(%(location)s)"
        params["location"] = f"%{location}%"

    if country:
        query += " AND country = %(country)s"
        params["country"] = country

    if from_date:
        query += " AND date >= %(from_date)s"
        params["from_date"] = from_date

    if to_date:
        query += " AND date <= %(to_date)s"
        params["to_date"] = to_date

    query += " ORDER BY date DESC LIMIT %(limit)s OFFSET %(offset)s"

    results = execute_query(query, params)

    races = [
        RaceBasic(
            race_id=row["race_id"],
            date=row["date"],
            location=row["location"],
            country=row.get("country"),
            discipline=row["discipline"],
            race_type=row.get("race_type")
        )
        for row in results
    ]

    return RaceListResponse(
        data=races,
        pagination=PaginationMeta(
            total=None,
            limit=limit,
            offset=offset,
            has_more=len(races) == limit
        )
    )


@router.get("/races/{race_id}", response_model=RaceDetails)
def get_race(
    race_id: int = Path(..., description="Race ID")
):
    """
    Get race details.

    Returns complete race information including course characteristics.
    """
    logger.info(f"GET /races/{race_id}")

    query = """
        SELECT
            race_id,
            date,
            location,
            country,
            discipline,
            race_type,
            CAST(NULLIF(vertical_drop, '') AS REAL) as vertical_drop,
            CAST(NULLIF(start_altitude, '') AS REAL) as start_altitude,
            CAST(NULLIF(first_run_number_of_gates, '') AS INTEGER) as gate_count
        FROM raw.race_details
        WHERE race_id = %(race_id)s
    """

    row = execute_query_single(query, {"race_id": race_id})

    if not row:
        raise HTTPException(
            status_code=404,
            detail=f"Race with ID {race_id} not found"
        )

    # Get competitor count
    count_query = """
        SELECT COUNT(*) as count FROM raw.fis_results WHERE race_id = %(race_id)s
    """
    count_row = execute_query_single(count_query, {"race_id": race_id})

    return RaceDetails(
        race_id=row["race_id"],
        date=row["date"],
        location=row["location"],
        country=row.get("country"),
        discipline=row["discipline"],
        race_type=row.get("race_type"),
        vertical_drop=row.get("vertical_drop"),
        start_altitude=row.get("start_altitude"),
        gate_count=row.get("gate_count"),
        competitor_count=count_row.get("count") if count_row else None
    )


@router.get("/races/{race_id}/results", response_model=RaceResultsResponse)
def get_race_results(
    race_id: int = Path(..., description="Race ID"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """
    Get race results/standings.

    Returns list of competitors and their results for this race.
    """
    logger.info(f"GET /races/{race_id}/results")

    # First, check if race exists
    race_query = """
        SELECT race_id, date, location, country, discipline, race_type
        FROM raw.race_details
        WHERE race_id = %(race_id)s
    """
    race_row = execute_query_single(race_query, {"race_id": race_id})

    if not race_row:
        raise HTTPException(
            status_code=404,
            detail=f"Race with ID {race_id} not found"
        )

    # Get results with z-scores
    results_query = """
        SELECT
            fr.rank,
            fr.fis_code,
            fr.name,
            fr.country,
            CAST(NULLIF(fr.bib, '') AS INTEGER) as bib,
            fr.final_time,
            CAST(NULLIF(fr.fis_points, '') AS REAL) as fis_points,
            rz.race_z_score
        FROM raw.fis_results fr
        LEFT JOIN race_aggregate.race_z_score rz
            ON fr.race_id = rz.race_id AND fr.fis_code = rz.fis_code
        WHERE fr.race_id = %(race_id)s
        ORDER BY
            CASE
                WHEN fr.rank ~ '^[0-9]+$' THEN CAST(fr.rank AS INTEGER)
                ELSE 999999
            END,
            fr.rank
        LIMIT %(limit)s OFFSET %(offset)s
    """

    results = execute_query(results_query, {"race_id": race_id, "limit": limit, "offset": offset})

    race_results = [
        RaceResult(
            rank=row["rank"],
            fis_code=row["fis_code"],
            name=row["name"],
            country=row.get("country"),
            bib=row.get("bib"),
            time=row.get("final_time"),
            fis_points=row.get("fis_points"),
            race_z_score=row.get("race_z_score")
        )
        for row in results
    ]

    return RaceResultsResponse(
        race=RaceBasic(
            race_id=race_row["race_id"],
            date=race_row["date"],
            location=race_row["location"],
            country=race_row.get("country"),
            discipline=race_row["discipline"],
            race_type=race_row.get("race_type")
        ),
        results=race_results
    )
