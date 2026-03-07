import { useState, useEffect, useCallback } from 'react';
import { useAISerializable } from '../hooks/useAISerializable';
import SendToAIButton from './SendToAIButton';
import CandlestickChart from './CandlestickChart';
import PerformanceTiles from './PerformanceTiles';
import EstimatesBadge from './EstimatesBadge';
import { API_BASE } from '../config';

export default function StockRow({ item, onRemove, onToggle, isExpanded }) {
  const quote = item.quote || {};
  const ma200 = item.ma_200;
  const price = quote.price || 0;
  const change = quote.change || 0;
  const changePercent = quote.change_percent || 0;
  const isPositive = change >= 0;
  const isAboveMA = ma200 && price > ma200;

  const [expandedData, setExpandedData] = useState(null);
  const [expandedLoading, setExpandedLoading] = useState(false);

  const serializeFn = useCallback(() => ({
    type: 'stock-quote',
    symbol: item.symbol,
    price,
    change,
    changePercent,
    volume: quote.volume || null,
    ma200: ma200 || null,
    isAboveMA: Boolean(isAboveMA),
  }), [item.symbol, price, change, changePercent, quote.volume, ma200, isAboveMA]);

  const ref = useAISerializable(`stock-${item.symbol}`, serializeFn);

  // Fetch OHLCV + performance + estimates when expanded
  useEffect(() => {
    if (!isExpanded || expandedData) return;

    const fetchExpandedData = async () => {
      setExpandedLoading(true);
      try {
        const response = await fetch(
          `${API_BASE}/api/securities/${item.symbol}?include=ohlcv,performance,estimates`,
          { credentials: 'include' }
        );
        if (response.ok) {
          const data = await response.json();
          setExpandedData(data);
        }
      } catch (err) {
        console.error(`Error fetching expanded data for ${item.symbol}:`, err);
      } finally {
        setExpandedLoading(false);
      }
    };

    fetchExpandedData();
  }, [isExpanded, item.symbol, expandedData]);

  // Show loading state
  if (item.loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-4 border-2 border-transparent">
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <h3 className="text-lg font-bold text-gray-900">{item.symbol}</h3>
            <p className="text-sm text-gray-500 mt-1">Loading quote data...</p>
          </div>
          <div className="animate-pulse text-gray-400">
            <div className="h-6 w-24 bg-gray-200 rounded mb-1"></div>
            <div className="h-4 w-20 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  // Show error state
  if (item.error) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-4 border-2 border-transparent">
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <h3 className="text-lg font-bold text-gray-900">{item.symbol}</h3>
            <p className="text-sm text-red-600 mt-1">Failed to load quote data</p>
          </div>
          <button
            onClick={(e) => {
              e.stopPropagation();
              onRemove();
            }}
            className="text-gray-400 hover:text-red-600 transition p-2"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>
    );
  }

  return (
    <div
      ref={ref}
      className={`bg-white rounded-lg shadow-sm border-2 transition ${
        isExpanded ? 'border-indigo-500' : 'border-transparent hover:border-gray-200'
      }`}
    >
      {/* Clickable stock bar */}
      <div
        onClick={onToggle}
        className="flex items-center justify-between p-4 cursor-pointer"
      >
        {/* Chevron toggle */}
        <div className="mr-3 text-gray-400">
          <svg
            className={`w-5 h-5 transition-transform duration-200 ${isExpanded ? 'rotate-90' : ''}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </div>

        {/* Symbol and Name */}
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <h3 className="text-lg font-bold text-gray-900">{item.symbol}</h3>
            {ma200 && (
              <span
                className={`text-xs px-2 py-0.5 rounded ${
                  isAboveMA
                    ? 'bg-green-100 text-green-700'
                    : 'bg-orange-100 text-orange-700'
                }`}
                title={`200-day MA: $${ma200.toFixed(2)}`}
              >
                {isAboveMA ? '↑ Above' : '↓ Below'} MA200
              </span>
            )}
            {item.estimates && (
              <EstimatesBadge estimates={item.estimates} currentPrice={price} />
            )}
          </div>
          {item.name && <p className="text-sm text-gray-500 mt-0.5">{item.name}</p>}
        </div>

        {/* Price and Change */}
        <div className="text-right mr-4">
          <div className="text-xl font-bold text-gray-900">
            ${price.toFixed(2)}
          </div>
          <div className={`text-sm font-medium ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
            {isPositive ? '+' : ''}
            {change.toFixed(2)} ({(changePercent * 100).toFixed(2)}%)
          </div>
        </div>

        {/* Volume */}
        <div className="text-right mr-4 hidden md:block">
          <div className="text-xs text-gray-500">Volume</div>
          <div className="text-sm font-medium text-gray-700">
            {quote.volume ? (quote.volume / 1000000).toFixed(1) + 'M' : 'N/A'}
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-1">
          <SendToAIButton componentId={`stock-${item.symbol}`} label={`Ask AI about ${item.symbol}`} />
          <button
            onClick={(e) => {
              e.stopPropagation();
              onRemove();
            }}
            className="text-gray-400 hover:text-red-600 transition p-2"
            title="Remove stock"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>

      {/* Additional Info */}
      {ma200 && (
        <div className="mx-4 pb-2 pt-0 border-t border-gray-100 text-xs text-gray-500">
          200-day MA: ${ma200.toFixed(2)}
        </div>
      )}

      {/* Expandable dropdown panel */}
      {isExpanded && (
        <div className="border-t border-gray-200 p-4 space-y-4">
          {expandedLoading ? (
            <div className="flex items-center justify-center h-64">
              <div className="text-gray-500">Loading chart data...</div>
            </div>
          ) : (
            <>
              <CandlestickChart
                symbol={item.symbol}
                ohlcv={expandedData?.ohlcv || []}
              />
              <PerformanceTiles performance={expandedData?.performance} />
            </>
          )}
        </div>
      )}
    </div>
  );
}
