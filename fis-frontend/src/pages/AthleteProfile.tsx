import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import {
  getAthlete,
  getAthleteRaces,
  getAthleteMomentum,
  getAthleteCourses,
} from '../services/api';
import type { AthleteProfile as AthleteProfileType } from '../types';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { TrophyIcon, FireIcon, MapPinIcon, ChartBarIcon } from '@heroicons/react/24/solid';
import { PageLoader } from '../components/LoadingSpinner';
import ErrorMessage from '../components/ErrorMessage';

export default function AthleteProfile() {
  const { fisCode } = useParams<{ fisCode: string }>();
  const [profile, setProfile] = useState<AthleteProfileType | null>(null);
  const [races, setRaces] = useState<any[]>([]);
  const [momentum, setMomentum] = useState<any[]>([]);
  const [courses, setCourses] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'races' | 'momentum' | 'courses'>('races');

  useEffect(() => {
    const fetchData = async () => {
      if (!fisCode) return;

      setLoading(true);
      setError(null);
      try {
        const [profileData, racesData, momentumData, coursesData] = await Promise.all([
          getAthlete(fisCode),
          getAthleteRaces(fisCode, { limit: 20 }),
          getAthleteMomentum(fisCode, { limit: 50 }),
          getAthleteCourses(fisCode, { min_races: 3 }),
        ]);

        setProfile(profileData);
        setRaces(racesData.data);
        setMomentum(momentumData.data);
        setCourses(coursesData.data);
      } catch (error) {
        console.error('Failed to fetch athlete data:', error);
        setError('Failed to load athlete profile. The athlete may not exist or there was a server error.');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [fisCode]);

  if (loading) {
    return <PageLoader />;
  }

  if (error || !profile) {
    return (
      <ErrorMessage
        title="Athlete Not Found"
        message={error || "The requested athlete profile could not be found."}
      />
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="card mb-8">
        <div className="flex items-start justify-between mb-6">
          <div>
            <h1 className="text-4xl font-bold text-gray-900 mb-2">{profile.name}</h1>
            <div className="flex items-center space-x-4 text-gray-600">
              {profile.country && (
                <span className="flex items-center">
                  <span className="text-2xl mr-2">🇺🇸</span>
                  {profile.country}
                </span>
              )}
              <span className="text-sm">FIS Code: {profile.fis_code}</span>
            </div>
          </div>
          {profile.momentum && (
            <div className="text-right">
              <div className="text-sm text-gray-600 mb-1">Current Momentum</div>
              <div className="flex items-center space-x-2">
                <FireIcon className={`h-6 w-6 ${
                  profile.momentum.trend === 'hot' ? 'text-orange-500' :
                  profile.momentum.trend === 'cold' ? 'text-blue-500' : 'text-gray-500'
                }`} />
                <span className="text-2xl font-bold text-gray-900">
                  {profile.momentum.current_momentum_z?.toFixed(2) || 'N/A'}
                </span>
              </div>
              <div className="text-xs text-gray-500 capitalize">{profile.momentum.trend}</div>
            </div>
          )}
        </div>

        {/* Career Stats */}
        {profile.career_stats && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 pt-6 border-t border-gray-200">
            <StatBox
              icon={<ChartBarIcon className="h-8 w-8 text-primary-600" />}
              label="Total Starts"
              value={profile.career_stats.starts}
            />
            <StatBox
              icon={<TrophyIcon className="h-8 w-8 text-yellow-500" />}
              label="Wins"
              value={profile.career_stats.wins}
            />
            <StatBox
              icon={<TrophyIcon className="h-8 w-8 text-gray-400" />}
              label="Podiums"
              value={profile.career_stats.podiums}
            />
            <StatBox
              icon={<ChartBarIcon className="h-8 w-8 text-primary-600" />}
              label="Avg FIS Points"
              value={profile.career_stats.avg_fis_points.toFixed(1)}
            />
          </div>
        )}

        {/* Current Tier */}
        {profile.current_tier && (
          <div className="mt-6 pt-6 border-t border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <span className="text-sm text-gray-600">Current Tier ({profile.current_tier.year}):</span>
                <span className="ml-2 font-bold text-primary-600">{profile.current_tier.tier}</span>
                <span className="ml-2 text-gray-600">in {profile.current_tier.discipline}</span>
              </div>
              <div className="text-right">
                <div className="text-sm text-gray-600">Season Stats</div>
                <div className="text-lg font-semibold text-gray-900">
                  {profile.current_tier.avg_fis_points.toFixed(1)} pts
                  <span className="text-sm text-gray-600 ml-2">
                    ({profile.current_tier.race_count} races)
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Tabs */}
      <div className="mb-6 border-b border-gray-200">
        <div className="flex space-x-8">
          <TabButton
            active={activeTab === 'races'}
            onClick={() => setActiveTab('races')}
            icon={<ChartBarIcon className="h-5 w-5" />}
            label="Race History"
          />
          <TabButton
            active={activeTab === 'momentum'}
            onClick={() => setActiveTab('momentum')}
            icon={<FireIcon className="h-5 w-5" />}
            label="Momentum"
          />
          <TabButton
            active={activeTab === 'courses'}
            onClick={() => setActiveTab('courses')}
            icon={<MapPinIcon className="h-5 w-5" />}
            label="Course Performance"
          />
        </div>
      </div>

      {/* Tab Content */}
      {activeTab === 'races' && (
        <div className="card">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Recent Race Results</h2>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-3 px-4 font-semibold text-gray-900">Date</th>
                  <th className="text-left py-3 px-4 font-semibold text-gray-900">Location</th>
                  <th className="text-left py-3 px-4 font-semibold text-gray-900">Discipline</th>
                  <th className="text-right py-3 px-4 font-semibold text-gray-900">Rank</th>
                  <th className="text-right py-3 px-4 font-semibold text-gray-900">FIS Points</th>
                  <th className="text-right py-3 px-4 font-semibold text-gray-900">Z-Score</th>
                </tr>
              </thead>
              <tbody>
                {races.map((race, idx) => (
                  <tr key={idx} className="border-b border-gray-100 hover:bg-gray-50">
                    <td className="py-3 px-4 text-gray-600">
                      {new Date(race.date).toLocaleDateString()}
                    </td>
                    <td className="py-3 px-4">
                      <div className="font-medium text-gray-900">{race.location}</div>
                      <div className="text-sm text-gray-500">{race.country}</div>
                    </td>
                    <td className="py-3 px-4 text-gray-600">{race.discipline}</td>
                    <td className="py-3 px-4 text-right font-semibold text-gray-900">
                      {race.rank}
                    </td>
                    <td className="py-3 px-4 text-right text-gray-900">
                      {race.fis_points?.toFixed(1) || 'N/A'}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <span className={`font-semibold ${
                        race.race_z_score > 0 ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {race.race_z_score?.toFixed(2) || 'N/A'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeTab === 'momentum' && (
        <div className="space-y-6">
          <div className="card">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Momentum Over Time</h2>
            <ResponsiveContainer width="100%" height={400}>
              <LineChart data={momentum}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="date"
                  tickFormatter={(date) => new Date(date).toLocaleDateString('en-US', { month: 'short', year: '2-digit' })}
                />
                <YAxis />
                <Tooltip
                  labelFormatter={(date) => new Date(date).toLocaleDateString()}
                  formatter={(value) => (value as number).toFixed(2)}
                />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="momentum_z"
                  stroke="#f97316"
                  strokeWidth={2}
                  name="Momentum Z-Score"
                  dot={{ fill: '#f97316' }}
                />
                <Line
                  type="monotone"
                  dataKey="race_z_score"
                  stroke="#0ea5e9"
                  strokeWidth={2}
                  name="Race Z-Score"
                  dot={{ fill: '#0ea5e9' }}
                />
              </LineChart>
            </ResponsiveContainer>
            <div className="mt-4 text-sm text-gray-600">
              <p>
                <strong>Momentum Z-Score:</strong> Higher values indicate better recent form (hot streak)
              </p>
              <p className="mt-1">
                <strong>Race Z-Score:</strong> Performance relative to field (positive = above average)
              </p>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'courses' && (
        <div className="card">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Performance by Course</h2>
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={courses.slice(0, 15)}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="location"
                angle={-45}
                textAnchor="end"
                height={120}
                tick={{ fontSize: 12 }}
              />
              <YAxis />
              <Tooltip formatter={(value) => (value as number).toFixed(2)} />
              <Legend />
              <Bar dataKey="mean_race_z_score" fill="#0ea5e9" name="Avg Z-Score" />
            </BarChart>
          </ResponsiveContainer>
          <div className="mt-6">
            <h3 className="font-semibold text-gray-900 mb-4">Top Courses</h3>
            <div className="grid md:grid-cols-2 gap-4">
              {courses.slice(0, 6).map((course, idx) => (
                <div key={idx} className="p-4 bg-gray-50 rounded-lg">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="font-semibold text-gray-900">{course.location}</div>
                      <div className="text-sm text-gray-600">{course.discipline}</div>
                    </div>
                    <div className="text-right">
                      <div className="font-bold text-primary-600">
                        {course.mean_race_z_score.toFixed(2)}
                      </div>
                      <div className="text-xs text-gray-500">{course.race_count} races</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function StatBox({ icon, label, value }: { icon: React.ReactNode; label: string; value: string | number }) {
  return (
    <div className="text-center">
      <div className="flex justify-center mb-2">{icon}</div>
      <div className="text-3xl font-bold text-gray-900 mb-1">{value}</div>
      <div className="text-sm text-gray-600">{label}</div>
    </div>
  );
}

function TabButton({
  active,
  onClick,
  icon,
  label,
}: {
  active: boolean;
  onClick: () => void;
  icon: React.ReactNode;
  label: string;
}) {
  return (
    <button
      onClick={onClick}
      className={`flex items-center space-x-2 pb-4 border-b-2 transition-colors ${
        active
          ? 'border-primary-600 text-primary-600'
          : 'border-transparent text-gray-600 hover:text-gray-900'
      }`}
    >
      {icon}
      <span className="font-medium">{label}</span>
    </button>
  );
}
