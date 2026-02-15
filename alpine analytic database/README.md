# Alpine Analytics Database - Update Scripts

This folder contains scripts to update your PostgreSQL database with new FIS race data and recompute analytics.

## 📊 What This Does

These scripts:
1. **Fetch new race data** from FIS website (scraping)
2. **Update PostgreSQL tables** with new results
3. **Recompute analytics**: Athlete stats, course difficulty, momentum tracking
4. **Keep your web app current** with latest race results

## 🗂️ Contents

### Main Update Scripts
- **`run_daily_update.py`** - Run this daily to fetch new races
- **`run_all_etl.py`** - Runs all ETL pipelines (weekly recommended)
- **`load_and_update.py`** - Loads data and updates aggregates

### Analytics Modules
- **`athlete_info/`** - Computes athlete statistics and aggregates
- **`hill_info/`** - Computes course difficulty (HDI) and metrics
- **`worldcup_info/`** - Computes World Cup analytics

## 🚀 Manual Usage

### Update with Latest Data (Run Weekly)

```bash
# Activate virtual environment
cd "/Users/finnbahr/Desktop/FIS Scraping"
source fis-api/venv/bin/activate

# Run daily update
cd "alpine analytic database"
python3 run_daily_update.py

# Or run full ETL pipeline
python3 run_all_etl.py
```

### What Each Script Does

**Daily Update** (`run_daily_update.py`):
- Scrapes new races from last 7 days
- Updates raw tables
- Recomputes basic aggregates
- Fast (~5-10 minutes)

**Full ETL** (`run_all_etl.py`):
- Runs all analysis modules
- Recomputes all aggregates
- Updates athlete tiers
- Slower (~30-60 minutes)

## ⏰ Automatic Updates

### Option 1: macOS Launchd (Recommended)

Create a scheduled job to run weekly:

```bash
# Create launchd plist file
mkdir -p ~/Library/LaunchAgents

cat > ~/Library/LaunchAgents/com.fis.update.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.fis.update</string>

    <key>ProgramArguments</key>
    <array>
        <string>/Users/finnbahr/Desktop/FIS Scraping/fis-api/venv/bin/python3</string>
        <string>/Users/finnbahr/Desktop/FIS Scraping/alpine analytic database/run_daily_update.py</string>
    </array>

    <key>WorkingDirectory</key>
    <string>/Users/finnbahr/Desktop/FIS Scraping/alpine analytic database</string>

    <key>StartCalendarInterval</key>
    <dict>
        <key>Weekday</key>
        <integer>0</integer>  <!-- Sunday -->
        <key>Hour</key>
        <integer>2</integer>   <!-- 2 AM -->
        <key>Minute</key>
        <integer>0</integer>
    </dict>

    <key>StandardOutPath</key>
    <string>/tmp/fis-update.log</string>

    <key>StandardErrorPath</key>
    <string>/tmp/fis-update-error.log</string>
</dict>
</plist>
EOF

# Load the job
launchctl load ~/Library/LaunchAgents/com.fis.update.plist

# Check status
launchctl list | grep fis
```

**Runs every Sunday at 2 AM**

### Option 2: Cron Job

```bash
# Edit crontab
crontab -e

# Add this line (runs every Sunday at 2 AM)
0 2 * * 0 cd "/Users/finnbahr/Desktop/FIS Scraping/alpine analytic database" && /Users/finnbahr/Desktop/FIS\ Scraping/fis-api/venv/bin/python3 run_daily_update.py >> /tmp/fis-update.log 2>&1
```

### Option 3: Manual Schedule

Just run it yourself once a week:
```bash
cd "/Users/finnbahr/Desktop/FIS Scraping/alpine analytic database"
source ../fis-api/venv/bin/activate
python3 run_daily_update.py
```

## 📝 Update Log

Check update logs:
```bash
# View last update
tail -50 /tmp/fis-update.log

# View errors
tail -50 /tmp/fis-update-error.log
```

## 🔧 Configuration

The scripts use environment variables from:
- `/Users/finnbahr/Desktop/FIS Scraping/.env`

Make sure these are set:
```env
DB_HOST=127.0.0.1
DB_PORT=5433
DB_USER=alpine_analytics
DB_PASSWORD=Plymouthskiing1!
DB_NAME=alpine_analytics
RAW_DB_NAME=alpine_analytics
```

## ⚠️ Important Notes

1. **PostgreSQL must be running** for updates to work
2. **Updates can take 5-60 minutes** depending on script
3. **Web app continues to work** during updates (reads are not blocked)
4. **Check logs** after each update to verify success
5. **Backup database** before major updates (optional but recommended)

## 🗓️ Recommended Schedule

- **Daily**: Not needed (races happen 1-2x per week in season)
- **Weekly**: ✅ Perfect (Sundays during ski season)
- **Monthly**: OK for off-season

## 🛑 Stop Automatic Updates

To disable automatic updates:

```bash
# Launchd
launchctl unload ~/Library/LaunchAgents/com.fis.update.plist

# Cron
crontab -e  # then delete the line
```

## 📊 What Gets Updated

When you run the update scripts:

### Raw Data Tables
- `raw.fis_results` - New race results
- `raw.race_details` - New race metadata

### Aggregate Tables
- `athlete_aggregate.*` - Athlete statistics
- `course_aggregate.*` - Course metrics
- `race_aggregate.*` - Race analytics

### Your Web App
- Leaderboards show latest results
- Athlete profiles update automatically
- Course difficulty recalculated
- Analytics refresh with new data

## 🔍 Troubleshooting

**Script fails with "connection refused"**
- PostgreSQL is not running
- Start it: `brew services start postgresql@14`

**Script runs but no new data**
- No new races in scraping window
- Check FIS website for recent results

**Script is slow**
- Large backlog of races to process
- Be patient or reduce date range

**Permission denied**
- Check file permissions
- Make scripts executable: `chmod +x *.py`

## 📚 More Information

- Database schema: `../DATA_DICTIONARY.md`
- Web app: `../fis-frontend/`
- API: `../fis-api/`

---

**Last Updated**: February 14, 2026
**Status**: ✅ Ready for automatic updates
