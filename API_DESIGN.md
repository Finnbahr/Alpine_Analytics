# FIS Alpine Analytics API Design

**Version**: 1.0
**Date**: February 12, 2026
**Tech Stack**: FastAPI (Python) + React (TypeScript)
**Base URL**: `http://localhost:8000/api/v1` (dev), `https://yourdomain.com/api/v1` (prod)

---

## Overview

RESTful API providing access to FIS Alpine skiing analytics including athlete performance, race results, course statistics, and advanced metrics.

---

## Authentication

**Phase 1** (MVP): No authentication - public read-only API

**Phase 2** (Future): JWT-based authentication
- Free tier: Basic endpoints, rate-limited
- Premium tier: Full access, higher limits

---

## API Endpoints

### Core Resources

```
Athletes
├── GET  /athletes                      # List/search athletes
├── GET  /athletes/{fis_code}           # Athlete profile
├── GET  /athletes/{fis_code}/stats     # Career statistics
├── GET  /athletes/{fis_code}/races     # Race history
├── GET  /athletes/{fis_code}/momentum  # Hot streak data
├── GET  /athletes/{fis_code}/courses   # Performance by course
└── GET  /athletes/{fis_code}/traits    # Course trait analysis

Races
├── GET  /races                         # List races
├── GET  /races/{race_id}               # Race details
└── GET  /races/{race_id}/results       # Race results

Courses
├── GET  /courses                       # List courses
├── GET  /courses/{location}            # Course details
├── GET  /courses/{location}/difficulty # HDI metrics
└── GET  /courses/{location}/athletes   # Athlete performance here

Leaderboards
├── GET  /leaderboards/performance      # Performance tier rankings
├── GET  /leaderboards/momentum         # Hot athletes (current streaks)
└── GET  /leaderboards/courses          # Course difficulty rankings

Analytics
├── GET  /analytics/home-advantage      # Home advantage statistics
├── GET  /analytics/setter-advantage    # Setter influence
└── GET  /analytics/course-similarity   # Similar courses

Search
└── GET  /search                        # Global search (athletes, locations)
```

---

## Detailed Endpoint Specifications

### 1. Athletes

#### `GET /athletes`
List or search athletes

**Query Parameters**:
```
name       (string, optional)  - Search by name (case-insensitive)
country    (string, optional)  - Filter by country code (e.g., "USA")
discipline (string, optional)  - Filter by discipline
tier       (string, optional)  - Filter by tier (Elite/Contender/Middle/Developing)
limit      (integer, default=50, max=500) - Results per page
offset     (integer, default=0) - Pagination offset
```

**Example Requests**:
```
GET /athletes?name=shiffrin
GET /athletes?country=USA&discipline=Slalom
GET /athletes?tier=Elite&limit=100
```

**Response** (200 OK):
```json
{
  "data": [
    {
      "fis_code": "54063",
      "name": "SHIFFRIN Mikaela",
      "country": "USA",
      "tier": "Elite",
      "starts": 245,
      "wins": 97,
      "podiums": 155,
      "avg_fis_points": 5.23
    }
  ],
  "pagination": {
    "total": 29545,
    "limit": 50,
    "offset": 0,
    "has_more": true
  }
}
```

---

#### `GET /athletes/{fis_code}`
Get complete athlete profile

**Path Parameters**:
- `fis_code` (string, required) - FIS athlete code

**Example Request**:
```
GET /athletes/54063
```

**Response** (200 OK):
```json
{
  "fis_code": "54063",
  "name": "SHIFFRIN Mikaela",
  "country": "USA",
  "career_stats": {
    "starts": 245,
    "wins": 97,
    "podiums": 155,
    "avg_fis_points": 5.23
  },
  "current_tier": {
    "tier": "Elite",
    "discipline": "Slalom",
    "year": 2025,
    "avg_fis_points": 3.45
  },
  "momentum": {
    "current_momentum_z": 2.34,
    "trend": "hot",
    "last_updated": "2025-04-30"
  }
}
```

---

#### `GET /athletes/{fis_code}/races`
Get athlete's race history

**Path Parameters**:
- `fis_code` (string, required)

**Query Parameters**:
```
discipline (string, optional) - Filter by discipline
from_date  (date, optional)   - Start date (YYYY-MM-DD)
to_date    (date, optional)   - End date (YYYY-MM-DD)
limit      (integer, default=50, max=500)
offset     (integer, default=0)
```

