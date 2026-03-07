import { useState, useEffect, useRef, useCallback } from 'react';
import { createChart, CandlestickSeries, LineSeries, AreaSeries, HistogramSeries } from 'lightweight-charts';
import { useAISerializable } from '../hooks/useAISerializable';
import SendToAIButton from './SendToAIButton';

const CHART_TYPES = [
  { key: 'candlestick', label: 'Candles' },
  { key: 'line', label: 'Line' },
  { key: 'area', label: 'Area' },
];

export default function CandlestickChart({ symbol, ohlcv }) {
  const chartContainerRef = useRef(null);
  const chartRef = useRef(null);
  const [chartType, setChartType] = useState('candlestick');

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

    const candleData = ohlcv
      .filter((d) => d.open != null && d.high != null && d.low != null)
      .map((d) => ({
        time: d.date,
        open: d.open,
        high: d.high,
        low: d.low,
        close: d.close,
      }));

    const lineData = ohlcv.map((d) => ({
      time: d.date,
      value: d.close,
    }));

    // Add price series based on chart type
    if (chartType === 'candlestick') {
      const series = chart.addSeries(CandlestickSeries, {
        upColor: '#10b981',
        downColor: '#ef4444',
        borderUpColor: '#10b981',
        borderDownColor: '#ef4444',
        wickUpColor: '#10b981',
        wickDownColor: '#ef4444',
      });
      series.setData(candleData);
    } else if (chartType === 'line') {
      const series = chart.addSeries(LineSeries, {
        color: '#6366f1',
        lineWidth: 2,
      });
      series.setData(lineData);
    } else if (chartType === 'area') {
      const series = chart.addSeries(AreaSeries, {
        topColor: 'rgba(99, 102, 241, 0.4)',
        bottomColor: 'rgba(99, 102, 241, 0.05)',
        lineColor: '#6366f1',
        lineWidth: 2,
      });
      series.setData(lineData);
    }

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
  }, [ohlcv, chartType]);

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

  return (
    <div ref={aiRef} className="bg-white rounded-lg p-6">
      <div className="mb-4 flex items-start justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">{symbol}</h3>
          <p className="text-sm text-gray-500">1-Year OHLCV</p>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex gap-0.5 bg-gray-100 rounded-md p-0.5">
            {CHART_TYPES.map((t) => (
              <button
                key={t.key}
                onClick={() => setChartType(t.key)}
                className={`px-2.5 py-1 rounded text-xs font-medium transition ${
                  chartType === t.key
                    ? 'bg-white shadow-sm text-gray-900'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>
          <SendToAIButton componentId={`chart-${symbol}`} label={`Ask AI about ${symbol} chart`} />
        </div>
      </div>

      <div ref={chartContainerRef} />

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
