import { useState, useEffect, useCallback } from 'react';
import { useAISerializable } from '../hooks/useAISerializable';
import SendToAIButton from './SendToAIButton';
import CandlestickChart from './CandlestickChart';
import PerformanceTiles from './PerformanceTiles';
import EstimatesBadge from './EstimatesBadge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import InsiderTrades from './InsiderTrades';
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
  const [insiderData, setInsiderData] = useState(null);
  const [insiderLoading, setInsiderLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('chart');

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

  const fetchInsiderTrades = useCallback(async () => {
    if (insiderData || insiderLoading) return;
    setInsiderLoading(true);
    try {
      const response = await fetch(
        `${API_BASE}/api/securities/${item.symbol}/insider-trades`,
        { credentials: 'include' }
      );
      if (response.ok) {
        const data = await response.json();
        setInsiderData(data);
      }
    } catch (err) {
      console.error(`Error fetching insider trades for ${item.symbol}:`, err);
    } finally {
      setInsiderLoading(false);
    }
  }, [item.symbol, insiderData, insiderLoading]);

  // Show loading state
  if (item.loading) {
    return (
      <div className="bg-card rounded-lg shadow-sm p-4 border border-transparent">
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-foreground">{item.symbol}</h3>
            <p className="text-sm text-muted-foreground mt-1">Loading quote data...</p>
          </div>
          <div className="animate-pulse text-muted-foreground">
            <div className="h-6 w-24 bg-muted rounded-lg mb-1"></div>
            <div className="h-4 w-20 bg-muted rounded-lg"></div>
          </div>
        </div>
      </div>
    );
  }

  // Show error state
  if (item.error) {
    return (
      <div className="bg-card rounded-lg shadow-sm p-4 border border-transparent">
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-foreground">{item.symbol}</h3>
            <p className="text-sm text-destructive mt-1">Failed to load quote data</p>
          </div>
          <button
            onClick={(e) => {
              e.stopPropagation();
              onRemove();
            }}
            className="text-muted-foreground hover:text-destructive transition-colors duration-fast p-2"
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
      className={`bg-card rounded-lg shadow-sm border transition-all duration-fast ${
        isExpanded ? 'border-primary' : 'border-transparent hover:border-border'
      }`}
    >
      {/* Clickable stock bar */}
      <div
        onClick={onToggle}
        className="flex items-center justify-between p-4 cursor-pointer"
      >
        {/* Chevron toggle */}
        <div className="mr-3 text-muted-foreground">
          <svg
            className={`w-5 h-5 transition-transform duration-fast ${isExpanded ? 'rotate-90' : ''}`}
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
            <h3 className="text-lg font-semibold text-foreground">{item.symbol}</h3>
            {ma200 && (
              <span
                className={`inline-flex items-center text-xs px-2 py-0.5 rounded-full font-medium ${
                  isAboveMA
                    ? 'bg-success/10 text-success'
                    : 'bg-warning/10 text-warning'
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
          {item.name && <p className="text-sm text-muted-foreground mt-0.5">{item.name}</p>}
        </div>

        {/* Price and Change */}
        <div className="text-right mr-4">
          <div className="text-xl font-semibold text-foreground font-mono">
            ${price.toFixed(2)}
          </div>
          <div className={`text-sm font-medium font-mono ${isPositive ? 'text-success' : 'text-destructive'}`}>
            {isPositive ? '+' : ''}
            {change.toFixed(2)} ({(changePercent * 100).toFixed(2)}%)
          </div>
        </div>

        {/* Volume */}
        <div className="text-right mr-4 hidden md:block">
          <div className="text-xs text-muted-foreground">Volume</div>
          <div className="text-sm font-medium text-foreground font-mono">
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
            className="text-muted-foreground hover:text-destructive transition-colors duration-fast p-2"
            title="Remove stock"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>

      {/* Additional Info: MA200 + Performance Tiles */}
      {(ma200 || item.performance) && (
        <div className="mx-4 pb-2 pt-0 border-t border-border">
          {ma200 && (
            <div className="text-xs text-muted-foreground mb-1 font-mono">
              200-day MA: ${ma200.toFixed(2)}
            </div>
          )}
          {item.performance && (
            <PerformanceTiles performance={item.performance} compact />
          )}
        </div>
      )}

      {/* Expandable dropdown panel */}
      {isExpanded && (
        <div className="border-t border-border p-4 space-y-4">
          <Tabs value={activeTab} onValueChange={(val) => {
            setActiveTab(val);
            if (val === 'insider' && !insiderData && !insiderLoading) {
              fetchInsiderTrades();
            }
          }}>
            <TabsList>
              <TabsTrigger value="chart">Chart</TabsTrigger>
              <TabsTrigger value="insider">Insider Trades</TabsTrigger>
            </TabsList>

            <TabsContent value="chart" className="mt-4">
              {expandedLoading ? (
                <div className="flex items-center justify-center h-64">
                  <div className="text-muted-foreground">Loading chart data...</div>
                </div>
              ) : (
                <CandlestickChart
                  symbol={item.symbol}
                  ohlcv={expandedData?.ohlcv || []}
                />
              )}
            </TabsContent>

            <TabsContent value="insider" className="mt-4">
              {insiderLoading ? (
                <div className="flex items-center justify-center h-32">
                  <div className="text-muted-foreground">Loading insider trades...</div>
                </div>
              ) : (
                <InsiderTrades data={insiderData} />
              )}
            </TabsContent>
          </Tabs>
        </div>
      )}
    </div>
  );
}