**Example Request**:
```
GET /athletes/54063/races?discipline=Slalom&limit=20
```

**Response** (200 OK):
```json
{
  "data": [
    {
      "race_id": 123456,
      "date": "2025-01-15",
      "location": "Flachau",
      "country": "AUT",
      "discipline": "Slalom",
      "rank": "1",
      "fis_points": 0.00,
      "race_z_score": 3.45,
      "momentum_z": 2.34
    }
  ],
  "pagination": {
    "total": 245,
    "limit": 20,
    "offset": 0
  }
}
```

---

#### `GET /athletes/{fis_code}/momentum`
Get momentum/hot streak data over time

**Path Parameters**:
- `fis_code` (string, required)

**Query Parameters**:
```
discipline (string, optional)
from_date  (date, optional)
to_date    (date, optional)
```

**Example Request**:
```
GET /athletes/54063/momentum?discipline=Slalom
```

**Response** (200 OK):
```json
{
  "data": [
    {
      "date": "2025-01-15",
      "race_id": 123456,
      "momentum_z": 2.34,
      "race_z_score": 3.45,
      "ewma_race_z": 2.10
    }
  ]
}
```

**Use Case**: Time series chart of momentum

---

#### `GET /athletes/{fis_code}/courses`
Performance by specific courses/locations

**Path Parameters**:
- `fis_code` (string, required)

**Query Parameters**:
```
discipline (string, optional)
min_races  (integer, default=3) - Minimum races at location
```

**Example Request**:
```
GET /athletes/54063/courses?discipline=Slalom&min_races=5
```

**Response** (200 OK):
```json
{
  "data": [
    {
      "location": "Flachau",
      "discipline": "Slalom",
      "race_count": 12,
      "mean_race_z_score": 2.45,
      "mean_points_gained": 15.3,
      "best_result": "1",
      "best_result_date": "2025-01-15"
    }
  ]
}
```

---

### 2. Races

#### `GET /races`
List recent races or search

**Query Parameters**:
```
discipline (string, optional)
location   (string, optional)  - Search by location name
country    (string, optional)
from_date  (date, optional)
to_date    (date, optional)
limit      (integer, default=50, max=500)
offset     (integer, default=0)
```

**Example Request**:
```
GET /races?discipline=Slalom&from_date=2025-01-01&limit=20
```

**Response** (200 OK):
```json
{
  "data": [
    {
      "race_id": 123456,
      "date": "2025-01-15",
      "location": "Flachau",
      "country": "AUT",
      "discipline": "Slalom",
      "race_type": "World Cup",
      "competitor_count": 65
    }
  ],
  "pagination": {
    "total": 34788,
    "limit": 20,
    "offset": 0
  }
}
```

---

#### `GET /races/{race_id}`
Get race details

**Path Parameters**:
- `race_id` (integer, required)

**Response** (200 OK):
```json
{
  "race_id": 123456,
  "date": "2025-01-15",
  "location": "Flachau",
  "country": "AUT",
  "discipline": "Slalom",
  "race_type": "World Cup",
  "vertical_drop": 180,
  "start_altitude": 1450,
  "gate_count": 58,
  "competitor_count": 65,
  "dnf_count": 18,
  "winner": {
    "fis_code": "54063",
    "name": "SHIFFRIN Mikaela",
    "time": "1:45.23"
  }
}
```

---

#### `GET /races/{race_id}/results`
Get race results/standings

**Path Parameters**:
- `race_id` (integer, required)

**Query Parameters**:
```
limit  (integer, default=100, max=500)
offset (integer, default=0)
```

**Response** (200 OK):
```json
{
  "race_id": 123456,
  "date": "2025-01-15",
  "location": "Flachau",
  "results": [
    {
      "rank": "1",
      "fis_code": "54063",
      "name": "SHIFFRIN Mikaela",
      "country": "USA",
      "bib": 1,
      "time": "1:45.23",
      "fis_points": 0.00,
      "race_z_score": 3.45
    },
    {
      "rank": "2",
      "fis_code": "12345",
      "name": "ATHLETE Name",
      "country": "SWE",
      "bib": 4,
      "time": "1:45.89",
      "fis_points": 2.34,
      "race_z_score": 2.10
    }
  ]
}
```

---

### 3. Courses

#### `GET /courses`
List or search courses

