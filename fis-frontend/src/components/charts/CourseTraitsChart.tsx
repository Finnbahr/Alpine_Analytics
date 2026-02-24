import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine, Cell } from 'recharts';

interface CourseTraitData {
  trait: string;
  quintile: number;
  quintile_label: string;
  race_count: number;
  avg_z_score: number;
}

interface Props {
  data: CourseTraitData[];
  trait: string;
}

const formatTrait = (trait: string) => {
  const mapping: Record<string, string> = {
    'bib': 'Start Position',
    'vertical_drop': 'Vertical Drop',
    'gate_count': 'Gate Count',
    'start_altitude': 'Altitude',
    'winning_time': 'Winning Time'
  };
  return mapping[trait] || trait.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
};

export default function CourseTraitsChart({ data, trait }: Props) {
  // Group by quintile and aggregate (handle duplicates)
  const quintileMap = new Map<number, CourseTraitData>();

  data.forEach(item => {
    const existing = quintileMap.get(item.quintile);
    if (!existing || item.race_count > existing.race_count) {
      quintileMap.set(item.quintile, item);
    }
  });

  const chartData = Array.from(quintileMap.values())
    .sort((a, b) => a.quintile - b.quintile)
    .map(d => ({
      quintile: `Q${d.quintile + 1}`,
      label: d.quintile_label,
      avg_z_score: Number(d.avg_z_score.toFixed(2)),
      race_count: d.race_count
    }));

  const getBarColor = (value: number) => {
    if (value > 0.5) return '#10b981';
    if (value > 0) return '#84cc16';
    if (value > -0.5) return '#eab308';
    return '#ef4444';
  };

  return (
    <div className="card">
      <div className="mb-4">
        <h3 className="text-xl font-bold text-gray-100">Performance by {formatTrait(trait)}</h3>
        <p className="text-sm text-gray-400 mt-1">Average Z-Score across quintiles</p>
      </div>
      <ResponsiveContainer width="100%" height={350}>
        <BarChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis
            dataKey="quintile"
            stroke="#9ca3af"
          />
          <YAxis
            stroke="#9ca3af"
            label={{ value: 'Avg Z-Score', angle: -90, position: 'insideLeft', style: { fill: '#9ca3af' } }}
          />
          <Tooltip
            formatter={(value: number, name: string) => {
              if (name === 'avg_z_score') return [value.toFixed(2), 'Avg Z-Score'];
              return [value, name];
            }}
            labelFormatter={(quintile) => {
              const item = chartData.find(d => d.quintile === quintile);
              return item ? `${quintile}: ${item.label}` : quintile;
            }}
            contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '0.5rem' }}
            labelStyle={{ color: '#f3f4f6' }}
          />
          <Legend wrapperStyle={{ color: '#f3f4f6' }} />
          <ReferenceLine y={0} stroke="#6b7280" strokeDasharray="3 3" />
          <Bar dataKey="avg_z_score" name="Avg Z-Score" radius={[4, 4, 0, 0]}>
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={getBarColor(entry.avg_z_score)} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      <div className="mt-4 grid grid-cols-5 gap-2 text-xs">
        {chartData.map((item, idx) => (
          <div key={idx} className="p-2 bg-gray-800 rounded border border-gray-700">
            <div className="font-semibold text-gray-100">{item.quintile}</div>
            <div className="text-gray-400">{item.race_count} races</div>
            <div className="text-gray-500 truncate" title={item.label}>{item.label}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
