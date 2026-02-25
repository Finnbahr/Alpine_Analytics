import { Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine, ComposedChart } from 'recharts';

interface StrokesGainedData {
  race_id: number;
  date: string;
  location: string;
  discipline: string;
  strokes_gained?: number;
  rank?: string;
}

interface BibData {
  race_id: number;
  date: string;
  location: string;
  discipline: string;
  bib_advantage?: number;
  bib?: number;
}

interface Props {
  strokesGainedData: StrokesGainedData[];
  bibData?: BibData[];
}

export default function StrokesGainedChart({ strokesGainedData, bibData }: Props) {
  // Merge the two datasets by race_id and date
  const mergedData = strokesGainedData.map(sg => {
    const bibMatch = bibData?.find(b => b.race_id === sg.race_id || b.date === sg.date);
    return {
      date: sg.date,
      location: sg.location,
      discipline: sg.discipline,
      strokes_gained: sg.strokes_gained || 0,
      bib_advantage: bibMatch?.bib_advantage || null,
      bib: bibMatch?.bib || null,
    };
  });

  return (
    <div className="space-y-6">
      <div className="card">
        <h3 className="text-xl font-bold text-gray-100 mb-4">Strokes Gained Over Time</h3>
        <ResponsiveContainer width="100%" height={400}>
          <ComposedChart data={mergedData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis
              dataKey="date"
              tickFormatter={(date) => new Date(date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
              stroke="#9ca3af"
              tick={{ fontSize: 11 }}
            />
            <YAxis stroke="#9ca3af" />
            <Tooltip
              labelFormatter={(date) => new Date(date).toLocaleDateString()}
              formatter={(value: number | null | undefined, name: string) => {
                if (value === null || value === undefined) return ['N/A', name];
                return [value.toFixed(2), name];
              }}
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
            {bibData && bibData.length > 0 && (
              <Line
                type="monotone"
                dataKey="bib_advantage"
                stroke="#3b82f6"
                strokeWidth={2}
                name="Bib Advantage"
                dot={{ fill: '#3b82f6', r: 4 }}
                activeDot={{ r: 6 }}
                connectNulls
              />
            )}
          </ComposedChart>
        </ResponsiveContainer>
        <div className="mt-4 text-sm text-gray-400 space-y-1">
          <p>
            <strong className="text-emerald-400">Strokes Gained:</strong> Performance relative to field average. Positive = above average.
          </p>
          {bibData && bibData.length > 0 && (
            <p>
              <strong className="text-blue-400">Bib Advantage:</strong> Expected rank advantage based on start position. Positive = earlier bib helps performance.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