**Query Parameters**:
```
location   (string, optional) - Search by name
discipline (string, optional)
country    (string, optional)
limit      (integer, default=50, max=500)
offset     (integer, default=0)
```

**Example Request**:
```
GET /courses?location=val&discipline=Slalom
```

**Response** (200 OK):
```json
{
  "data": [
    {
      "location": "Val d'Isere",
      "country": "FRA",
      "discipline": "Slalom",
      "race_count": 45,
      "homologation_number": "123456",
      "difficulty_index": 78.5,
      "avg_vertical_drop": 225,
      "avg_gate_count": 62
    }
  ],
  "pagination": {
    "total": 3891,
    "limit": 50,
    "offset": 0
  }
}
```

---

#### `GET /courses/{location}/difficulty`
Get Hill Difficulty Index (HDI) metrics

**Path Parameters**:
- `location` (string, required, URL-encoded) - Course location

**Query Parameters**:
```
discipline (string, optional)
```

**Example Request**:
```
GET /courses/Flachau/difficulty?discipline=Slalom
```

**Response** (200 OK):
```json
{
  "location": "Flachau",
  "discipline": "Slalom",
  "hill_difficulty_index": 78.5,
  "rank": 15,
  "total_courses": 892,
  "metrics": {
    "avg_dnf_rate": 0.28,
    "avg_winning_time": "1:45.23",
    "avg_gate_count": 62,
    "avg_vertical_drop": 225,
    "avg_start_altitude": 1450
  },
  "race_count": 45
}
```

---

### 4. Leaderboards

#### `GET /leaderboards/performance`
Performance tier rankings

**Query Parameters**:
```
discipline (string, required)  - Discipline to rank
tier       (string, optional)  - Filter by tier
year       (integer, optional, default=current) - Season year
min_races  (integer, default=10) - Minimum races
limit      (integer, default=50, max=500)
offset     (integer, default=0)
```

**Example Request**:
```
GET /leaderboards/performance?discipline=Slalom&tier=Elite&limit=50
```

**Response** (200 OK):
```json
{
  "discipline": "Slalom",
  "tier": "Elite",
  "year": 2025,
  "data": [
    {
      "rank": 1,
      "fis_code": "54063",
      "name": "SHIFFRIN Mikaela",
      "country": "USA",
      "avg_fis_points": 3.45,
      "race_count": 28,
      "wins": 15,
      "podiums": 22
    }
  ],
  "pagination": {
    "total": 145,
    "limit": 50,
    "offset": 0
  }
}
```

---

#### `GET /leaderboards/momentum`
Hot athletes (current momentum leaders)

**Query Parameters**:
```
discipline (string, optional)
days       (integer, default=30) - Days to look back
limit      (integer, default=50, max=500)
```

**Example Request**:
```
GET /leaderboards/momentum?discipline=Slalom&days=30
```

**Response** (200 OK):
```json
{
  "discipline": "Slalom",
  "period": "last_30_days",
  "data": [
    {
      "rank": 1,
      "fis_code": "54063",
      "name": "SHIFFRIN Mikaela",
      "country": "USA",
      "peak_momentum_z": 3.45,
      "recent_races": 5,
      "recent_wins": 3,
      "trend": "hot"
    }
  ]
}
```

---

#### `GET /leaderboards/courses`
Course difficulty rankings

**Query Parameters**:
```
discipline (string, required)
order      (string, default="hardest") - "hardest" or "easiest"
limit      (integer, default=50, max=500)
```

**Example Request**:
```
GET /leaderboards/courses?discipline=Slalom&order=hardest
```

**Response** (200 OK):
```json
{
  "discipline": "Slalom",
  "order": "hardest",
  "data": [
    {
      "rank": 1,
      "location": "Kitzbühel",
      "country": "AUT",
      "difficulty_index": 95.3,
      "avg_dnf_rate": 0.42,
      "race_count": 67
    }
  ]
}
```

---

### 5. Analytics

#### `GET /analytics/home-advantage`
Home advantage statistics

**Query Parameters**:
```
country    (string, optional)
discipline (string, optional)
sex        (string, optional) - "M" or "W"
```

**Response** (200 OK):
```json
{
  "data": [
    {
      "country": "USA",
      "sex": "W",
      "discipline": "Slalom",
      "home_race_count": 45,
      "away_race_count": 123,
      "home_avg_fis_points": 15.3,
      "away_avg_fis_points": 18.2,
      "fis_points_pct_diff": -15.9,
      "has_advantage": true
    }
  ]
}
```

