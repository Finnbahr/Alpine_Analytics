import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine, Cell } from 'recharts';

interface RegressionCoefficient {
  characteristic: string;
  coefficient: number;
  r_squared?: number;
}

interface Props {
  data: RegressionCoefficient[];
  discipline: string;
}

const formatCharacteristic = (char: string) => {
  const mapping: Record<string, string> = {
    'gate_count': 'Gate Count',
    'start_altitude': 'Start Altitude',
    'vertical_drop': 'Vertical Drop',
    'winning_time': 'Winning Time',
    'dnf_rate': 'DNF Rate',
    'course_length': 'Course Length'
  };
  return mapping[char] || char.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
};

export default function RegressionChart({ data, discipline }: Props) {
  // Filter out characteristics with very small coefficients
  const significantData = data
    .filter(d => Math.abs(d.coefficient) > 0.001)
    .map(d => ({
      ...d,
      name: formatCharacteristic(d.characteristic),
      coefficient: Number(d.coefficient.toFixed(4))
    }))
    .sort((a, b) => Math.abs(b.coefficient) - Math.abs(a.coefficient))
    .slice(0, 6);

  const getBarColor = (value: number) => {
    return value > 0 ? '#10b981' : '#ef4444';
  };

  return (
    <div className="card">
      <div className="mb-4">
        <h3 className="text-xl font-bold text-gray-100">Course Characteristic Impact</h3>
        <p className="text-sm text-gray-400 mt-1">
          {discipline} • R² = {data[0]?.r_squared?.toFixed(3) || 'N/A'}
        </p>
      </div>
      <ResponsiveContainer width="100%" height={400}>
        <BarChart data={significantData} layout="vertical" margin={{ left: 100 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis
            type="number"
            stroke="#9ca3af"
            label={{ value: 'Coefficient', position: 'insideBottom', offset: -5, style: { fill: '#9ca3af' } }}
          />
          <YAxis
            type="category"
            dataKey="name"
            stroke="#9ca3af"
            width={90}
            tick={{ fontSize: 12 }}
          />
          <Tooltip
            formatter={(value: number) => value.toFixed(4)}
            contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '0.5rem' }}
            labelStyle={{ color: '#f3f4f6' }}
          />
          <Legend wrapperStyle={{ color: '#f3f4f6' }} />
          <ReferenceLine x={0} stroke="#6b7280" strokeWidth={2} />
          <Bar dataKey="coefficient" name="Impact on Performance" radius={[0, 4, 4, 0]}>
            {significantData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={getBarColor(entry.coefficient)} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      <div className="mt-4 text-sm text-gray-400 space-y-1">
        <p>
          <strong className="text-gray-300">Positive coefficients (green):</strong> Athlete performs better on courses with higher values
        </p>
        <p>
          <strong className="text-gray-300">Negative coefficients (red):</strong> Athlete performs better on courses with lower values
        </p>
      </div>
    </div>
  );
}
