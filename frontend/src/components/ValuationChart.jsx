import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

export default function ValuationChart({ data }) {
  if (!data || data.length === 0) {
    return (
      <div className="p-4 text-center text-gray-500">
        No valuation data available
      </div>
    );
  }

  const chartConfig = {
    height: 200,
    margin: { top: 5, right: 20, left: 10, bottom: 5 }
  };

  const renderMetricChart = (dataKey, title) => (
    <div className="mb-6 last:mb-0" key={dataKey}>
      <h4 className="text-sm font-semibold text-gray-700 mb-2">{title}</h4>
      <ResponsiveContainer width="100%" height={chartConfig.height}>
        <LineChart data={data} margin={chartConfig.margin}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="date"
            tick={{ fontSize: 12 }}
            tickFormatter={(date) => {
              const d = new Date(date);
              return `${d.getMonth() + 1}/${String(d.getDate()).slice(-2)}`;
            }}
          />
          <YAxis
            tick={{ fontSize: 12 }}
            tickFormatter={(value) => value?.toFixed(1) || ''}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#fff',
              border: '1px solid #e5e7eb',
              borderRadius: '8px',
            }}
            labelFormatter={(date) => new Date(date).toLocaleDateString()}
            formatter={(value) => [value?.toFixed(2) || 'N/A', title]}
          />
          <Line
            type="monotone"
            dataKey={dataKey}
            stroke="#000000"
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4 }}
            connectNulls
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );

  return (
    <div className="p-4">
      {renderMetricChart('pe_ratio', 'P/E Ratio')}
      {renderMetricChart('pb_ratio', 'P/B Ratio')}
      {renderMetricChart('ps_ratio', 'P/S Ratio')}
    </div>
  );
}