---

#### `GET /analytics/setter-advantage`
Course setter influence statistics

**Response**: Similar structure to home advantage

---

### 6. Search

#### `GET /search`
Global search across athletes and locations

**Query Parameters**:
```
q     (string, required, min=2) - Search query
type  (string, optional) - "athletes" or "locations" (default: both)
limit (integer, default=20, max=100)
```

**Example Request**:
```
GET /search?q=shiffrin&type=athletes
```

**Response** (200 OK):
```json
{
  "query": "shiffrin",
  "results": {
    "athletes": [
      {
        "type": "athlete",
        "fis_code": "54063",
        "name": "SHIFFRIN Mikaela",
        "country": "USA",
        "starts": 245,
        "wins": 97
      }
    ],
    "locations": []
  },
  "total_results": 1
}
```

---

## Common Response Patterns

### Success Response
```json
{
  "data": [...],           // Results array or single object
  "pagination": {...},     // Pagination info (if applicable)
  "meta": {...}           // Additional metadata (optional)
}
```

### Error Response
```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Athlete with FIS code '99999' not found",
    "details": {}
  }
}
```

### HTTP Status Codes
- `200` - Success
- `400` - Bad Request (invalid parameters)
- `404` - Not Found
- `422` - Validation Error
- `429` - Rate Limit Exceeded
- `500` - Internal Server Error

---

## Pagination

All list endpoints support pagination:

**Request Parameters**:
```
limit  - Results per page (default: 50, max: 500)
offset - Skip N results (default: 0)
```

**Response**:
```json
{
  "data": [...],
  "pagination": {
    "total": 1000,
    "limit": 50,
    "offset": 0,
    "has_more": true
  }
}
```

---

## Filtering & Sorting

**Common Filters** (available on most list endpoints):
- `discipline` - Filter by discipline
- `country` - Filter by country code
- `from_date`, `to_date` - Date range filtering

**Sorting**:
```
sort_by   - Field to sort by
sort_dir  - "asc" or "desc" (default: varies by endpoint)
```

Example:
```
GET /athletes?discipline=Slalom&sort_by=wins&sort_dir=desc
```

---

## Rate Limiting

**Phase 1** (No Auth):
- 60 requests/minute per IP
- 1000 requests/hour per IP

**Phase 2** (With Auth):
- Free tier: 120 requests/minute
- Premium tier: Unlimited

**Headers**:
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1640995200
```

---

## CORS Configuration

**Development**:
```
Access-Control-Allow-Origin: http://localhost:3000
```

**Production**:
```
Access-Control-Allow-Origin: https://yourdomain.com
```

---

## Implementation Priority

### Phase 1 (MVP) - Week 1
- [x] Basic athlete endpoints
- [x] Race endpoints
- [x] Search endpoint
- [x] Performance leaderboard

### Phase 2 - Week 2
- [ ] Momentum/hot streak data
- [ ] Course endpoints
- [ ] Course difficulty rankings
- [ ] Athlete performance by course

### Phase 3 - Week 3
- [ ] Advanced analytics (home advantage, setter)
- [ ] Course traits/regression
- [ ] Comparison tools

---

## Tech Stack Details

### Backend (FastAPI)
```python
from fastapi import FastAPI, Query, Path
from pydantic import BaseModel

app = FastAPI()

@app.get("/api/v1/athletes/{fis_code}")
async def get_athlete(fis_code: str = Path(...)):
    # Database query
    # Return response
    pass
```

### Frontend (React + TypeScript)
```typescript
// API client
const getAthlete = async (fisCode: string) => {
  const response = await fetch(`/api/v1/athletes/${fisCode}`);
  return response.json();
};
```

---

## Next Steps

1. **Backend Setup**:
   - Create FastAPI project structure
   - Set up database connection pool
   - Implement core endpoints
   - Add request validation
   - Write tests

2. **Frontend Setup**:
   - Create React + TypeScript project
   - Set up routing
   - Create API client layer
   - Implement components
   - Add charts/visualizations

3. **Deploy**:
   - Backend: Railway, Render, or DigitalOcean
   - Frontend: Vercel or Netlify
   - Database: Keep on current PostgreSQL instance

---

**Version**: 1.0
**Last Updated**: February 12, 2026
**Ready for Implementation**: ✅
