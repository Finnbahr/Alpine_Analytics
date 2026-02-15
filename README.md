# ⛷️ FIS Alpine Analytics

A full-stack web application for analyzing FIS Alpine skiing statistics with interactive visualizations, athlete profiles, and advanced analytics.

![Tech Stack](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-61DAFB?style=flat&logo=react&logoColor=black)
![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=flat&logo=typescript&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=flat&logo=postgresql&logoColor=white)
![Tailwind CSS](https://img.shields.io/badge/Tailwind-38B2AC?style=flat&logo=tailwind-css&logoColor=white)

## 📊 Overview

This application provides comprehensive analytics for FIS Alpine skiing, featuring:

- **6.7M+ race results** from official FIS data
- **29,000+ athlete profiles** with career statistics
- **35,000+ races** across 1,300+ locations
- **Interactive visualizations** with Recharts
- **Advanced metrics**: Momentum tracking, Hill Difficulty Index, Home Advantage analysis

## 🚀 Quick Start

### Prerequisites
- Python 3.13+
- Node.js 20+
- PostgreSQL 14+ (with alpine_analytics database)

### 1. Start Backend
\`\`\`bash
cd fis-api
source venv/bin/activate
uvicorn app.main:app --reload
# API: http://localhost:8000
# Docs: http://localhost:8000/docs
\`\`\`

### 2. Start Frontend
\`\`\`bash
cd fis-frontend
npm install
npm run dev
# App: http://localhost:5173
\`\`\`

### 3. Open Application
Visit **http://localhost:5173** in your browser

## 🏗️ Project Structure

\`\`\`
FIS Alpine Analytics/
├── fis-api/                 # FastAPI Backend
│   ├── app/
│   │   ├── main.py         # Application entry
│   │   ├── config.py       # Configuration
│   │   ├── database.py     # DB connection
│   │   ├── models.py       # Pydantic models
│   │   └── routers/        # API endpoints
│   ├── requirements.txt
│   └── .env
│
├── fis-frontend/            # React Frontend
│   ├── src/
│   │   ├── components/     # Reusable components
│   │   ├── pages/          # Page components
│   │   ├── services/       # API client
│   │   └── types/          # TypeScript types
│   ├── package.json
│   └── vite.config.ts
│
├── database/                # Database package
│   └── __init__.py
│
└── docs/
    ├── DEPLOYMENT.md        # Deployment guide
    ├── DEPLOY_CHECKLIST.md # Step-by-step deploy
    ├── PROJECT_SUMMARY.md   # Technical overview
    ├── QUICK_DEMO_GUIDE.md  # Demo walkthrough
    ├── API_DESIGN.md        # API documentation
    └── DATA_DICTIONARY.md   # Database schema
\`\`\`

## ✨ Features

### 🏠 Home Page
- Quick statistics overview
- Hot streak leaderboard
- Discipline rankings preview
- Fast global search (Cmd+K)

### 🏆 Leaderboards
- 5 disciplines: Slalom, Giant Slalom, Super G, Downhill, Alpine Combined
- Momentum-based "Hot Streak" rankings
- Sortable tables with detailed stats
- Direct links to athlete profiles

### ⛷️ Athlete Profiles
- Complete career statistics
- Race history with FIS points
- Momentum tracking (line chart)
- Performance by course (bar chart)
- Current tier and form

### 🏔️ Courses
- Hill Difficulty Index (HDI) rankings
- Interactive difficulty visualization
- DNF rate analysis
- Course statistics (vertical drop, gates, races)

### 📊 Analytics
- Home advantage analysis
- Country-level performance comparison
- Interactive charts and tables
- Statistical insights

## 🔌 API Endpoints

### Athletes
- \`GET /api/v1/athletes\` - List athletes
- \`GET /api/v1/athletes/{fis_code}\` - Profile
- \`GET /api/v1/athletes/{fis_code}/races\` - Race history
- \`GET /api/v1/athletes/{fis_code}/momentum\` - Momentum data
- \`GET /api/v1/athletes/{fis_code}/courses\` - Course performance

### Leaderboards
- \`GET /api/v1/leaderboards/{discipline}\` - Rankings
- \`GET /api/v1/leaderboards/hot-streak\` - Hot athletes

### Courses
- \`GET /api/v1/courses\` - List courses
- \`GET /api/v1/courses/difficulty/{discipline}\` - Difficulty rankings

### Analytics
- \`GET /api/v1/analytics/home-advantage\` - Home vs Away

### Search
- \`GET /api/v1/search\` - Global search

## 🛠️ Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **PostgreSQL** - Relational database
- **Pydantic** - Data validation
- **Uvicorn** - ASGI server

### Frontend
- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **React Router** - Navigation
- **Recharts** - Data visualization
- **Axios** - HTTP client

## 📖 Documentation

- **[QUICK_DEMO_GUIDE.md](QUICK_DEMO_GUIDE.md)** - Try the app locally
- **[DEPLOY_CHECKLIST.md](DEPLOY_CHECKLIST.md)** - Deploy to production
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Complete deployment guide
- **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** - Technical overview
- **[API_DESIGN.md](API_DESIGN.md)** - API reference
- **[DATA_DICTIONARY.md](DATA_DICTIONARY.md)** - Database schema

## 🚢 Deployment

See **[DEPLOY_CHECKLIST.md](DEPLOY_CHECKLIST.md)** for step-by-step instructions.

**Quick Deploy:**
1. Push to GitHub
2. Deploy backend to Render (free tier available)
3. Deploy frontend to Vercel (free tier available)
4. Total time: ~30 minutes

**Cost**: Free for 90 days, then ~$7-14/month

## 📱 Demo

Try these features:
1. Press \`Cmd+K\` → Search for "shiffrin"
2. Click any athlete → See full profile with charts
3. Go to Courses → View difficulty rankings
4. Go to Analytics → See home advantage analysis
5. Resize window → Fully responsive!

## 🎯 Key Metrics

- **API Response**: < 100ms average
- **Bundle Size**: 727 KB (223 KB gzipped)
- **Database**: 6.7M race results, optimized queries
- **Charts**: 60 FPS smooth rendering
- **Mobile**: Fully responsive design

## 📊 Database

PostgreSQL database with:
- 24 tables across 4 schemas
- Athlete aggregates and career stats
- Race results with FIS points
- Course metadata and difficulty metrics
- Momentum tracking and tier classifications

See **[DATA_DICTIONARY.md](DATA_DICTIONARY.md)** for complete schema.

## 🔧 Development

### Backend Development
\`\`\`bash
cd fis-api
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
\`\`\`

### Frontend Development
\`\`\`bash
cd fis-frontend
npm run dev
\`\`\`

### Build for Production
\`\`\`bash
# Backend - no build needed, just deploy
cd fis-api
pip install -r requirements.txt

# Frontend
cd fis-frontend
npm run build
\`\`\`

## 🤝 Contributing

This is a personal project, but suggestions are welcome!

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📝 License

This project is for educational and portfolio purposes.
Data sourced from FIS (International Ski Federation).

## 🙏 Acknowledgments

- **Data Source**: FIS (International Ski Federation)
- **Frameworks**: FastAPI, React, Recharts
- **Icons**: Heroicons
- **Styling**: Tailwind CSS

## 📧 Contact

For questions or feedback about this project, please open an issue on GitHub.

---

**Built with** ⛷️ **by a skiing analytics enthusiast**

**Status**: ✅ Production Ready
**Last Updated**: February 14, 2026
