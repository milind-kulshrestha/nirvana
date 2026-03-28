import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

const METRICS = [
  { key: 'pe_ratio', label: 'P/E Ratio', color: '#0071e3' },
  { key: 'ps_ratio', label: 'P/S Ratio', color: '#34c759' },
  { key: 'pb_ratio', label: 'P/B Ratio', color: '#ff9500' },
  { key: 'ev_to_ebitda', label: 'EV/EBITDA', color: '#af52de' },
];

function hasMetricData(data, key) {
  return data.some((d) => d[key] != null);
}

export default function ValuationChart({ data }) {
  if (!data || data.length === 0) {
    return (
      <div className="p-4 text-center text-muted-foreground">
        No valuation data available
      </div>
    );
  }

  const visibleMetrics = METRICS.filter((m) => hasMetricData(data, m.key));

  if (visibleMetrics.length === 0) {
    return (
      <div className="p-4 text-center text-muted-foreground">
        No valuation data available
      </div>
    );
  }

  const chartMargin = { top: 5, right: 20, left: 10, bottom: 5 };

  return (
    <div className="p-4 space-y-6">
      {visibleMetrics.map(({ key, label, color }) => (
        <div key={key}>
          <h4 className="text-sm font-semibold text-foreground mb-2">{label}</h4>
          <ResponsiveContainer width="100%" height={160}>
            <LineChart data={data} margin={chartMargin}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
              <XAxis
                dataKey="fiscal_year"
                tick={{ fontSize: 12, fill: 'hsl(var(--muted-foreground))' }}
              />
              <YAxis
                tick={{ fontSize: 12, fill: 'hsl(var(--muted-foreground))' }}
                tickFormatter={(v) => (v != null ? v.toFixed(1) : '')}
                width={50}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'hsl(var(--card))',
                  border: '1px solid hsl(var(--border))',
                  borderRadius: '8px',
                  color: 'hsl(var(--foreground))',
                }}
                labelFormatter={(yr) => `FY ${yr}`}
                formatter={(value) => [
                  value != null ? value.toFixed(2) : 'N/A',
                  label,
                ]}
              />
              <Line
                type="monotone"
                dataKey={key}
                stroke={color}
                strokeWidth={2}
                dot={{ r: 4, fill: color }}
                activeDot={{ r: 6, fill: color }}
                connectNulls
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      ))}
    </div>
  );
}
