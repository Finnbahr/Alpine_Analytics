"""
Courses API endpoints.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import logging

from app.database import execute_query
from app.models import (
    CourseListResponse,
    CourseBasic,
    CourseDifficultyResponse,
    CourseDifficulty,
    PaginationMeta,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/courses", response_model=CourseListResponse)
def list_courses(
    discipline: Optional[str] = Query(None, description="Filter by discipline"),
    country: Optional[str] = Query(None, description="Filter by country"),
    location: Optional[str] = Query(None, description="Search by location name"),
    min_races: int = Query(5, ge=1, description="Minimum number of races"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """
    List courses/locations with race history.

    - **discipline**: Optional discipline filter
    - **country**: Optional country filter
    - **location**: Optional location name search
    - **min_races**: Minimum number of races at location
    - **limit**: Results per page
    - **offset**: Pagination offset
    """
    logger.info(f"GET /courses - discipline={discipline}, country={country}")

    query = """
        SELECT DISTINCT
            rd.location,
            rd.country,
            rd.discipline,
            COUNT(*) as race_count
        FROM raw.race_details rd
        WHERE 1=1
    """

    params = {"min_races": min_races, "limit": limit, "offset": offset}

    if discipline:
        query += " AND rd.discipline = %(discipline)s"
        params["discipline"] = discipline

    if country:
        query += " AND rd.country = %(country)s"
        params["country"] = country

    if location:
        query += " AND LOWER(rd.location) LIKE LOWER(%(location)s)"
        params["location"] = f"%{location}%"

    query += """
        GROUP BY rd.location, rd.country, rd.discipline
        HAVING COUNT(*) >= %(min_races)s
        ORDER BY race_count DESC
        LIMIT %(limit)s OFFSET %(offset)s
    """

    results = execute_query(query, params)

    courses = [
        CourseBasic(
            location=row["location"],
            country=row.get("country"),
            discipline=row["discipline"],
            race_count=row["race_count"]
        )
        for row in results
    ]

    return CourseListResponse(
        data=courses,
        pagination=PaginationMeta(
            total=None,
            limit=limit,
            offset=offset,
            has_more=len(courses) == limit
        )
    )


@router.get("/courses/difficulty/{discipline}", response_model=CourseDifficultyResponse)
def get_course_difficulty(
    discipline: str,
    sort_by: str = Query("difficulty", description="Sort by: difficulty, dnf_rate, race_count"),
    limit: int = Query(50, ge=1, le=200),
):
    """
    Get course difficulty rankings for a discipline.

    Returns courses ranked by Hill Difficulty Index (HDI).

    - **discipline**: Discipline name (e.g., "Slalom", "Giant Slalom")
    - **sort_by**: Sort criteria (difficulty, dnf_rate, race_count)
    - **limit**: Maximum number of courses
    """
    logger.info(f"GET /courses/difficulty/{discipline} - sort_by={sort_by}")

    # Determine sort column
    sort_column = {
        "difficulty": "hill_difficulty_index DESC",
        "dnf_rate": "avg_dnf_rate DESC",
        "race_count": "race_count DESC",
    }.get(sort_by, "hill_difficulty_index DESC")

    query = f"""
        SELECT
            location,
            discipline,
            homologation_number,
            hill_difficulty_index,
            avg_dnf_rate,
            race_count,
            avg_winning_time,
            avg_gate_count,
            avg_start_altitude,
            avg_vertical_drop
        FROM course_aggregate.difficulty_index
        WHERE discipline = %(discipline)s
        AND race_count >= 3
        ORDER BY {sort_column}
        LIMIT %(limit)s
    """

    results = execute_query(query, {"discipline": discipline, "limit": limit})

    if not results:
        raise HTTPException(
            status_code=404,
            detail=f"No course difficulty data found for discipline '{discipline}'"
        )

    courses = [
        CourseDifficulty(
            location=row["location"],
            discipline=row["discipline"],
            homologation_number=row.get("homologation_number"),
            hill_difficulty_index=row["hill_difficulty_index"],
            avg_dnf_rate=row["avg_dnf_rate"],
            race_count=row["race_count"],
            avg_winning_time=row.get("avg_winning_time"),
            avg_gate_count=row.get("avg_gate_count"),
            avg_start_altitude=row.get("avg_start_altitude"),
            avg_vertical_drop=row.get("avg_vertical_drop")
        )
        for row in results
    ]

    return CourseDifficultyResponse(
        discipline=discipline,
        data=courses
    )
