# Data Dictionary

**Last Updated**: February 12, 2026

Complete reference for all database tables and columns in the FIS Alpine Analytics platform.

---

## Quick Reference

| Schema | Tables | Purpose |
|--------|--------|---------|
| **raw** | 2 | Source data from FIS scraper |
| **race_aggregate** | 3 | Race-level analytics |
| **athlete_aggregate** | 10 | Athlete-level analytics |
| **course_aggregate** | 7 | Course/location analytics |
| **worldcup_aggregate** | 2 | World Cup level analytics |

**Total**: 24 tables, ~6.7M records

---

## raw Schema (Source Data)

### raw.fis_results
**Purpose**: Individual race results for each athlete
**Rows**: 1,512,315

| Column | Type | Description |
|--------|------|-------------|
| race_id | bigint | Unique race identifier (FK to race_details) |
| fis_code | text | FIS athlete code |
| name | text | Athlete name (format: "LASTNAME Firstname") |
| country | text | 3-letter country code (e.g., "USA", "AUT") |
| rank | text | Final rank (e.g., "1", "DNF", "DSQ") |
| bib | text | Start bib number |
| fis_points | text | FIS points for this race |
| final_time | text | Final time (format: "M:SS.XX") |

**Indexes**:
- `fis_code` - For athlete lookups
- `race_id` - For race result queries
- `LOWER(name)` - For case-insensitive search

**Common Queries**:
```sql
-- Get athlete's race results
SELECT * FROM raw.fis_results WHERE fis_code = '54063';

-- Search athletes by name
SELECT DISTINCT fis_code, name FROM raw.fis_results
WHERE LOWER(name) LIKE '%shiffrin%';

-- Get race results
SELECT * FROM raw.fis_results WHERE race_id = 12345
ORDER BY CAST(rank AS INTEGER) NULLS LAST;
```

---

### raw.race_details
**Purpose**: Metadata for each race
**Rows**: 34,788

| Column | Type | Description |
|--------|------|-------------|
| race_id | bigint | Unique race identifier (PK) |
| date | date | Race date |
| location | text | Race location (e.g., "Val d'Isere") |
| country | text | Host country |
| discipline | text | Discipline (e.g., "Slalom", "Giant Slalom") |
| race_type | text | Type (e.g., "World Cup", "European Cup") |
| homologation_number | text | Course homologation number |
| vertical_drop | text | Vertical drop in meters |
| start_altitude | text | Start altitude in meters |
| first_run_number_of_gates | text | Number of gates in run 1 |

**Indexes**:
- `date` - For time-based queries
- `discipline` - For discipline filtering
- `LOWER(location)` - For location search

**Common Queries**:
```sql
-- Recent races
SELECT * FROM raw.race_details
WHERE date >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY date DESC;

-- Find races at location
SELECT * FROM raw.race_details
WHERE LOWER(location) LIKE '%val d%';
```

---

## race_aggregate Schema (Race-Level Analytics)

### race_aggregate.race_z_score
**Purpose**: Standardized performance metric for each athlete in each race
**Rows**: 940,911

| Column | Type | Description |
|--------|------|-------------|
| race_id | bigint | Race identifier |
| fis_code | text | Athlete FIS code |
| name | text | Athlete name |
| race_z_score | double | Z-score (higher = better performance) |

**Formula**: `(mean_fis_points - athlete_fis_points) / std_fis_points`

**Use Cases**:
- Athlete performance comparison
- Historical performance tracking
- Performance trends

**Common Queries**:
```sql
-- Athlete's z-score history
SELECT race_id, race_z_score FROM race_aggregate.race_z_score
WHERE fis_code = '54063' ORDER BY race_id DESC;

-- Best performances (top z-scores)
SELECT * FROM race_aggregate.race_z_score
WHERE race_z_score > 2.0 ORDER BY race_z_score DESC;
```

---

### race_aggregate.strokes_gained
**Purpose**: Points gained vs field average
**Rows**: 940,911

| Column | Type | Description |
|--------|------|-------------|
| race_id | bigint | Race identifier |
| fis_code | text | Athlete FIS code |
| name | text | Athlete name |
| fis_points | double | Athlete's FIS points |
| points_gained | double | Points gained vs field average (positive = better) |

**Formula**: `avg_race_fis_points - athlete_fis_points`

