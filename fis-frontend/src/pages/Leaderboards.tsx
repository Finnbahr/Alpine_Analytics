import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { getLeaderboard, getHotStreak } from '../services/api';
import type { LeaderboardAthlete, HotStreakAthlete } from '../types';
import { TrophyIcon, FireIcon } from '@heroicons/react/24/solid';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorMessage, { EmptyState } from '../components/ErrorMessage';

const DISCIPLINES = ['Slalom', 'Giant Slalom', 'Super G', 'Downhill', 'Alpine Combined'];

export default function Leaderboards() {
  const { discipline } = useParams();
  const [selectedDiscipline, setSelectedDiscipline] = useState(discipline || 'Slalom');
  const [showHotStreak, setShowHotStreak] = useState(false);
  const [leaderboard, setLeaderboard] = useState<LeaderboardAthlete[]>([]);
  const [hotStreak, setHotStreak] = useState<HotStreakAthlete[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      try {
        if (showHotStreak) {
          const data = await getHotStreak({ days: 365, limit: 50 });
          setHotStreak(data.data);
        } else {
          const data = await getLeaderboard(selectedDiscipline, { limit: 50 });
          setLeaderboard(data.data);
        }
      } catch (error) {
        console.error('Failed to fetch leaderboard:', error);
        setError('Failed to load leaderboard data. Please try again later.');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [selectedDiscipline, showHotStreak]);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">Leaderboards</h1>

        {/* Toggle between Discipline and Hot Streak */}
        <div className="flex space-x-2 mb-6">
          <button
            onClick={() => setShowHotStreak(false)}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              !showHotStreak
                ? 'bg-primary-600 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            <TrophyIcon className="h-5 w-5 inline mr-2" />
            By Discipline
          </button>
          <button
            onClick={() => setShowHotStreak(true)}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              showHotStreak
                ? 'bg-orange-600 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            <FireIcon className="h-5 w-5 inline mr-2" />
            Hot Streak
          </button>
        </div>

        {/* Discipline Selector */}
        {!showHotStreak && (
          <div className="flex flex-wrap gap-2">
            {DISCIPLINES.map((disc) => (
              <button
                key={disc}
                onClick={() => setSelectedDiscipline(disc)}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  selectedDiscipline === disc
                    ? 'bg-primary-100 text-primary-800 border-2 border-primary-600'
                    : 'bg-white text-gray-700 border-2 border-gray-300 hover:border-gray-400'
                }`}
              >
                {disc}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Leaderboard Table */}
      <div className="card">
        {loading ? (
          <div className="text-center py-12">
            <LoadingSpinner />
          </div>
        ) : error ? (
          <ErrorMessage title="Error" message={error} showHomeButton={false} />
        ) : (showHotStreak && hotStreak.length === 0) || (!showHotStreak && leaderboard.length === 0) ? (
          <EmptyState
            title="No Data Available"
            message={`No ${showHotStreak ? 'hot streak' : 'leaderboard'} data found for the selected criteria.`}
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-4 px-4 font-semibold text-gray-900">Rank</th>
                  <th className="text-left py-4 px-4 font-semibold text-gray-900">Athlete</th>
                  {showHotStreak && (
                    <th className="text-left py-4 px-4 font-semibold text-gray-900">
                      Discipline
                    </th>
                  )}
                  <th className="text-right py-4 px-4 font-semibold text-gray-900">
                    {showHotStreak ? 'Momentum' : 'Avg FIS Points'}
                  </th>
                  <th className="text-right py-4 px-4 font-semibold text-gray-900">
                    {showHotStreak ? 'Recent Races' : 'Wins'}
                  </th>
                  {!showHotStreak && (
                    <th className="text-right py-4 px-4 font-semibold text-gray-900">Podiums</th>
                  )}
                </tr>
              </thead>
              <tbody>
                {showHotStreak
                  ? hotStreak.map((athlete) => (
                      <tr
                        key={athlete.fis_code}
                        className="border-b border-gray-100 hover:bg-gray-50 transition-colors"
                      >
                        <td className="py-4 px-4">
                          <div className="flex items-center">
                            {athlete.rank <= 3 && (
                              <TrophyIcon
                                className={`h-5 w-5 mr-2 ${
                                  athlete.rank === 1
                                    ? 'text-yellow-500'
                                    : athlete.rank === 2
                                    ? 'text-gray-400'
                                    : 'text-orange-600'
                                }`}
                              />
                            )}
                            <span className="font-bold text-gray-900">#{athlete.rank}</span>
                          </div>
                        </td>
                        <td className="py-4 px-4">
                          <Link
                            to={`/athletes/${athlete.fis_code}`}
                            className="font-medium text-primary-600 hover:text-primary-700"
                          >
                            {athlete.name}
                          </Link>
                        </td>
                        <td className="py-4 px-4 text-gray-600">{athlete.discipline}</td>
                        <td className="py-4 px-4 text-right font-bold text-orange-600">
                          {athlete.momentum_z.toFixed(2)}
                        </td>
                        <td className="py-4 px-4 text-right text-gray-600">
                          {athlete.recent_races}
                        </td>
                      </tr>
                    ))
                  : leaderboard.map((athlete) => (
                      <tr
                        key={athlete.fis_code}
                        className="border-b border-gray-100 hover:bg-gray-50 transition-colors"
                      >
                        <td className="py-4 px-4">
                          <div className="flex items-center">
                            {athlete.rank <= 3 && (
                              <TrophyIcon
                                className={`h-5 w-5 mr-2 ${
                                  athlete.rank === 1
                                    ? 'text-yellow-500'
                                    : athlete.rank === 2
                                    ? 'text-gray-400'
                                    : 'text-orange-600'
                                }`}
                              />
                            )}
                            <span className="font-bold text-gray-900">#{athlete.rank}</span>
                          </div>
                        </td>
                        <td className="py-4 px-4">
                          <Link
                            to={`/athletes/${athlete.fis_code}`}
                            className="font-medium text-primary-600 hover:text-primary-700"
                          >
                            {athlete.name}
                          </Link>
                        </td>
                        <td className="py-4 px-4 text-right font-bold text-primary-600">
                          {athlete.avg_fis_points.toFixed(1)}
                        </td>
                        <td className="py-4 px-4 text-right text-gray-600">{athlete.wins || 0}</td>
                        <td className="py-4 px-4 text-right text-gray-600">
                          {athlete.podiums || 0}
                        </td>
                      </tr>
                    ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
