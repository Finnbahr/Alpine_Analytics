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
      coefficient: Number(d.coefficient.toFixed(4)),
      r_squared: d.r_squared
    }))
    .sort((a, b) => Math.abs(b.coefficient) - Math.abs(a.coefficient))
    .slice(0, 6);

  const getBarColor = (value: number) => {
    return value > 0 ? '#10b981' : '#ef4444';
  };

  return (
    <div className="card bg-black/40 border-cyan-500/20">
      <div className="mb-4">
        <h3 className="text-xl font-bold text-gray-100">Course Characteristic Impact</h3>
        <p className="text-sm text-cyan-400 mt-1">
          {discipline} • Each factor shows its correlation with performance
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
            formatter={(value: number | undefined, _name: string, props: any) => {
              if (!value) return ['N/A', 'Coefficient'];
              const r2 = props.payload.r_squared;
              return [
                `${value.toFixed(4)} (R² = ${r2?.toFixed(3) || 'N/A'})`,
                'Coefficient'
              ];
            }}
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
      <div className="mt-4 text-sm text-gray-400 space-y-2">
        <p>
          <strong className="text-emerald-400">Positive (green):</strong> Performs better when value is higher
        </p>
        <p>
          <strong className="text-red-400">Negative (red):</strong> Performs better when value is lower
        </p>
        <p>
          <strong className="text-cyan-400">R² value:</strong> Shows how well each factor predicts performance (0-1, higher = stronger correlation)
        </p>
      </div>
    </div>
  );
}
