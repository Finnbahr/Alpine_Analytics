import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getHotStreak, getLeaderboard } from '../services/api';
import type { HotStreakAthlete, LeaderboardAthlete } from '../types';
import { FireIcon, TrophyIcon, MapPinIcon, ChartBarIcon } from '@heroicons/react/24/solid';
import { PageLoader } from '../components/LoadingSpinner';
import ErrorMessage from '../components/ErrorMessage';

export default function Home() {
  const [hotAthletes, setHotAthletes] = useState<HotStreakAthlete[]>([]);
  const [slalomLeaders, setSlalomLeaders] = useState<LeaderboardAthlete[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [hot, slalom] = await Promise.all([
          getHotStreak({ days: 365, limit: 5 }),
          getLeaderboard('Slalom', { limit: 5 }),
        ]);
        setHotAthletes(hot.data);
        setSlalomLeaders(slalom.data);
        setError(null);
      } catch (error) {
        console.error('Failed to fetch data:', error);
        setError('Failed to load leaderboards. Please try again later.');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return <PageLoader />;
  }

  if (error) {
    return <ErrorMessage message={error} />;
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Hero Section */}
      <div className="bg-gradient-to-r from-primary-600 to-primary-800 rounded-xl p-8 text-white mb-8">
        <h1 className="text-4xl font-bold mb-4">FIS Alpine Analytics</h1>
        <p className="text-xl text-primary-100 mb-6">
          Professional alpine skiing statistics, rankings, and insights
        </p>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatCard icon={<TrophyIcon className="h-6 w-6" />} label="Athletes" value="29K+" />
          <StatCard icon={<MapPinIcon className="h-6 w-6" />} label="Locations" value="1.3K+" />
          <StatCard icon={<ChartBarIcon className="h-6 w-6" />} label="Races" value="35K+" />
          <StatCard icon={<FireIcon className="h-6 w-6" />} label="Results" value="1.5M+" />
        </div>
      </div>

      {/* Quick Links */}
      <div className="grid md:grid-cols-4 gap-6 mb-8">
        <QuickLink
          to="/leaderboards"
          title="Leaderboards"
          description="View top athletes by discipline"
          icon="🏆"
        />
        <QuickLink
          to="/athletes"
          title="Athletes"
          description="Browse athlete profiles"
          icon="⛷️"
        />
        <QuickLink
          to="/courses"
          title="Courses"
          description="Explore course difficulty"
          icon="🏔️"
        />
        <QuickLink
          to="/analytics"
          title="Analytics"
          description="In-depth statistics"
          icon="📊"
        />
      </div>

      <div className="grid lg:grid-cols-2 gap-8">
        {/* Hot Streak */}
        <div className="card">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-gray-900 flex items-center">
              <FireIcon className="h-7 w-7 text-orange-500 mr-2" />
              Hot Streak
            </h2>
            <Link to="/leaderboards/hot-streak" className="text-primary-600 hover:text-primary-700 text-sm font-medium">
              View All →
            </Link>
          </div>
          <div className="space-y-3">
            {hotAthletes.map((athlete) => (
              <Link
                key={athlete.fis_code}
                to={`/athletes/${athlete.fis_code}`}
                className="block p-4 hover:bg-gray-50 rounded-lg transition-colors"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <div className="text-2xl font-bold text-gray-400">#{athlete.rank}</div>
                    <div>
                      <div className="font-semibold text-gray-900">{athlete.name}</div>
                      <div className="text-sm text-gray-500">{athlete.discipline}</div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="font-bold text-orange-600">
                      {athlete.momentum_z.toFixed(2)}
                    </div>
                    <div className="text-xs text-gray-500">{athlete.recent_races} races</div>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </div>

        {/* Slalom Leaders */}
        <div className="card">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-gray-900 flex items-center">
              <TrophyIcon className="h-7 w-7 text-yellow-500 mr-2" />
              Slalom Leaders
            </h2>
            <Link to="/leaderboards/slalom" className="text-primary-600 hover:text-primary-700 text-sm font-medium">
              View All →
            </Link>
          </div>
          <div className="space-y-3">
            {slalomLeaders.map((athlete) => (
              <Link
                key={athlete.fis_code}
                to={`/athletes/${athlete.fis_code}`}
                className="block p-4 hover:bg-gray-50 rounded-lg transition-colors"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <div className="text-2xl font-bold text-gray-400">#{athlete.rank}</div>
                    <div>
                      <div className="font-semibold text-gray-900">{athlete.name}</div>
                      <div className="text-sm text-gray-500">
                        {athlete.wins} wins • {athlete.podiums} podiums
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="font-bold text-primary-600">
                      {athlete.avg_fis_points.toFixed(1)}
                    </div>
                    <div className="text-xs text-gray-500">FIS pts</div>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function StatCard({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return (
    <div className="bg-white/10 rounded-lg p-4">
      <div className="flex items-center space-x-2 mb-2">
        {icon}
        <span className="text-sm text-primary-100">{label}</span>
      </div>
      <div className="text-2xl font-bold">{value}</div>
    </div>
  );
}

function QuickLink({
  to,
  title,
  description,
  icon,
}: {
  to: string;
  title: string;
  description: string;
  icon: string;
}) {
  return (
    <Link to={to} className="card hover:shadow-lg transition-shadow">
      <div className="text-4xl mb-3">{icon}</div>
      <h3 className="text-lg font-semibold text-gray-900 mb-1">{title}</h3>
      <p className="text-sm text-gray-600">{description}</p>
    </Link>
  );
}
