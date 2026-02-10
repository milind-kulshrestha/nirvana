import { useState, useEffect, useCallback } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { useAISerializable } from '../hooks/useAISerializable';
import SendToAIButton from './SendToAIButton';
import { API_BASE } from '../config';

export default function PriceChart({ symbol }) {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const serializeFn = useCallback(() => {
    if (!data || data.length === 0) return { type: 'price-chart', symbol, dataPoints: 0 };
    const prices = data.map((d) => d.close);
    return {
      type: 'price-chart',
      symbol,
      dataPoints: data.length,
      dateRange: { start: data[0]?.date, end: data[data.length - 1]?.date },
      priceRange: { min: Math.min(...prices), max: Math.max(...prices) },
      startPrice: data[0]?.close,
      endPrice: data[data.length - 1]?.close,
      changePercent: data[0]?.close
        ? ((data[data.length - 1]?.close - data[0]?.close) / data[0]?.close * 100).toFixed(2)
        : null,
    };
  }, [symbol, data]);

  const chartRef = useAISerializable(`chart-${symbol}`, serializeFn);

  useEffect(() => {
    if (!symbol) return;

    const fetchChartData = async () => {
      setLoading(true);
      setError(null);

      try {
        const response = await fetch(
          `${API_BASE}/api/securities/${symbol}?include=history`,
          { credentials: 'include' }
        );

        if (response.ok) {
          const stockData = await response.json();
          setData(stockData.history || []);
        } else {
          setError('Failed to load chart data');
        }
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchChartData();
  }, [symbol]);

  if (loading) {
    return (
      <div className="bg-white rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">{symbol} Chart</h3>
        <div className="flex items-center justify-center h-64">
          <div className="text-gray-500">Loading chart...</div>
        </div>
      </div>
    );
  }

  if (error || !data || data.length === 0) {
    return (
      <div className="bg-white rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">{symbol} Chart</h3>
        <div className="flex items-center justify-center h-64">
          <div className="text-gray-500">
            {error || 'No chart data available'}
          </div>
        </div>
      </div>
    );
  }

  // Calculate min and max for better chart scaling
  const prices = data.map((d) => d.close);
  const minPrice = Math.min(...prices);
  const maxPrice = Math.max(...prices);
  const priceRange = maxPrice - minPrice;
  const yMin = minPrice - priceRange * 0.1;
  const yMax = maxPrice + priceRange * 0.1;

  // Determine if stock is trending up or down
  const firstPrice = data[0]?.close || 0;
  const lastPrice = data[data.length - 1]?.close || 0;
  const isPositive = lastPrice >= firstPrice;
  const lineColor = isPositive ? '#10b981' : '#ef4444';

  return (
    <div ref={chartRef} className="bg-white rounded-lg p-6">
      <div className="mb-4 flex items-start justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">{symbol}</h3>
          <p className="text-sm text-gray-500">6-Month Price History</p>
        </div>
        <SendToAIButton componentId={`chart-${symbol}`} label={`Ask AI about ${symbol} chart`} />
      </div>

      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data} margin={{ top: 5, right: 5, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="date"
            tick={{ fontSize: 12 }}
            tickFormatter={(date) => {
              const d = new Date(date);
              return `${d.getMonth() + 1}/${d.getDate()}`;
            }}
          />
          <YAxis
            domain={[yMin, yMax]}
            tick={{ fontSize: 12 }}
            tickFormatter={(value) => `$${value.toFixed(0)}`}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#fff',
              border: '1px solid #e5e7eb',
              borderRadius: '8px',
            }}
            formatter={(value) => [`$${value.toFixed(2)}`, 'Close']}
            labelFormatter={(date) => new Date(date).toLocaleDateString()}
          />
          <Line
            type="monotone"
            dataKey="close"
            stroke={lineColor}
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4 }}
          />
        </LineChart>
      </ResponsiveContainer>

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
    </div>
  );
}
