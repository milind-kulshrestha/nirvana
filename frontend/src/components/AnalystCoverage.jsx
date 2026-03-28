import { Badge } from './ui/badge';

function formatRevenue(value) {
  if (value == null) return '—';
  const abs = Math.abs(value);
  if (abs >= 1_000_000_000) return `$${(value / 1_000_000_000).toFixed(1)}B`;
  if (abs >= 1_000_000) return `$${(value / 1_000_000).toFixed(0)}M`;
  return `$${value.toLocaleString()}`;
}

function formatPrice(value) {
  if (value == null) return '—';
  return `$${value.toFixed(2)}`;
}

function consensusColor(type) {
  if (!type) return 'text-muted-foreground';
  const t = type.toLowerCase();
  if (t.includes('strong buy') || t.includes('buy')) return 'text-success';
  if (t.includes('hold')) return 'text-warning';
  if (t.includes('sell')) return 'text-destructive';
  return 'text-muted-foreground';
}

function consensusBgColor(type) {
  if (!type) return 'bg-muted/50';
  const t = type.toLowerCase();
  if (t.includes('strong buy') || t.includes('buy')) return 'bg-success/15';
  if (t.includes('hold')) return 'bg-warning/15';
  if (t.includes('sell')) return 'bg-destructive/15';
  return 'bg-muted/50';
}

function fiscalYear(dateStr) {
  if (!dateStr) return '—';
  return `FY${dateStr.slice(0, 4)}`;
}

export default function AnalystCoverage({ data, currentPrice }) {
  if (!data) {
    return (
      <div className="flex items-center justify-center py-12 text-muted-foreground text-sm">
        No analyst data available
      </div>
    );
  }

  const { consensus, price_targets, forward_estimates } = data;

  const hasConsensus = consensus && (consensus.consensus_type || consensus.consensus_rating || consensus.target_price);
  const hasPriceTargets = price_targets && (price_targets.last_year_count > 0 || price_targets.all_time_count > 0);
  const hasForward = forward_estimates && forward_estimates.length > 0;

  if (!hasConsensus && !hasPriceTargets && !hasForward) {
    return (
      <div className="flex items-center justify-center py-12 text-muted-foreground text-sm">
        No analyst data available
      </div>
    );
  }

  // Calculate upside/downside from last year avg target
  const targetPrice = price_targets?.last_year_avg ?? consensus?.target_price;
  const upside = targetPrice && currentPrice ? ((targetPrice - currentPrice) / currentPrice) * 100 : null;

  return (
    <div className="space-y-4">
      {/* Consensus + Price Target row */}
      {(hasConsensus || hasPriceTargets) && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {/* Consensus */}
          <div className="bg-card rounded-lg p-4">
            <span className="text-xs text-muted-foreground font-medium uppercase tracking-wide">
              Consensus Rating
            </span>
            {hasConsensus ? (
              <div className="mt-2 flex items-center gap-3">
                <Badge
                  className={`text-sm px-3 py-1 border-0 ${consensusBgColor(consensus.consensus_type)} ${consensusColor(consensus.consensus_type)}`}
                >
                  {consensus.consensus_type || 'N/A'}
                </Badge>
                {consensus.consensus_rating != null && (
                  <span className="text-sm text-muted-foreground font-mono">
                    {consensus.consensus_rating.toFixed(1)}/5
                  </span>
                )}
              </div>
            ) : (
              <div className="mt-2 text-sm text-muted-foreground">—</div>
            )}
          </div>

          {/* Price Target */}
          <div className="bg-card rounded-lg p-4">
            <span className="text-xs text-muted-foreground font-medium uppercase tracking-wide">
              Avg Price Target (1Y)
            </span>
            <div className="mt-2 flex items-center gap-3">
              <span className="text-lg font-semibold font-mono text-foreground">
                {formatPrice(targetPrice)}
              </span>
              {upside != null && (
                <span className={`text-sm font-medium ${upside >= 0 ? 'text-success' : 'text-destructive'}`}>
                  {upside >= 0 ? '+' : ''}{upside.toFixed(1)}%
                </span>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Price target activity */}
      {hasPriceTargets && (
        <div className="bg-card rounded-lg px-4 py-3">
          <div className="flex items-center gap-4 text-sm flex-wrap">
            <span className="text-xs text-muted-foreground font-medium uppercase tracking-wide mr-1">
              Target Activity
            </span>
            {price_targets.last_month_count > 0 && (
              <span className="text-muted-foreground">
                <span className="font-medium text-foreground">{price_targets.last_month_count}</span> last month
                {price_targets.last_month_avg != null && (
                  <span className="text-muted-foreground"> (avg {formatPrice(price_targets.last_month_avg)})</span>
                )}
              </span>
            )}
            {price_targets.last_quarter_count > 0 && (
              <>
                <span className="text-muted-foreground">·</span>
                <span className="text-muted-foreground">
                  <span className="font-medium text-foreground">{price_targets.last_quarter_count}</span> last quarter
                  {price_targets.last_quarter_avg != null && (
                    <span className="text-muted-foreground"> (avg {formatPrice(price_targets.last_quarter_avg)})</span>
                  )}
                </span>
              </>
            )}
            {price_targets.last_year_count > 0 && (
              <>
                <span className="text-muted-foreground">·</span>
                <span className="text-muted-foreground">
                  <span className="font-medium text-foreground">{price_targets.last_year_count}</span> last year
                </span>
              </>
            )}
          </div>
        </div>
      )}

      {/* Forward Estimates Table */}
      {hasForward && (
        <div className="bg-card rounded-lg overflow-hidden">
          <div className="px-4 py-2 border-b border-border">
            <span className="text-xs text-muted-foreground font-medium uppercase tracking-wide">
              Forward Estimates
            </span>
          </div>
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border text-left text-xs text-muted-foreground uppercase tracking-wide">
                <th className="px-4 py-2">Year</th>
                <th className="px-4 py-2 text-right">Revenue</th>
                <th className="px-4 py-2 text-right">EPS Avg</th>
                <th className="px-4 py-2 text-right hidden md:table-cell">EPS Range</th>
                <th className="px-4 py-2 text-right hidden md:table-cell">Analysts</th>
              </tr>
            </thead>
            <tbody>
              {forward_estimates
                .slice()
                .sort((a, b) => (a.date || '').localeCompare(b.date || ''))
                .map((est, i) => (
                  <tr key={i} className="border-b border-border last:border-0 hover:bg-muted/50">
                    <td className="px-4 py-2 font-medium">{fiscalYear(est.date)}</td>
                    <td className="px-4 py-2 text-right font-mono">{formatRevenue(est.revenue_avg)}</td>
                    <td className="px-4 py-2 text-right font-mono">
                      {est.eps_avg != null ? `$${est.eps_avg.toFixed(2)}` : '—'}
                    </td>
                    <td className="px-4 py-2 text-right font-mono text-muted-foreground hidden md:table-cell">
                      {est.eps_low != null && est.eps_high != null
                        ? `$${est.eps_low.toFixed(2)} – $${est.eps_high.toFixed(2)}`
                        : '—'}
                    </td>
                    <td className="px-4 py-2 text-right font-mono text-muted-foreground hidden md:table-cell">
                      {est.num_analysts_eps ?? est.num_analysts_revenue ?? '—'}
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
