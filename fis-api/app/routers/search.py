"""
Search API endpoints.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import logging

from app.database import execute_query
from app.models import (
    SearchResponse,
    SearchResults,
    SearchResultAthlete,
    SearchResultLocation,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/search", response_model=SearchResponse)
def global_search(
    q: str = Query(..., min_length=2, description="Search query (minimum 2 characters)"),
    type: Optional[str] = Query(None, description="Filter by type: 'athletes' or 'locations'"),
    limit: int = Query(20, ge=1, le=100),
):
    """
    Global search across athletes and locations.

    - **q**: Search query (minimum 2 characters)
    - **type**: Optional filter ('athletes' or 'locations')
    - **limit**: Maximum results per type

    Returns matching athletes and/or locations.
    """
    logger.info(f"GET /search - q={q}, type={type}")

    if len(q.strip()) < 2:
        raise HTTPException(
            status_code=400,
            detail="Search query must be at least 2 characters"
        )

    search_results = SearchResults()

    # Search athletes (unless type is specifically 'locations')
    if type != "locations":
        athletes_query = """
            SELECT DISTINCT
                fr.fis_code,
                fr.name,
                fr.country,
                aic.starts,
                aic.wins
            FROM raw.fis_results fr
            LEFT JOIN athlete_aggregate.basic_athlete_info_career aic
                ON fr.fis_code = aic.fis_code
            WHERE LOWER(fr.name) LIKE LOWER(%(query)s)
            LIMIT %(limit)s
        """

        athlete_results = execute_query(
            athletes_query,
            {"query": f"%{q}%", "limit": limit}
        )

        search_results.athletes = [
            SearchResultAthlete(
                fis_code=row["fis_code"],
                name=row["name"],
                country=row.get("country"),
                starts=row.get("starts"),
                wins=row.get("wins")
            )
            for row in athlete_results
        ]

    # Search locations (unless type is specifically 'athletes')
    if type != "athletes":
        locations_query = """
            SELECT
                location,
                country,
                COUNT(*) as race_count
            FROM raw.race_details
            WHERE LOWER(location) LIKE LOWER(%(query)s)
            GROUP BY location, country
            ORDER BY race_count DESC
            LIMIT %(limit)s
        """

        location_results = execute_query(
            locations_query,
            {"query": f"%{q}%", "limit": limit}
        )

        search_results.locations = [
            SearchResultLocation(
                location=row["location"],
                country=row.get("country"),
                race_count=row.get("race_count")
            )
            for row in location_results
        ]

    total = len(search_results.athletes) + len(search_results.locations)

    if total == 0:
        logger.info(f"No results found for query: {q}")

    return SearchResponse(
        query=q,
        results=search_results,
        total_results=total
    )
