export default function EstimatesBadge({ estimates, currentPrice }) {
  if (!estimates || !estimates.consensus_type) return null;

  const type = estimates.consensus_type.toLowerCase();

  const colorMap = {
    'strong_buy': 'bg-green-100 text-green-800',
    'buy': 'bg-green-100 text-green-700',
    'hold': 'bg-yellow-100 text-yellow-800',
    'sell': 'bg-red-100 text-red-700',
    'strong_sell': 'bg-red-100 text-red-800',
  };

  const labelMap = {
    'strong_buy': 'Strong Buy',
    'buy': 'Buy',
    'hold': 'Hold',
    'sell': 'Sell',
    'strong_sell': 'Strong Sell',
  };

  const color = colorMap[type] || 'bg-gray-100 text-gray-700';
  const label = labelMap[type] || estimates.consensus_type;

  let targetDelta = null;
  if (estimates.target_price && currentPrice && currentPrice > 0) {
    const diff = ((estimates.target_price - currentPrice) / currentPrice * 100).toFixed(0);
    targetDelta = diff >= 0 ? `+${diff}%` : `${diff}%`;
  }

  return (
    <span
      className={`inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded ${color}`}
      title={estimates.target_price ? `Target: $${estimates.target_price.toFixed(2)}` : undefined}
    >
      {label}
      {targetDelta && (
        <span className="opacity-70">({targetDelta})</span>
      )}
    </span>
  );
}
