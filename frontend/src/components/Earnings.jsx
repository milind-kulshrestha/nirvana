import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';

function formatLargeNumber(value) {
  if (value == null) return '—';
  const abs = Math.abs(value);
  if (abs >= 1e12) return `$${(value / 1e12).toFixed(2)}T`;
  if (abs >= 1e9) return `$${(value / 1e9).toFixed(2)}B`;
  if (abs >= 1e6) return `$${(value / 1e6).toFixed(1)}M`;
  if (abs >= 1e3) return `$${(value / 1e3).toFixed(0)}K`;
  return `$${value.toFixed(0)}`;
}

function formatDollar(value) {
  if (value == null) return '—';
  return `$${value.toFixed(2)}`;
}

function formatQuarterLabel(item) {
  // e.g. "Q1 2025"
  const period = item.period || '';
  const year = item.fiscal_year || '';
  if (period && year) return `${period} ${year}`;
  if (item.date) return item.date.slice(0, 7);
  return '—';
}

function yearFromDate(dateStr) {
  if (!dateStr) return '—';
  return dateStr.slice(0, 4);
}

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload || !payload.length) return null;
  const data = payload[0].payload;
  return (
    <div
      className="rounded-lg px-3 py-2 text-xs shadow-lg border"
      style={{
        backgroundColor: 'hsl(var(--card))',
        borderColor: 'hsl(var(--border))',
        color: 'hsl(var(--foreground))',
      }}
    >
      <div className="font-medium mb-1">{label}</div>
      <div>EPS: {formatDollar(data.eps_diluted ?? data.eps)}</div>
      <div>Revenue: {formatLargeNumber(data.revenue)}</div>
      <div>Net Income: {formatLargeNumber(data.net_income)}</div>
    </div>
  );
}

export default function Earnings({ data }) {
  if (!data || (!data.quarterly?.length && !data.forward?.length)) {
    return (
      <div className="flex items-center justify-center py-12 text-sm text-muted-foreground">
        No earnings data available
      </div>
    );
  }

  // Reverse quarterly so oldest is first (left-to-right chronological)
  const chartData = [...(data.quarterly || [])]
    .reverse()
    .map((item) => ({
      ...item,
      label: formatQuarterLabel(item),
      epsValue: item.eps_diluted ?? item.eps ?? 0,
    }));

  return (
    <div className="space-y-4">
      {/* EPS Bar Chart */}
      {chartData.length > 0 && (
        <div className="bg-card rounded-lg p-4">
          <h3 className="text-xs text-muted-foreground font-medium uppercase tracking-wide mb-3">
            Quarterly EPS
          </h3>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={chartData} margin={{ top: 5, right: 10, left: 10, bottom: 5 }}>
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="hsl(var(--border))"
                vertical={false}
              />
              <XAxis
                dataKey="label"
                tick={{ fontSize: 11, fill: 'hsl(var(--muted-foreground))' }}
                axisLine={{ stroke: 'hsl(var(--border))' }}
                tickLine={false}
              />
              <YAxis
                tick={{ fontSize: 11, fill: 'hsl(var(--muted-foreground))' }}
                axisLine={false}
                tickLine={false}
                tickFormatter={(v) => `$${v.toFixed(2)}`}
              />
              <Tooltip content={<CustomTooltip />} cursor={{ fill: 'hsl(var(--muted) / 0.5)' }} />
              <Bar dataKey="epsValue" radius={[4, 4, 0, 0]} maxBarSize={48}>
                {chartData.map((entry, index) => (
                  <Cell
                    key={index}
                    fill={
                      entry.epsValue >= 0
                        ? 'hsl(var(--success))'
                        : 'hsl(var(--destructive))'
                    }
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Forward Estimates Table */}
      {data.forward?.length > 0 && (
        <div className="bg-card rounded-lg overflow-hidden">
          <div className="px-4 py-2 border-b border-border">
            <h3 className="text-xs text-muted-foreground font-medium uppercase tracking-wide">
              Forward Estimates
            </h3>
          </div>
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border text-left text-xs text-muted-foreground uppercase tracking-wide">
                <th className="px-4 py-2">Year</th>
                <th className="px-4 py-2 text-right">Revenue</th>
                <th className="px-4 py-2 text-right">EPS</th>
                <th className="px-4 py-2 text-right hidden sm:table-cell">EBITDA</th>
              </tr>
            </thead>
            <tbody>
              {data.forward.map((est, i) => (
                <tr key={i} className="border-b border-border last:border-0 hover:bg-muted/50">
                  <td className="px-4 py-2 font-mono text-xs">{yearFromDate(est.date)}</td>
                  <td className="px-4 py-2 text-right font-mono">
                    {formatLargeNumber(est.revenue_avg)}
                  </td>
                  <td className="px-4 py-2 text-right font-mono">
                    <span>{formatDollar(est.eps_avg)}</span>
                    {est.eps_low != null && est.eps_high != null && (
                      <span className="text-muted-foreground text-xs ml-1">
                        ({formatDollar(est.eps_low)} - {formatDollar(est.eps_high)})
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-2 text-right font-mono hidden sm:table-cell">
                    {formatLargeNumber(est.ebitda_avg)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