**Note**: This table has limited columns. For full race context (date, location), join with `raw.race_details` or `raw.fis_results`.

---

### race_aggregate.strokes_gained_bib_relative
**Purpose**: Performance vs nearby start positions (±5 bibs)
**Rows**: 1,512,315

| Column | Type | Description |
|--------|------|-------------|
| race_id | bigint | Race identifier |
| fis_code | text | Athlete FIS code |
| bib | double | Start bib number |
| bib_strokes_gained | double | Points gained vs ±5 bib positions |

**Use Case**: Measure advantage/disadvantage of start position

---

## athlete_aggregate Schema (Athlete-Level Analytics)

### athlete_aggregate.basic_athlete_info_career
**Purpose**: Career statistics for each athlete
**Rows**: 28,635

| Column | Type | Description |
|--------|------|-------------|
| fis_code | text | Athlete FIS code (PK) |
| name | text | Athlete name |
| starts | integer | Total race starts |
| podiums | integer | Total podium finishes (top 3) |
| wins | integer | Total wins |
| avg_fis_points | double | Average FIS points across career |

**Common Queries**:
```sql
-- Athlete profile
SELECT * FROM athlete_aggregate.basic_athlete_info_career
WHERE fis_code = '54063';

-- Top performers (most wins)
SELECT * FROM athlete_aggregate.basic_athlete_info_career
ORDER BY wins DESC LIMIT 50;
```

---

### athlete_aggregate.performance_tiers
**Purpose**: Tier classification (Elite, Contender, Middle, Developing)
**Rows**: 199,446 (includes yearly tiers)

| Column | Type | Description |
|--------|------|-------------|
| fis_code | text | Athlete FIS code |
| name | text | Athlete name |
| discipline | text | Discipline |
| year | integer | Season year |
| race_count | bigint | Number of races |
| avg_fis_points | double | Average FIS points |
| log_avg_fis_points | double | Log-transformed avg FIS points (for tier calculation) |
| tier | text | Tier ("Elite", "Contender", "Middle", "Developing") |

**Tier Calculation**: Based on log(avg_fis_points) quartiles within discipline

**Common Queries**:
```sql
-- Elite athletes in Slalom
SELECT fis_code, name, avg_fis_points FROM athlete_aggregate.performance_tiers
WHERE discipline = 'Slalom' AND tier = 'Elite' AND year = 2025
ORDER BY avg_fis_points LIMIT 50;

-- Athlete's tier progression over years
SELECT year, tier, avg_fis_points FROM athlete_aggregate.performance_tiers
WHERE fis_code = '54063' AND discipline = 'Slalom'
ORDER BY year;
```

---

### athlete_aggregate.hot_streak
**Purpose**: Momentum tracking using EWMA (Exponentially Weighted Moving Average)
**Rows**: 863,316

| Column | Type | Description |
|--------|------|-------------|
| race_id | bigint | Race identifier |
| fis_code | text | Athlete FIS code |
| name | text | Athlete name |
| date | date | Race date |
| discipline | text | Discipline |
| race_z_score | double | Raw z-score for this race |
| ewma_race_z | double | EWMA of z-scores (momentum indicator) |
| ewstd_race_z | double | EWMA of z-score std dev |
| momentum_z | double | Momentum score (ewma / ewstd) |

**Key Metric**: `momentum_z` - Higher = hotter streak

**Common Queries**:
```sql
-- Current hot athletes (last 30 days)
SELECT fis_code, name, discipline, MAX(momentum_z) as peak_momentum
FROM athlete_aggregate.hot_streak
WHERE date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY fis_code, name, discipline
ORDER BY peak_momentum DESC LIMIT 50;

-- Athlete's momentum over time
SELECT date, momentum_z FROM athlete_aggregate.hot_streak
WHERE fis_code = '54063' AND discipline = 'Slalom'
ORDER BY date DESC LIMIT 50;
```

---

### athlete_aggregate.top_3_performances_career
**Purpose**: Top 3 career performances for each athlete
**Rows**: 197,944

| Column | Type | Description |
|--------|------|-------------|
| race_id | bigint | Race identifier |
| fis_code | text | Athlete FIS code |
| name | text | Athlete name |
| fis_points | double | FIS points |
| rank | text | Final rank |
| date | date | Race date |
| location | text | Race location |
| discipline | text | Discipline |
| race_z_score | double | Z-score for this race |

