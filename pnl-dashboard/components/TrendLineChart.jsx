import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

export default function TrendLineChart({ data }) {
  // Format data for recharts
  const chartData = data.map((item) => ({
    date: new Date(item.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    revenue: item.revenue,
    expenses: item.expenses,
    net: item.net,
  }));

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-[#1a1a2e]/95 border border-[#00d4ff]/30 rounded-lg p-3 backdrop-blur-sm">
          <p className="text-white text-xs font-bold">{label}</p>
          {payload.map((entry, index) => (
            <p key={index} style={{ color: entry.color }} className="text-xs font-mono mt-1">
              {entry.name}: ${(entry.value || 0).toLocaleString()}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="bg-gradient-to-br from-purple-900/20 to-purple-800/10 border border-purple-500/30 rounded-xl p-6 backdrop-blur-sm">
      <div className="mb-4">
        <h2 className="text-xl font-bold text-white flex items-center gap-2">
          <span>📈</span>
          30-Day Trend
        </h2>
        <p className="text-sm text-gray-400 mt-1">Revenue, Expenses & Net P&L over time</p>
      </div>

      <div className="bg-[#1a1a2e]/50 rounded-lg overflow-hidden border border-purple-500/10">
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={chartData} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#00d4ff/10" />
            <XAxis
              dataKey="date"
              stroke="#999"
              style={{ fontSize: '12px' }}
              tick={{ fill: '#999' }}
              angle={-45}
              textAnchor="end"
              height={80}
            />
            <YAxis
              stroke="#999"
              style={{ fontSize: '12px' }}
              tick={{ fill: '#999' }}
              tickFormatter={(value) => `$${(value / 1000).toFixed(0)}K`}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend
              wrapperStyle={{ color: '#999', paddingTop: '20px' }}
              iconType="line"
            />
            <Line
              type="monotone"
              dataKey="revenue"
              stroke="#10b981"
              strokeWidth={2}
              dot={false}
              name="Revenue"
              isAnimationActive={true}
            />
            <Line
              type="monotone"
              dataKey="expenses"
              stroke="#ef4444"
              strokeWidth={2}
              dot={false}
              name="Expenses"
              isAnimationActive={true}
            />
            <Line
              type="monotone"
              dataKey="net"
              stroke="#00d4ff"
              strokeWidth={2.5}
              dot={false}
              name="Net P&L"
              isAnimationActive={true}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-3 gap-3 mt-4 text-xs">
        <div className="bg-purple-500/10 border border-purple-500/20 rounded-lg p-3">
          <p className="text-gray-400">Avg Revenue</p>
          <p className="text-green-300 font-bold mt-1">
            ${(data.reduce((sum, d) => sum + d.revenue, 0) / data.length).toLocaleString('en-US', {
              maximumFractionDigits: 0,
            })}
          </p>
        </div>
        <div className="bg-purple-500/10 border border-purple-500/20 rounded-lg p-3">
          <p className="text-gray-400">Avg Expenses</p>
          <p className="text-red-300 font-bold mt-1">
            ${(data.reduce((sum, d) => sum + d.expenses, 0) / data.length).toLocaleString('en-US', {
              maximumFractionDigits: 0,
            })}
          </p>
        </div>
        <div className="bg-purple-500/10 border border-purple-500/20 rounded-lg p-3">
          <p className="text-gray-400">Avg Net P&L</p>
          <p className="text-cyan-300 font-bold mt-1">
            ${(data.reduce((sum, d) => sum + d.net, 0) / data.length).toLocaleString('en-US', {
              maximumFractionDigits: 0,
            })}
          </p>
        </div>
      </div>
    </div>
  );
}
