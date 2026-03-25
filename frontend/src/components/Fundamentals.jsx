function formatLargeNumber(value) {
  if (value == null) return '—';
  const abs = Math.abs(value);
  if (abs >= 1e12) return `$${(value / 1e12).toFixed(2)}T`;
  if (abs >= 1e9) return `$${(value / 1e9).toFixed(2)}B`;
  if (abs >= 1e6) return `$${(value / 1e6).toFixed(1)}M`;
  if (abs >= 1e3) return `$${(value / 1e3).toFixed(0)}K`;
  return `$${value.toFixed(0)}`;
}

function formatPercent(value) {
  if (value == null) return '—';
  return `${(value * 100).toFixed(1)}%`;
}

function formatRatio(value) {
  if (value == null) return '—';
  return value.toFixed(2);
}

function formatEmployees(value) {
  if (value == null) return '—';
  const num = typeof value === 'string' ? parseInt(value, 10) : value;
  if (isNaN(num)) return '—';
  return num.toLocaleString();
}

function MetricCard({ label, value }) {
  return (
    <div className="bg-muted/50 rounded-lg px-3 py-2.5">
      <div className="text-xs text-muted-foreground mb-0.5">{label}</div>
      <div className="text-sm font-mono text-foreground font-medium">{value}</div>
    </div>
  );
}

export default function Fundamentals({ data }) {
  if (!data) {
    return (
      <div className="flex items-center justify-center py-12 text-sm text-muted-foreground">
        No fundamentals data available
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Company header */}
      <div className="bg-card rounded-lg p-4">
        {data.description && (
          <p className="text-sm text-muted-foreground leading-relaxed line-clamp-3 mb-3">
            {data.description}
          </p>
        )}
        <div className="flex items-center gap-2 text-xs text-muted-foreground flex-wrap">
          {data.sector && (
            <span className="bg-muted/50 rounded px-2 py-0.5 font-medium">{data.sector}</span>
          )}
          {data.industry && (
            <span className="bg-muted/50 rounded px-2 py-0.5">{data.industry}</span>
          )}
          {data.employees && (
            <span>{formatEmployees(data.employees)} employees</span>
          )}
          {data.ceo && (
            <span>CEO: {data.ceo}</span>
          )}
          {data.website && (
            <a
              href={data.website}
              target="_blank"
              rel="noopener noreferrer"
              className="text-primary hover:underline"
            >
              {data.website.replace(/^https?:\/\/(www\.)?/, '')}
            </a>
          )}
        </div>
      </div>

      {/* Metrics grid */}
      <div className="grid grid-cols-3 sm:grid-cols-4 gap-2">
        <MetricCard label="Market Cap" value={formatLargeNumber(data.market_cap)} />
        <MetricCard label="Enterprise Value" value={formatLargeNumber(data.enterprise_value)} />
        <MetricCard label="P/E Ratio" value={formatRatio(data.pe_ratio)} />
        <MetricCard label="EV/EBITDA" value={formatRatio(data.ev_to_ebitda)} />
        <MetricCard label="EV/Sales" value={formatRatio(data.ev_to_sales)} />
        <MetricCard label="ROE" value={formatPercent(data.roe)} />
        <MetricCard label="ROA" value={formatPercent(data.roa)} />
        <MetricCard label="ROIC" value={formatPercent(data.roic)} />
        <MetricCard label="Current Ratio" value={formatRatio(data.current_ratio)} />
        <MetricCard label="FCF Yield" value={formatPercent(data.free_cash_flow_yield)} />
        <MetricCard label="Beta" value={formatRatio(data.beta)} />
        <MetricCard label="52W Range" value={data['52w_range'] || '—'} />
      </div>
    </div>
  );
}
