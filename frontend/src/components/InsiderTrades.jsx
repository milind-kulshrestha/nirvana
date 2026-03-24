import { Badge } from './ui/badge';

function formatValue(value) {
  if (value == null) return '—';
  const abs = Math.abs(value);
  if (abs >= 1_000_000) return `$${(value / 1_000_000).toFixed(1)}M`;
  if (abs >= 1_000) return `$${(value / 1_000).toFixed(0)}K`;
  return `$${value.toFixed(0)}`;
}

function formatShares(shares) {
  if (shares == null) return '—';
  if (shares >= 1_000_000) return `${(shares / 1_000_000).toFixed(1)}M`;
  if (shares >= 1_000) return `${(shares / 1_000).toFixed(1)}K`;
  return shares.toLocaleString();
}

export default function InsiderTrades({ data }) {
  if (!data) return null;

  const { summary, trades } = data;

  const totalTrades = summary.total_buys + summary.total_sells;
  const buyPct = totalTrades > 0 ? (summary.total_buys / totalTrades) * 100 : 0;

  return (
    <div className="space-y-4">
      {/* Summary bar */}
      <div className="bg-card rounded-lg p-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs text-muted-foreground font-medium uppercase tracking-wide">
            Last 3 months
          </span>
          {totalTrades === 0 && (
            <span className="text-sm text-muted-foreground">No insider trades</span>
          )}
        </div>

        {totalTrades > 0 && (
          <>
            {/* Stacked bar */}
            <div className="h-3 rounded-full overflow-hidden flex bg-muted mb-3">
              {buyPct > 0 && (
                <div
                  className="bg-success transition-all"
                  style={{ width: `${buyPct}%` }}
                />
              )}
              {buyPct < 100 && (
                <div
                  className="bg-destructive transition-all"
                  style={{ width: `${100 - buyPct}%` }}
                />
              )}
            </div>

            {/* Stats text */}
            <div className="flex items-center gap-2 text-sm flex-wrap">
              <span className="text-success font-medium">
                {summary.total_buys} {summary.total_buys === 1 ? 'buy' : 'buys'} ({formatValue(summary.buy_value)})
              </span>
              <span className="text-muted-foreground">·</span>
              <span className="text-destructive font-medium">
                {summary.total_sells} {summary.total_sells === 1 ? 'sell' : 'sells'} ({formatValue(summary.sell_value)})
              </span>
              <span className="text-muted-foreground">·</span>
              <span className={`font-medium ${summary.net_value >= 0 ? 'text-success' : 'text-destructive'}`}>
                Net: {summary.net_value >= 0 ? '+' : ''}{formatValue(summary.net_value)}
              </span>
            </div>
          </>
        )}
      </div>

      {/* Trade table */}
      {trades.length > 0 && (
        <div className="bg-card rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border text-left text-xs text-muted-foreground uppercase tracking-wide">
                <th className="px-4 py-2">Date</th>
                <th className="px-4 py-2">Insider</th>
                <th className="px-4 py-2 hidden md:table-cell">Title</th>
                <th className="px-4 py-2">Type</th>
                <th className="px-4 py-2 text-right">Shares</th>
                <th className="px-4 py-2 text-right">Value</th>
              </tr>
            </thead>
            <tbody>
              {trades.map((trade, i) => (
                <tr key={i} className="border-b border-border last:border-0 hover:bg-muted/50">
                  <td className="px-4 py-2 font-mono text-xs">{trade.date || '—'}</td>
                  <td className="px-4 py-2 truncate max-w-[150px]" title={trade.insider_name}>
                    {trade.insider_name || '—'}
                  </td>
                  <td className="px-4 py-2 truncate max-w-[120px] hidden md:table-cell text-muted-foreground" title={trade.insider_title}>
                    {trade.insider_title || '—'}
                  </td>
                  <td className="px-4 py-2">
                    <Badge
                      variant={trade.transaction_type === 'buy' ? 'default' : 'destructive'}
                      className={`text-xs ${
                        trade.transaction_type === 'buy'
                          ? 'bg-success/15 text-success hover:bg-success/25 border-0'
                          : 'bg-destructive/15 text-destructive hover:bg-destructive/25 border-0'
                      }`}
                    >
                      {trade.transaction_type === 'buy' ? 'Buy' : 'Sell'}
                    </Badge>
                  </td>
                  <td className="px-4 py-2 text-right font-mono">{formatShares(trade.shares)}</td>
                  <td className="px-4 py-2 text-right font-mono">{formatValue(trade.value)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