**Use Case**: Show athlete's best performances

---

### athlete_aggregate.course_regression
**Purpose**: Linear regression coefficients for performance prediction
**Rows**: 199,926

| Column | Type | Description |
|--------|------|-------------|
| fis_code | text | Athlete FIS code |
| name | text | Athlete name |
| discipline | text | Discipline |
| trait | text | Course feature (e.g., "vertical_drop", "gate_count") |
| coefficient | double | Regression coefficient |
| r_squared | double | Model R² (goodness of fit) |
| race_count | integer | Number of races in model |

**Use Case**: Predict athlete performance based on course characteristics

---

### athlete_aggregate.course_traits
**Purpose**: Performance by course characteristic bins (quintiles)
**Rows**: 890,694

| Column | Type | Description |
|--------|------|-------------|
| fis_code | text | Athlete FIS code |
| name | text | Athlete name |
| discipline | text | Discipline |
| trait | text | Course feature |
| trait_bin | text | Quintile bin (e.g., "(0.0, 1000.0]") |
| avg_performance_delta | double | Avg performance delta in this bin |
| avg_z_score | double | Average z-score in this bin |
| race_count | integer | Number of races in this bin |

**Use Case**: "How does Shiffrin perform on steep courses vs flat courses?"

---

## course_aggregate Schema (Course-Level Analytics)

### course_aggregate.basic_stats
**Purpose**: Course characteristic aggregations
**Rows**: 3,891

**Key Columns** (49 total):
- `location`, `homologation_number`, `discipline`, `country`
- `race_count` - Number of races at this course
- Vertical drop: `min_`, `max_`, `mean_`, `median_`, `std_vertical_drop`
- Gate count: `min_`, `max_`, `mean_`, `median_`, `std_gate_count`
- Start altitude: `min_`, `max_`, `mean_`, `median_`, `std_start_altitude`
- Winning time: `min_`, `max_`, `mean_`, `median_`, `std_winning_time`

**Use Case**: Course characteristics for display/filtering

---

### course_aggregate.difficulty_index
**Purpose**: Hill Difficulty Index (HDI) - composite difficulty score
**Rows**: 3,892

| Column | Type | Description |
|--------|------|-------------|
| location | text | Course location |
| discipline | text | Discipline |
| homologation_number | text | Course homologation |
| hill_difficulty_index | real | HDI score (0-100, higher = harder) |
| avg_dnf_rate | real | DNF rate (% did not finish) |
| race_count | integer | Number of races |
| avg_winning_time | text | Average winning time |
| avg_gate_count | real | Average number of gates |
| avg_start_altitude | real | Average start altitude (m) |
| avg_vertical_drop | real | Average vertical drop (m) |

**HDI Formula**: Weighted composite of:
- Winning time (20%)
- Gate count (10%)
- Start altitude (10%)
- Vertical drop (20%)
- DNF rate (40%)

**Common Queries**:
```sql
-- Hardest Slalom courses
SELECT location, hill_difficulty_index, avg_dnf_rate
FROM course_aggregate.difficulty_index
WHERE discipline = 'Slalom'
ORDER BY hill_difficulty_index DESC LIMIT 20;
```

---

### course_aggregate.location_performance
**Purpose**: Athlete performance at specific locations
**Rows**: 538,964

| Column | Type | Description |
|--------|------|-------------|
| fis_code | text | Athlete FIS code |
| name | text | Athlete name |
| discipline | text | Discipline |
| location | text | Course location |
| homologation_number | text | Course homologation |
| race_count | integer | Races at this location |
| mean_points_gained | double | Avg points gained vs field |
| mean_race_z_score | double | Average z-score at this location |

**Use Case**: "How does athlete X perform at location Y?"

**Common Queries**:
```sql
-- Shiffrin's best locations
SELECT location, race_count, mean_race_z_score
FROM course_aggregate.location_performance
WHERE fis_code = '54063' AND race_count >= 3
ORDER BY mean_race_z_score DESC LIMIT 20;
```

---

### course_aggregate.best_courses
**Purpose**: Course quality rankings
**Rows**: 3,453

| Column | Type | Description |
|--------|------|-------------|
| location | text | Course location |
| discipline | text | Discipline |
| mean_z_score | double | Average z-score at this course |
| performance_count | integer | Number of performances |
| rank | integer | Rank (1 = best course) |

