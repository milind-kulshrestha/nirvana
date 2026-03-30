export default function EstimatesBadge({ estimates, currentPrice }) {
  if (!estimates || !estimates.consensus_type) return null;

  const type = estimates.consensus_type.toLowerCase();

  const colorMap = {
    'strong_buy': 'bg-success/15 text-success',
    'buy': 'bg-success/10 text-success',
    'hold': 'bg-warning/10 text-warning',
    'sell': 'bg-destructive/10 text-destructive',
    'strong_sell': 'bg-destructive/15 text-destructive',
  };

  const labelMap = {
    'strong_buy': 'Strong Buy',
    'buy': 'Buy',
    'hold': 'Hold',
    'sell': 'Sell',
    'strong_sell': 'Strong Sell',
  };

  const color = colorMap[type] || 'bg-muted text-muted-foreground';
  const label = labelMap[type] || estimates.consensus_type;

  let targetDelta = null;
  if (estimates.target_price && currentPrice && currentPrice > 0) {
    const diff = ((estimates.target_price - currentPrice) / currentPrice * 100).toFixed(0);
    targetDelta = diff >= 0 ? `+${diff}%` : `${diff}%`;
  }

  return (
    <span
      className={`inline-flex items-center gap-1 text-xs font-medium px-2.5 py-0.5 rounded-full ${color}`}
      title={estimates.target_price ? `Target: $${estimates.target_price.toFixed(2)}` : undefined}
    >
      {label}
      {targetDelta && (
        <span className="opacity-70 font-mono">({targetDelta})</span>
      )}
    </span>
  );
}
