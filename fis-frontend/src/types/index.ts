/**
 * TypeScript types for API responses
 */

export interface Athlete {
  fis_code: string;
  name: string;
  country?: string;
  tier?: string;
  starts?: number;
  wins?: number;
  podiums?: number;
  avg_fis_points?: number;
}

export interface AthleteProfile {
  fis_code: string;
  name: string;
  country?: string;
  career_stats?: {
    starts: number;
    wins: number;
    podiums: number;
    avg_fis_points: number;
  };
  current_tier?: {
    tier: string;
    discipline: string;
    year: number;
    avg_fis_points: number;
    race_count: number;
  };
  momentum?: {
    current_momentum_z: number;
    trend: string;
    last_updated: string;
  };
}

export interface LeaderboardAthlete {
  rank: number;
  fis_code: string;
  name: string;
  country?: string;
  avg_fis_points: number;
  race_count: number;
  wins?: number;
  podiums?: number;
}

export interface HotStreakAthlete {
  rank: number;
  fis_code: string;
  name: string;
  country?: string;
  discipline: string;
  momentum_z: number;
  recent_races: number;
  last_race_date: string;
}

export interface Course {
  location: string;
  country?: string;
  discipline: string;
  race_count: number;
}

export interface CourseDifficulty {
  location: string;
  discipline: string;
  homologation_number?: string;
  hill_difficulty_index: number;
  avg_dnf_rate: number;
  race_count: number;
  avg_winning_time?: string;
  avg_gate_count?: number;
  avg_start_altitude?: number;
  avg_vertical_drop?: number;
}

export interface Race {
  race_id: number;
  date: string;
  location: string;
  country?: string;
  discipline: string;
  race_type?: string;
}

export interface SearchResult {
  query: string;
  results: {
    athletes: Array<{
      type: string;
      fis_code: string;
      name: string;
      country?: string;
      starts?: number;
      wins?: number;
    }>;
    locations: Array<{
      type: string;
      location: string;
      country?: string;
      race_count?: number;
    }>;
  };
  total_results: number;
}

export interface PaginationMeta {
  total?: number;
  limit: number;
  offset: number;
  has_more: boolean;
}
