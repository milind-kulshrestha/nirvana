export default function PerformanceTiles({ performance, compact = false }) {
  if (!performance) return null;

  const periods = [
    { key: 'one_day_return', label: '1D' },
    { key: 'one_week_return', label: '1W' },
    { key: 'one_month_return', label: '1M' },
    { key: 'three_month_return', label: '3M' },
    { key: 'six_month_return', label: '6M' },
    { key: 'ytd_return', label: 'YTD' },
    { key: 'one_year_return', label: '1Y' },
  ];

  const activePeriods = periods.filter((p) => performance[p.key] != null);

  if (activePeriods.length === 0) return null;

  const formatReturn = (value) => {
    const pct = (value * 100).toFixed(1);
    return value >= 0 ? `+${pct}%` : `${pct}%`;
  };

  const getColor = (value) => {
    if (value == null) return 'bg-muted text-muted-foreground';
    if (value > 0.05) return 'bg-success/15 text-success';
    if (value > 0) return 'bg-success/10 text-success';
    if (value > -0.05) return 'bg-destructive/10 text-destructive';
    return 'bg-destructive/15 text-destructive';
  };

  if (compact) {
    return (
      <div className="flex flex-wrap gap-1.5 mt-1">
        {activePeriods.map(({ key, label }) => {
          const value = performance[key];
          return (
            <span
              key={key}
              className={`inline-flex items-center gap-1 text-[11px] px-1.5 py-0.5 rounded-full ${getColor(value)}`}
            >
              <span className="font-medium opacity-70">{label}</span>
              <span className="font-semibold font-mono">{formatReturn(value)}</span>
            </span>
          );
        })}
      </div>
    );
  }

  return (
    <div>
      <h4 className="text-sm font-medium text-muted-foreground mb-2">Performance</h4>
      <div className="flex flex-wrap gap-2">
        {activePeriods.map(({ key, label }) => {
          const value = performance[key];
          return (
            <div
              key={key}
              className={`px-3 py-1.5 rounded-lg text-center min-w-[60px] ${getColor(value)}`}
            >
              <div className="text-[10px] font-medium opacity-70">{label}</div>
              <div className="text-sm font-semibold font-mono">{formatReturn(value)}</div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
