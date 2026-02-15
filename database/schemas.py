"""
Database schema definitions and management
"""

# Schema structure for PostgreSQL databases
SCHEMAS = {
    'alpine_analytics': {
        'raw': 'Raw scraped data from FIS',
        'athlete_aggregate': 'Aggregated athlete performance metrics',
        'race_aggregate': 'Aggregated race-level metrics',
        'course_aggregate': 'Aggregated course/hill metrics'
    },
    'fis_aggregate_data': {
        'public': 'Additional aggregate tables'
    }
}

# Table definitions
RAW_TABLES = {
    'fis_results': {
        'schema': 'raw',
        'description': 'Individual athlete race results',
        'source': 'Scraped from FIS race results pages',
        'columns': [
            'race_id', 'rank', 'bib', 'fis_code', 'name',
            'equipment', 'yob', 'country', 'run1', 'run2',
            'final_time', 'fis_points', 'cup_points', 'status'
        ]
    },
    'race_details': {
        'schema': 'raw',
        'description': 'Race metadata and course details',
        'source': 'Scraped from FIS race detail pages',
        'columns': [
            'race_id', 'location', 'country', 'race_type', 'sex',
            'discipline', 'date', 'technical_delegate', 'td_country',
            'referee', 'ref_country', 'chief_of_race', 'chief_country',
            'start_altitude', 'finish_altitude', 'vertical_drop',
            'homologation_number', 'course_setter_1', 'cs1_country',
            'course_setter_2', 'cs2_country', 'gates_1', 'turning_gates_1',
            'start_time_1', 'gates_2', 'turning_gates_2', 'start_time_2',
            'dnf_rate', 'winning_time'
        ]
    }
}

ATHLETE_AGGREGATE_TABLES = {
    'race_z_score': 'Standardized performance scores per race',
    'strokes_gained': 'Performance relative to field average',
    'strokes_gained_bib_relative': 'Bib-adjusted performance metrics',
    'basic_athlete_info_career': 'Career-level athlete statistics',
    'basic_athlete_info_yearly': 'Year-by-year athlete statistics',
    'performance_consistency_career': 'Career consistency metrics',
    'performance_consistency_yearly': 'Yearly consistency metrics',
    'hot_streak': 'Momentum and streak analysis',
    'course_regression': 'Course characteristic regression coefficients',
    'course_trait': 'Performance by course trait bins',
    'performance_tiers': 'Athlete tier classification',
    'top_3_performances': 'Career and yearly podium finishes'
}

COURSE_AGGREGATE_TABLES = {
    'strokes_gained_location': 'Location-based performance metrics',
    'basic_hill_info': 'Hill/course statistics',
    'hill_difficulty_index': 'HDI scores and rankings',
    'hill_favorability_analysis': 'Course difficulty assessments',
    'similar_events': 'Comparable race identification'
}


def print_schema_structure():
    """Print the complete database schema structure"""
    print("=" * 70)
    print("FIS ALPINE ANALYTICS - DATABASE SCHEMA")
    print("=" * 70)

    print("\n📊 DATABASE: alpine_analytics")
    print("-" * 70)

    print("\n  Schema: raw")
    print("  " + "─" * 66)
    for table_name, info in RAW_TABLES.items():
        print(f"    • {table_name}")
        print(f"      {info['description']}")
        print(f"      Columns: {len(info['columns'])}")

    print("\n  Schema: athlete_aggregate")
    print("  " + "─" * 66)
    for table_name, description in ATHLETE_AGGREGATE_TABLES.items():
        print(f"    • {table_name}: {description}")

    print("\n  Schema: race_aggregate")
    print("  " + "─" * 66)
    print(f"    • race_z_score: Standardized performance scores")
    print(f"    • strokes_gained: Performance relative to field")
    print(f"    • strokes_gained_bib_relative: Bib-adjusted metrics")

    print("\n  Schema: course_aggregate")
    print("  " + "─" * 66)
    for table_name, description in COURSE_AGGREGATE_TABLES.items():
        print(f"    • {table_name}: {description}")

    print("\n" + "=" * 70)


if __name__ == '__main__':
    print_schema_structure()
