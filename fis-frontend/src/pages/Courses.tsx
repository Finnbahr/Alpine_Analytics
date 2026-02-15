import { useEffect, useState } from 'react';
import { getCourses, getCourseDifficulty } from '../services/api';
import type { Course, CourseDifficulty } from '../types';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { MapPinIcon, FireIcon } from '@heroicons/react/24/solid';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorMessage, { EmptyState } from '../components/ErrorMessage';

const DISCIPLINES = ['Slalom', 'Giant Slalom', 'Super G', 'Downhill', 'Alpine Combined'];

export default function Courses() {
  const [selectedDiscipline, setSelectedDiscipline] = useState('Slalom');
  const [difficultyCourses, setDifficultyCourses] = useState<CourseDifficulty[]>([]);
  const [allCourses, setAllCourses] = useState<Course[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'difficulty' | 'all'>('difficulty');

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      try {
        const [difficulty, courses] = await Promise.all([
          getCourseDifficulty(selectedDiscipline, { limit: 50 }),
          getCourses({ discipline: selectedDiscipline, limit: 50 }),
        ]);
        setDifficultyCourses(difficulty.data);
        setAllCourses(courses.data);
      } catch (error) {
        console.error('Failed to fetch courses:', error);
        setError('Failed to load course data. Please try again later.');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [selectedDiscipline]);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">Course Analytics</h1>

        {/* Discipline Selector */}
        <div className="flex flex-wrap gap-2 mb-6">
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

        {/* Tabs */}
        <div className="border-b border-gray-200">
          <div className="flex space-x-8">
            <button
              onClick={() => setActiveTab('difficulty')}
              className={`pb-4 border-b-2 transition-colors font-medium ${
                activeTab === 'difficulty'
                  ? 'border-primary-600 text-primary-600'
                  : 'border-transparent text-gray-600 hover:text-gray-900'
              }`}
            >
              <FireIcon className="h-5 w-5 inline mr-2" />
              Difficulty Rankings
            </button>
            <button
              onClick={() => setActiveTab('all')}
              className={`pb-4 border-b-2 transition-colors font-medium ${
                activeTab === 'all'
                  ? 'border-primary-600 text-primary-600'
                  : 'border-transparent text-gray-600 hover:text-gray-900'
              }`}
            >
              <MapPinIcon className="h-5 w-5 inline mr-2" />
              All Courses
            </button>
          </div>
        </div>
      </div>

      {loading ? (
        <div className="text-center py-12">
          <LoadingSpinner />
        </div>
      ) : error ? (
        <ErrorMessage message={error} />
      ) : activeTab === 'difficulty' ? (
        difficultyCourses.length === 0 ? (
          <EmptyState
            title="No Difficulty Data"
            message={`No course difficulty data available for ${selectedDiscipline}.`}
          />
        ) : (
        <div className="space-y-6">
          {/* Difficulty Chart */}
          <div className="card">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">
              Hill Difficulty Index (Top 15)
            </h2>
            <ResponsiveContainer width="100%" height={400}>
              <BarChart data={difficultyCourses.slice(0, 15)}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="location"
                  angle={-45}
                  textAnchor="end"
                  height={120}
                  tick={{ fontSize: 12 }}
                />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="hill_difficulty_index" fill="#ef4444" name="Difficulty Index" />
                <Bar dataKey="avg_dnf_rate" fill="#f97316" name="DNF Rate (%)" />
              </BarChart>
            </ResponsiveContainer>
            <div className="mt-4 p-4 bg-blue-50 rounded-lg">
              <h3 className="font-semibold text-blue-900 mb-2">About Hill Difficulty Index</h3>
              <p className="text-sm text-blue-800">
                The Hill Difficulty Index (HDI) is a composite score (0-100) based on:
                Winning Time (20%), Gate Count (10%), Start Altitude (10%), Vertical Drop (20%),
                and DNF Rate (40%). Higher scores indicate more challenging courses.
              </p>
            </div>
          </div>

          {/* Difficulty Table */}
          <div className="card">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Hardest Courses</h2>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-3 px-4 font-semibold text-gray-900">Rank</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-900">Location</th>
                    <th className="text-right py-3 px-4 font-semibold text-gray-900">HDI</th>
                    <th className="text-right py-3 px-4 font-semibold text-gray-900">DNF %</th>
                    <th className="text-right py-3 px-4 font-semibold text-gray-900">Races</th>
                    <th className="text-right py-3 px-4 font-semibold text-gray-900">Details</th>
                  </tr>
                </thead>
                <tbody>
                  {difficultyCourses.slice(0, 20).map((course, idx) => (
                    <tr key={idx} className="border-b border-gray-100 hover:bg-gray-50">
                      <td className="py-3 px-4 font-bold text-gray-900">#{idx + 1}</td>
                      <td className="py-3 px-4">
                        <div className="font-medium text-gray-900">{course.location}</div>
                        <div className="text-sm text-gray-500">
                          {course.homologation_number || 'N/A'}
                        </div>
                      </td>
                      <td className="py-3 px-4 text-right">
                        <span className="font-bold text-red-600">
                          {course.hill_difficulty_index.toFixed(1)}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right text-gray-900">
                        {(course.avg_dnf_rate * 100).toFixed(1)}%
                      </td>
                      <td className="py-3 px-4 text-right text-gray-600">
                        {course.race_count}
                      </td>
                      <td className="py-3 px-4 text-right">
                        <div className="text-xs text-gray-600">
                          {course.avg_vertical_drop && `${course.avg_vertical_drop.toFixed(0)}m drop`}
                          {course.avg_gate_count && ` • ${course.avg_gate_count.toFixed(0)} gates`}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Course Stats Grid */}
          <div className="grid md:grid-cols-3 gap-6">
            <div className="card">
              <h3 className="font-semibold text-gray-900 mb-4">Highest DNF Rate</h3>
              {difficultyCourses
                .slice()
                .sort((a, b) => b.avg_dnf_rate - a.avg_dnf_rate)
                .slice(0, 5)
                .map((course, idx) => (
                  <div key={idx} className="flex justify-between py-2 border-b border-gray-100">
                    <span className="text-gray-900">{course.location}</span>
                    <span className="font-semibold text-red-600">
                      {(course.avg_dnf_rate * 100).toFixed(1)}%
                    </span>
                  </div>
                ))}
            </div>

            <div className="card">
              <h3 className="font-semibold text-gray-900 mb-4">Longest Vertical Drop</h3>
              {difficultyCourses
                .filter((c) => c.avg_vertical_drop)
                .sort((a, b) => (b.avg_vertical_drop || 0) - (a.avg_vertical_drop || 0))
                .slice(0, 5)
                .map((course, idx) => (
                  <div key={idx} className="flex justify-between py-2 border-b border-gray-100">
                    <span className="text-gray-900">{course.location}</span>
                    <span className="font-semibold text-primary-600">
                      {course.avg_vertical_drop?.toFixed(0)}m
                    </span>
                  </div>
                ))}
            </div>

            <div className="card">
              <h3 className="font-semibold text-gray-900 mb-4">Most Gates</h3>
              {difficultyCourses
                .filter((c) => c.avg_gate_count)
                .sort((a, b) => (b.avg_gate_count || 0) - (a.avg_gate_count || 0))
                .slice(0, 5)
                .map((course, idx) => (
                  <div key={idx} className="flex justify-between py-2 border-b border-gray-100">
                    <span className="text-gray-900">{course.location}</span>
                    <span className="font-semibold text-primary-600">
                      {course.avg_gate_count?.toFixed(0)}
                    </span>
                  </div>
                ))}
            </div>
          </div>
        </div>
        )
      ) : allCourses.length === 0 ? (
        <EmptyState
          title="No Courses Found"
          message={`No courses found for ${selectedDiscipline}.`}
        />
      ) : (
        <div className="card">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">All Courses</h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {allCourses.map((course, idx) => (
              <div key={idx} className="p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                <div className="flex items-start justify-between">
                  <div>
                    <div className="font-semibold text-gray-900">{course.location}</div>
                    <div className="text-sm text-gray-600">{course.country}</div>
                  </div>
                  <div className="text-right">
                    <div className="font-bold text-primary-600">{course.race_count}</div>
                    <div className="text-xs text-gray-500">races</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
