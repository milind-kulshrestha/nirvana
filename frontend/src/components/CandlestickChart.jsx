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
        background: { color: 'transparent' },
        textColor: '#7a7a7a',
        fontSize: 12,
      },
      grid: {
        vertLines: { color: '#e8e8e8' },
        horzLines: { color: '#e8e8e8' },
      },
      crosshair: {
        mode: 0,
      },
      rightPriceScale: {
        borderColor: '#e8e8e8',
      },
      timeScale: {
        borderColor: '#e8e8e8',
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
        upColor: '#34c759',
        downColor: '#ff3b30',
        borderUpColor: '#34c759',
        borderDownColor: '#ff3b30',
        wickUpColor: '#34c759',
        wickDownColor: '#ff3b30',
      });
      series.setData(candleData);
    } else if (chartType === 'line') {
      const series = chart.addSeries(LineSeries, {
        color: '#0071e3',
        lineWidth: 2,
      });
      series.setData(lineData);
    } else if (chartType === 'area') {
      const series = chart.addSeries(AreaSeries, {
        topColor: 'rgba(0, 113, 227, 0.3)',
        bottomColor: 'rgba(0, 113, 227, 0.05)',
        lineColor: '#0071e3',
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
        color: d.close >= d.open ? 'rgba(52, 199, 89, 0.3)' : 'rgba(255, 59, 48, 0.3)',
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
      <div className="bg-card rounded-lg p-4">
        <h3 className="text-lg font-semibold text-foreground mb-4">{symbol} Chart</h3>
        <div className="flex items-center justify-center h-64">
          <div className="text-muted-foreground">No chart data available</div>
        </div>
      </div>
    );
  }

  return (
    <div ref={aiRef} className="bg-card rounded-lg p-4">
      <div className="mb-4 flex items-start justify-between">
        <div>
          <h3 className="text-lg font-semibold text-foreground">{symbol}</h3>
          <p className="text-sm text-muted-foreground">1-Year OHLCV</p>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex gap-0.5 bg-muted rounded-lg p-0.5">
            {CHART_TYPES.map((t) => (
              <button
                key={t.key}
                onClick={() => setChartType(t.key)}
                className={`px-2.5 py-1 rounded-md text-xs font-medium transition-colors duration-fast ${
                  chartType === t.key
                    ? 'bg-background shadow-sm text-foreground'
                    : 'text-muted-foreground hover:text-foreground'
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
          className="text-[10px] text-muted-foreground hover:text-foreground transition-colors duration-fast"
        >
          Charting by TradingView
        </a>
      </div>
    </div>
  );
}
