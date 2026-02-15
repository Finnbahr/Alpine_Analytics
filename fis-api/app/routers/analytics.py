"""
Analytics API endpoints.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import logging

from app.database import execute_query
from app.models import (
    HomeAdvantageResponse,
    HomeAdvantageItem,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/analytics/home-advantage", response_model=HomeAdvantageResponse)
def get_home_advantage(
    discipline: Optional[str] = Query(None, description="Filter by discipline"),
    min_races: int = Query(10, ge=1, description="Minimum races for inclusion"),
    limit: int = Query(50, ge=1, le=200),
):
    """
    Get home advantage statistics.

    Returns home vs away performance comparison by country.
    Negative percentage difference indicates home advantage.

    - **discipline**: Optional discipline filter
    - **min_races**: Minimum number of races for statistical significance
    - **limit**: Maximum number of countries
    """
    logger.info(f"GET /analytics/home-advantage - discipline={discipline}")

    query = """
        SELECT
            competitor_country as country,
            discipline,
            sex,
            home_race_count,
            away_race_count,
            home_avg_fis_points,
            away_avg_fis_points,
            fis_points_pct_diff
        FROM worldcup_aggregate.home_advantage
        WHERE home_race_count >= %(min_races)s
        AND away_race_count >= %(min_races)s
    """

    params = {"min_races": min_races, "limit": limit}

    if discipline:
        query += " AND discipline = %(discipline)s"
        params["discipline"] = discipline

    query += """
        ORDER BY ABS(fis_points_pct_diff) DESC
        LIMIT %(limit)s
    """

    results = execute_query(query, params)

    if not results:
        raise HTTPException(
            status_code=404,
            detail="No home advantage data found for the specified criteria"
        )

    advantage_items = [
        HomeAdvantageItem(
            country=row["country"],
            discipline=row["discipline"],
            sex=row.get("sex"),
            home_race_count=row["home_race_count"],
            away_race_count=row["away_race_count"],
            home_avg_fis_points=row["home_avg_fis_points"],
            away_avg_fis_points=row["away_avg_fis_points"],
            fis_points_pct_diff=row["fis_points_pct_diff"]
        )
        for row in results
    ]

    return HomeAdvantageResponse(
        discipline=discipline,
        data=advantage_items
    )
