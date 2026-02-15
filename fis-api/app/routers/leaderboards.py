"""
Leaderboards API endpoints.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import logging

from app.database import execute_query
from app.models import (
    LeaderboardResponse,
    LeaderboardAthleteItem,
    HotStreakResponse,
    HotStreakAthleteItem,
    PaginationMeta,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/leaderboards/hot-streak", response_model=HotStreakResponse)
def get_hot_streak_leaderboard(
    discipline: Optional[str] = Query(None, description="Filter by discipline"),
    days: int = Query(30, ge=7, le=365, description="Time window in days"),
    limit: int = Query(50, ge=1, le=200, description="Number of results"),
):
    """
    Get current hot streak leaderboard.

    Returns athletes with highest momentum in recent period.

    - **discipline**: Optional discipline filter
    - **days**: Time window for momentum calculation (default 30 days)
    - **limit**: Maximum number of athletes
    """
    logger.info(f"GET /leaderboards/hot-streak - discipline={discipline}, days={days}")

    query = """
        SELECT
            hs.fis_code,
            hs.name,
            hs.discipline,
            MAX(hs.momentum_z) as max_momentum_z,
            COUNT(*) as recent_races,
            MAX(hs.date) as last_race_date
        FROM athlete_aggregate.hot_streak hs
        WHERE hs.date >= CURRENT_DATE - (%(days)s * INTERVAL '1 day')
        AND hs.momentum_z IS NOT NULL
    """

    params = {"days": days, "limit": limit}

    if discipline:
        query += " AND hs.discipline = %(discipline)s"
        params["discipline"] = discipline

    query += """
        GROUP BY hs.fis_code, hs.name, hs.discipline
        HAVING COUNT(*) >= 3
        ORDER BY max_momentum_z DESC
        LIMIT %(limit)s
    """

    results = execute_query(query, params)

    if not results:
        raise HTTPException(
            status_code=404,
            detail=f"No hot streak data found for the specified period"
        )

    athletes = [
        HotStreakAthleteItem(
            rank=idx + 1,
            fis_code=row["fis_code"],
            name=row["name"],
            country=None,  # Not in this query
            discipline=row["discipline"],
            momentum_z=row["max_momentum_z"],
            recent_races=row["recent_races"],
            last_race_date=row["last_race_date"]
        )
        for idx, row in enumerate(results)
    ]

    return HotStreakResponse(
        discipline=discipline,
        days=days,
        data=athletes
    )


@router.get("/leaderboards/{discipline}", response_model=LeaderboardResponse)
def get_discipline_leaderboard(
    discipline: str,
    tier: Optional[str] = Query(None, description="Filter by tier (Elite, Contender, Middle, Developing)"),
    year: Optional[int] = Query(None, description="Filter by year (defaults to most recent)"),
    limit: int = Query(50, ge=1, le=200, description="Number of results"),
):
    """
    Get leaderboard for a specific discipline.

    Returns top athletes ranked by average FIS points (lower is better).

    - **discipline**: Discipline name (e.g., "Slalom", "Giant Slalom", "Downhill")
    - **tier**: Optional tier filter
    - **year**: Optional year filter
    - **limit**: Maximum number of athletes
    """
    logger.info(f"GET /leaderboards/{discipline} - tier={tier}, year={year}")

    query = """
        SELECT
            pt.fis_code,
            pt.name,
            pt.tier,
            pt.avg_fis_points,
            pt.race_count,
            aic.wins,
            aic.podiums
        FROM athlete_aggregate.performance_tiers pt
        LEFT JOIN athlete_aggregate.basic_athlete_info_career aic
            ON pt.fis_code = aic.fis_code
        WHERE pt.discipline = %(discipline)s
    """

    params = {"discipline": discipline, "limit": limit}

    if tier:
        query += " AND pt.tier = %(tier)s"
        params["tier"] = tier

    if year:
        query += " AND pt.year = %(year)s"
        params["year"] = year
    else:
        # Get most recent year if not specified
        query += " AND pt.year = (SELECT MAX(year) FROM athlete_aggregate.performance_tiers WHERE discipline = %(discipline)s)"

    query += " AND pt.race_count >= 5"  # Minimum races for ranking
    query += " ORDER BY pt.avg_fis_points ASC LIMIT %(limit)s"

    results = execute_query(query, params)

    if not results:
        raise HTTPException(
            status_code=404,
            detail=f"No leaderboard data found for discipline '{discipline}'"
        )

    # Add rank numbers
    athletes = [
        LeaderboardAthleteItem(
            rank=idx + 1,
            fis_code=row["fis_code"],
            name=row["name"],
            country=None,  # Not in this query
            avg_fis_points=row["avg_fis_points"],
            race_count=row["race_count"],
            wins=row.get("wins"),
            podiums=row.get("podiums")
        )
        for idx, row in enumerate(results)
    ]

    # Get year from results
    result_year = year if year else None
    if results and not year:
        # Query for the year we actually used
        year_query = "SELECT MAX(year) as year FROM athlete_aggregate.performance_tiers WHERE discipline = %(discipline)s"
        year_result = execute_query(year_query, {"discipline": discipline})
        if year_result:
            result_year = year_result[0].get("year")

    return LeaderboardResponse(
        discipline=discipline,
        tier=tier,
        year=result_year,
        data=athletes,
        pagination=PaginationMeta(
            total=len(athletes),
            limit=limit,
            offset=0,
            has_more=False
        )
    )
