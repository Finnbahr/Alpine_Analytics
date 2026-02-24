import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine } from 'recharts';

interface StrokesGainedData {
  race_id: number;
  date: string;
  location: string;
  discipline: string;
  strokes_gained: number;
  rank?: string;
}

interface Props {
  data: StrokesGainedData[];
}

export default function StrokesGainedChart({ data }: Props) {
  return (
    <div className="card">
      <h3 className="text-xl font-bold text-gray-100 mb-4">Strokes Gained Over Time</h3>
      <ResponsiveContainer width="100%" height={400}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis
            dataKey="date"
            tickFormatter={(date) => new Date(date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
            stroke="#9ca3af"
            tick={{ fontSize: 11 }}
          />
          <YAxis stroke="#9ca3af" label={{ value: 'Strokes Gained', angle: -90, position: 'insideLeft', style: { fill: '#9ca3af' } }} />
          <Tooltip
            labelFormatter={(date) => new Date(date).toLocaleDateString()}
            formatter={(value: number) => value.toFixed(2)}
            contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '0.5rem' }}
            labelStyle={{ color: '#f3f4f6' }}
          />
          <Legend wrapperStyle={{ color: '#f3f4f6' }} />
          <ReferenceLine y={0} stroke="#6b7280" strokeDasharray="3 3" />
          <Line
            type="monotone"
            dataKey="strokes_gained"
            stroke="#10b981"
            strokeWidth={2}
            name="Strokes Gained"
            dot={{ fill: '#10b981', r: 4 }}
            activeDot={{ r: 6 }}
          />
        </LineChart>
      </ResponsiveContainer>
      <div className="mt-4 text-sm text-gray-400">
        <p>
          <strong className="text-gray-300">Strokes Gained:</strong> Measures performance relative to the field average. Positive values indicate above-average performance.
        </p>
      </div>
    </div>
  );
}
