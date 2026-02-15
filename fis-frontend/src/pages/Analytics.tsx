import { useEffect, useState } from 'react';
import { getHomeAdvantage } from '../services/api';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { HomeIcon, GlobeAltIcon, TrophyIcon } from '@heroicons/react/24/solid';
import { PageLoader } from '../components/LoadingSpinner';
import ErrorMessage, { EmptyState } from '../components/ErrorMessage';

const DISCIPLINES = ['Slalom', 'Giant Slalom', 'Super G', 'Downhill', 'Alpine Combined'];

export default function Analytics() {
  const [selectedDiscipline, setSelectedDiscipline] = useState<string | null>(null);
  const [homeAdvantageData, setHomeAdvantageData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await getHomeAdvantage({
          discipline: selectedDiscipline || undefined,
          limit: 50,
        });
        setHomeAdvantageData(data.data);
      } catch (error) {
        console.error('Failed to fetch analytics:', error);
        setError('Failed to load analytics data. Please try again later.');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [selectedDiscipline]);

  // Prepare data for chart
  const chartData = homeAdvantageData.slice(0, 15).map((item) => ({
    country: item.country,
    advantage: Math.abs(item.fis_points_pct_diff),
    type: item.fis_points_pct_diff < 0 ? 'Home Advantage' : 'Away Advantage',
  }));

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Advanced Analytics</h1>
        <p className="text-gray-600">Statistical insights and performance analysis</p>
      </div>

      {/* Discipline Filter */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Filter by Discipline
        </label>
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => setSelectedDiscipline(null)}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              selectedDiscipline === null
                ? 'bg-primary-600 text-white'
                : 'bg-white text-gray-700 border-2 border-gray-300 hover:border-gray-400'
            }`}
          >
            All Disciplines
          </button>
          {DISCIPLINES.map((disc) => (
            <button
              key={disc}
              onClick={() => setSelectedDiscipline(disc)}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                selectedDiscipline === disc
                  ? 'bg-primary-600 text-white'
                  : 'bg-white text-gray-700 border-2 border-gray-300 hover:border-gray-400'
              }`}
            >
              {disc}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <PageLoader />
      ) : error ? (
        <ErrorMessage message={error} />
      ) : homeAdvantageData.length === 0 ? (
        <EmptyState
          title="No Data Available"
          message="No home advantage data found for the selected discipline."
        />
      ) : (
        <div className="space-y-8">
          {/* Overview Cards */}
          <div className="grid md:grid-cols-3 gap-6">
            <div className="card">
              <div className="flex items-center space-x-3 mb-4">
                <HomeIcon className="h-8 w-8 text-green-600" />
                <h3 className="text-lg font-semibold text-gray-900">Biggest Home Advantage</h3>
              </div>
              {homeAdvantageData
                .filter((d) => d.fis_points_pct_diff < 0)
                .slice(0, 3)
                .map((item, idx) => (
                  <div key={idx} className="flex justify-between py-2 border-b border-gray-100">
                    <span className="text-gray-900">{item.country}</span>
                    <span className="font-semibold text-green-600">
                      {Math.abs(item.fis_points_pct_diff).toFixed(1)}%
                    </span>
                  </div>
                ))}
            </div>

            <div className="card">
              <div className="flex items-center space-x-3 mb-4">
                <GlobeAltIcon className="h-8 w-8 text-blue-600" />
                <h3 className="text-lg font-semibold text-gray-900">Best Away Performance</h3>
              </div>
              {homeAdvantageData
                .filter((d) => d.fis_points_pct_diff > 0)
                .slice(0, 3)
                .map((item, idx) => (
                  <div key={idx} className="flex justify-between py-2 border-b border-gray-100">
                    <span className="text-gray-900">{item.country}</span>
                    <span className="font-semibold text-blue-600">
                      {item.fis_points_pct_diff.toFixed(1)}%
                    </span>
                  </div>
                ))}
            </div>

            <div className="card">
              <div className="flex items-center space-x-3 mb-4">
                <TrophyIcon className="h-8 w-8 text-yellow-600" />
                <h3 className="text-lg font-semibold text-gray-900">Most Consistent</h3>
              </div>
              {homeAdvantageData
                .slice()
                .sort((a, b) => Math.abs(a.fis_points_pct_diff) - Math.abs(b.fis_points_pct_diff))
                .slice(0, 3)
                .map((item, idx) => (
                  <div key={idx} className="flex justify-between py-2 border-b border-gray-100">
                    <span className="text-gray-900">{item.country}</span>
                    <span className="font-semibold text-gray-600">
                      {Math.abs(item.fis_points_pct_diff).toFixed(1)}%
                    </span>
                  </div>
                ))}
            </div>
          </div>

          {/* Chart */}
          <div className="card">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">
              Home vs Away Performance by Country
            </h2>
            <ResponsiveContainer width="100%" height={400}>
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="country" />
                <YAxis label={{ value: 'Advantage (%)', angle: -90, position: 'insideLeft' }} />
                <Tooltip formatter={(value) => `${(value as number).toFixed(1)}%`} />
                <Legend />
                <Bar dataKey="advantage" fill="#0ea5e9" name="Performance Difference" />
              </BarChart>
            </ResponsiveContainer>
            <div className="mt-4 p-4 bg-blue-50 rounded-lg">
              <h3 className="font-semibold text-blue-900 mb-2">Understanding the Data</h3>
              <p className="text-sm text-blue-800 mb-2">
                <strong>Negative values (green):</strong> Athletes perform better at home
                (lower FIS points = better performance)
              </p>
              <p className="text-sm text-blue-800">
                <strong>Positive values (blue):</strong> Athletes perform better away from home
              </p>
            </div>
          </div>

          {/* Detailed Table */}
          <div className="card">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Detailed Statistics</h2>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-3 px-4 font-semibold text-gray-900">Country</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-900">Discipline</th>
                    <th className="text-right py-3 px-4 font-semibold text-gray-900">Home Races</th>
                    <th className="text-right py-3 px-4 font-semibold text-gray-900">Away Races</th>
                    <th className="text-right py-3 px-4 font-semibold text-gray-900">Home Avg</th>
                    <th className="text-right py-3 px-4 font-semibold text-gray-900">Away Avg</th>
                    <th className="text-right py-3 px-4 font-semibold text-gray-900">Difference</th>
                  </tr>
                </thead>
                <tbody>
                  {homeAdvantageData.map((item, idx) => (
                    <tr key={idx} className="border-b border-gray-100 hover:bg-gray-50">
                      <td className="py-3 px-4 font-medium text-gray-900">{item.country}</td>
                      <td className="py-3 px-4 text-gray-600">{item.discipline}</td>
                      <td className="py-3 px-4 text-right text-gray-600">
                        {item.home_race_count}
                      </td>
                      <td className="py-3 px-4 text-right text-gray-600">
                        {item.away_race_count}
                      </td>
                      <td className="py-3 px-4 text-right text-gray-900">
                        {item.home_avg_fis_points.toFixed(2)}
                      </td>
                      <td className="py-3 px-4 text-right text-gray-900">
                        {item.away_avg_fis_points.toFixed(2)}
                      </td>
                      <td className="py-3 px-4 text-right">
                        <span
                          className={`font-semibold ${
                            item.fis_points_pct_diff < 0 ? 'text-green-600' : 'text-blue-600'
                          }`}
                        >
                          {item.fis_points_pct_diff.toFixed(1)}%
                          {item.fis_points_pct_diff < 0 ? ' ↓' : ' ↑'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Insights */}
          <div className="card bg-gradient-to-r from-primary-50 to-blue-50">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Key Insights</h2>
            <div className="space-y-3">
              <div className="flex items-start space-x-3">
                <div className="flex-shrink-0 h-6 w-6 rounded-full bg-primary-600 flex items-center justify-center text-white text-sm font-bold">
                  1
                </div>
                <p className="text-gray-700">
                  <strong>Home advantage is real:</strong> Most countries show better performance
                  (lower FIS points) when competing at home venues.
                </p>
              </div>
              <div className="flex items-start space-x-3">
                <div className="flex-shrink-0 h-6 w-6 rounded-full bg-primary-600 flex items-center justify-center text-white text-sm font-bold">
                  2
                </div>
                <p className="text-gray-700">
                  <strong>Familiarity matters:</strong> Athletes who train regularly on specific
                  courses tend to perform better due to knowledge of terrain and conditions.
                </p>
              </div>
              <div className="flex items-start space-x-3">
                <div className="flex-shrink-0 h-6 w-6 rounded-full bg-primary-600 flex items-center justify-center text-white text-sm font-bold">
                  3
                </div>
                <p className="text-gray-700">
                  <strong>Crowd support:</strong> Home crowds provide psychological advantages,
                  potentially explaining the performance difference.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
