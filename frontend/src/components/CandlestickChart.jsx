import { useEffect, useRef, useCallback } from 'react';
import { createChart, CandlestickSeries, HistogramSeries } from 'lightweight-charts';
import { useAISerializable } from '../hooks/useAISerializable';
import SendToAIButton from './SendToAIButton';

export default function CandlestickChart({ symbol, ohlcv }) {
  const chartContainerRef = useRef(null);
  const chartRef = useRef(null);

  const serializeFn = useCallback(() => {
    if (!ohlcv || ohlcv.length === 0) return { type: 'candlestick-chart', symbol, dataPoints: 0 };
    const closes = ohlcv.map((d) => d.close);
    return {
      type: 'candlestick-chart',
      symbol,
      dataPoints: ohlcv.length,
      dateRange: { start: ohlcv[0]?.date, end: ohlcv[ohlcv.length - 1]?.date },
      priceRange: { min: Math.min(...closes), max: Math.max(...closes) },
      startPrice: ohlcv[0]?.close,
      endPrice: ohlcv[ohlcv.length - 1]?.close,
      changePercent: ohlcv[0]?.close
        ? (((ohlcv[ohlcv.length - 1]?.close - ohlcv[0]?.close) / ohlcv[0]?.close) * 100).toFixed(2)
        : null,
    };
  }, [symbol, ohlcv]);

  const aiRef = useAISerializable(`chart-${symbol}`, serializeFn);

  useEffect(() => {
    if (!chartContainerRef.current || !ohlcv || ohlcv.length === 0) return;

    const container = chartContainerRef.current;

    const chart = createChart(container, {
      width: container.clientWidth,
      height: 320,
      layout: {
        background: { color: '#ffffff' },
        textColor: '#6b7280',
        fontSize: 12,
      },
      grid: {
        vertLines: { color: '#f3f4f6' },
        horzLines: { color: '#f3f4f6' },
      },
      crosshair: {
        mode: 0,
      },
      rightPriceScale: {
        borderColor: '#e5e7eb',
      },
      timeScale: {
        borderColor: '#e5e7eb',
        timeVisible: false,
      },
    });

    chartRef.current = chart;

    // Candlestick series
    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: '#10b981',
      downColor: '#ef4444',
      borderUpColor: '#10b981',
      borderDownColor: '#ef4444',
      wickUpColor: '#10b981',
      wickDownColor: '#ef4444',
    });

    const candleData = ohlcv
      .filter((d) => d.open != null && d.high != null && d.low != null)
      .map((d) => ({
        time: d.date,
        open: d.open,
        high: d.high,
        low: d.low,
        close: d.close,
      }));

    candleSeries.setData(candleData);

    // Volume histogram series
    const volumeSeries = chart.addSeries(HistogramSeries, {
      priceFormat: { type: 'volume' },
      priceScaleId: 'volume',
    });

    chart.priceScale('volume').applyOptions({
      scaleMargins: { top: 0.8, bottom: 0 },
    });

    const volumeData = ohlcv
      .filter((d) => d.volume != null)
      .map((d) => ({
        time: d.date,
        value: d.volume,
        color: d.close >= d.open ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)',
      }));

    volumeSeries.setData(volumeData);

    chart.timeScale().fitContent();

    // Handle resize
    const handleResize = () => {
      if (chartContainerRef.current) {
        chart.applyOptions({ width: chartContainerRef.current.clientWidth });
      }
    };
    const resizeObserver = new ResizeObserver(handleResize);
    resizeObserver.observe(container);

    return () => {
      resizeObserver.disconnect();
      chart.remove();
      chartRef.current = null;
    };
  }, [ohlcv]);

  if (!ohlcv || ohlcv.length === 0) {
    return (
      <div className="bg-white rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">{symbol} Chart</h3>
        <div className="flex items-center justify-center h-64">
          <div className="text-gray-500">No chart data available</div>
        </div>
      </div>
    );
  }

  const firstPrice = ohlcv[0]?.close || 0;
  const lastPrice = ohlcv[ohlcv.length - 1]?.close || 0;
  const isPositive = lastPrice >= firstPrice;

  return (
    <div ref={aiRef} className="bg-white rounded-lg p-6">
      <div className="mb-4 flex items-start justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">{symbol}</h3>
          <p className="text-sm text-gray-500">1-Year OHLCV</p>
        </div>
        <SendToAIButton componentId={`chart-${symbol}`} label={`Ask AI about ${symbol} chart`} />
      </div>

      <div ref={chartContainerRef} />

      <div className="mt-4 pt-4 border-t border-gray-100">
        <div className="flex justify-between text-sm">
          <div>
            <div className="text-gray-500">Start</div>
            <div className="font-semibold">${firstPrice.toFixed(2)}</div>
          </div>
          <div className="text-right">
            <div className="text-gray-500">Current</div>
            <div className={`font-semibold ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
              ${lastPrice.toFixed(2)} ({isPositive ? '+' : ''}
              {((lastPrice - firstPrice) / firstPrice * 100).toFixed(2)}%)
            </div>
          </div>
        </div>
      </div>

      <div className="mt-2 text-right">
        <a
          href="https://www.tradingview.com/"
          target="_blank"
          rel="noopener noreferrer"
          className="text-[10px] text-gray-400 hover:text-gray-500"
        >
          Charting by TradingView
        </a>
      </div>
    </div>
  );
}
