# FIS Alpine Analytics API

FastAPI backend for FIS Alpine skiing analytics platform.

## Quick Start

### 1. Set Up Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

The `.env` file is already configured with your database settings.

### 3. Run the Server

```bash
# Development server with auto-reload
python app/main.py

# Or use uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Access the API

- **API Root**: http://localhost:8000/
- **Interactive Docs (Swagger)**: http://localhost:8000/docs
- **Alternative Docs (ReDoc)**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## Project Structure

```
fis-api/
├── app/
│   ├── __init__.py          # Package init
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration (env variables)
│   ├── database.py          # Database connection
│   ├── models.py            # Pydantic models
│   └── routers/
│       ├── __init__.py
│       ├── athletes.py      # Athlete endpoints
│       ├── races.py         # Race endpoints
│       └── search.py        # Search endpoints
├── .env                     # Environment variables
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## API Endpoints

### Athletes

- `GET /api/v1/athletes` - List/search athletes
- `GET /api/v1/athletes/{fis_code}` - Athlete profile
- `GET /api/v1/athletes/{fis_code}/races` - Race history
- `GET /api/v1/athletes/{fis_code}/momentum` - Momentum data
- `GET /api/v1/athletes/{fis_code}/courses` - Performance by course

### Races

- `GET /api/v1/races` - List races
- `GET /api/v1/races/{race_id}` - Race details
- `GET /api/v1/races/{race_id}/results` - Race results

### Search

- `GET /api/v1/search` - Global search

## Example Requests

### Search for Athletes

```bash
curl "http://localhost:8000/api/v1/athletes?name=shiffrin"
```

### Get Athlete Profile

```bash
curl "http://localhost:8000/api/v1/athletes/54063"
```

### Get Recent Races

```bash
curl "http://localhost:8000/api/v1/races?discipline=Slalom&limit=10"
```

### Global Search

```bash
curl "http://localhost:8000/api/v1/search?q=val+d"
```

## Testing with Swagger UI

1. Open http://localhost:8000/docs in your browser
2. Click on any endpoint to expand it
3. Click "Try it out"
4. Fill in parameters
5. Click "Execute"
6. View the response

## Development

### Adding New Endpoints

1. Create or modify router file in `app/routers/`
2. Define Pydantic models in `app/models.py`
3. Write database queries using `execute_query()` or `execute_query_single()`
4. Include router in `app/main.py`

### Example New Endpoint

```python
# app/routers/athletes.py

@router.get("/athletes/{fis_code}/stats")
def get_athlete_stats(fis_code: str):
    query = "SELECT * FROM athlete_aggregate.basic_athlete_info_career WHERE fis_code = :fis_code"
    result = execute_query_single(query, {"fis_code": fis_code})

    if not result:
        raise HTTPException(status_code=404, detail="Not found")

    return result
```

## Database

The API connects to your existing PostgreSQL database:
- Host: 127.0.0.1:5433
- Database: alpine_analytics
- User: alpine_analytics

Connection is configured in `.env` file.

## CORS

CORS is enabled for:
- http://localhost:3000 (React dev server)
- http://localhost:3001

Update `CORS_ORIGINS` in `.env` to add more origins.

## Error Handling

All endpoints return consistent error responses:

```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Athlete with FIS code '99999' not found",
    "details": {}
  }
}
```

## Next Steps

1. ✅ Backend running
2. Add more endpoints (leaderboards, courses, analytics)
3. Build React frontend
4. Deploy to production

## Deployment

### Railway (Recommended)

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway init
railway up
```

### Render

1. Create new Web Service
2. Connect GitHub repo
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables from `.env`

## Support

- API Documentation: http://localhost:8000/docs
- Database Schema: See `../DATA_DICTIONARY.md`
- API Design: See `../API_DESIGN.md`

---

**Version**: 1.0.0
**Last Updated**: February 12, 2026