**Use Case**: "Which courses produce the best skiing?"

---

### course_aggregate.favorability
**Purpose**: Course favorability via rolling deltas
**Rows**: 3,559

| Column | Type | Description |
|--------|------|-------------|
| location | text | Course location |
| discipline | text | Discipline |
| avg_performance_delta | double | Average performance delta |
| ci_lower | double | 95% confidence interval lower bound |
| ci_upper | double | 95% confidence interval upper bound |

**Use Case**: Identify courses where field performs better/worse than usual

---

## worldcup_aggregate Schema (Elite Competition)

### worldcup_aggregate.home_advantage
**Purpose**: Home vs Away performance analysis
**Rows**: 92

| Column | Type | Description |
|--------|------|-------------|
| competitor_country | text | Athlete's country |
| sex | text | Gender |
| discipline | text | Discipline |
| home_race_count | integer | Races at home |
| away_race_count | integer | Races away |
| home_avg_fis_points | double | Avg FIS points at home |
| away_avg_fis_points | double | Avg FIS points away |
| fis_points_pct_diff | double | % difference (negative = home advantage) |

**Use Case**: Quantify home field advantage

---

### worldcup_aggregate.setter_advantage
**Purpose**: Course setter country influence
**Rows**: 62

| Column | Type | Description |
|--------|------|-------------|
| setter_country | text | Course setter's country |
| sex | text | Gender |
| discipline | text | Discipline |
| home_setter_count | integer | Races with home setter |
| away_setter_count | integer | Races with away setter |
| fis_points_pct_diff | double | % difference in FIS points |

**Use Case**: Measure setter bias effect

---

## Common Query Patterns for API

### Athlete Profile
```sql
-- Basic info
SELECT * FROM athlete_aggregate.basic_athlete_info_career WHERE fis_code = ?;

-- Current tier
SELECT * FROM athlete_aggregate.performance_tiers
WHERE fis_code = ? AND year = EXTRACT(YEAR FROM CURRENT_DATE);

-- Recent momentum
SELECT * FROM athlete_aggregate.hot_streak
WHERE fis_code = ? ORDER BY date DESC LIMIT 20;
```

### Leaderboards
```sql
-- Elite athletes
SELECT fis_code, name, avg_fis_points FROM athlete_aggregate.performance_tiers
WHERE discipline = ? AND tier = 'Elite' AND year = ?
ORDER BY avg_fis_points LIMIT 50;

-- Hot athletes
SELECT fis_code, name, MAX(momentum_z) as peak_momentum
FROM athlete_aggregate.hot_streak
WHERE date >= CURRENT_DATE - INTERVAL '30 days' AND discipline = ?
GROUP BY fis_code, name
ORDER BY peak_momentum DESC LIMIT 50;
```

### Search
```sql
-- Athlete search
SELECT DISTINCT fis_code, name, country FROM raw.fis_results
WHERE LOWER(name) LIKE LOWER(CONCAT('%', ?, '%'))
LIMIT 50;

-- Location search
SELECT DISTINCT location, country FROM raw.race_details
WHERE LOWER(location) LIKE LOWER(CONCAT('%', ?, '%'))
LIMIT 50;
```

### Time Series
```sql
-- Athlete performance over time
SELECT hs.date, hs.momentum_z, hs.race_z_score
FROM athlete_aggregate.hot_streak hs
WHERE hs.fis_code = ? AND hs.discipline = ?
AND hs.date >= CURRENT_DATE - INTERVAL '2 years'
ORDER BY hs.date ASC;
```

---

## Performance Notes

**Fast Queries** (< 100ms):
- Exact lookups by fis_code
- Indexed column filtering (date, discipline)
- Small result sets (< 1000 rows)

**Slow Queries** (> 500ms):
- LIKE '%search%' on large tables without index
- Complex joins across multiple tables
- Large result sets (> 10,000 rows)

**Optimization Strategies**:
1. Use exact matches when possible
2. Leverage indexes (see index list above)
3. LIMIT results aggressively
4. Consider materialized views for common aggregations
5. Use connection pooling

---

**Last Updated**: February 12, 2026
**Database**: PostgreSQL 14+, alpine_analytics@127.0.0.1:5433
**Total Tables**: 24 | **Total Records**: ~6.7M
