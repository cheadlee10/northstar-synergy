import React, { useState } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
} from 'recharts';

export default function AgentAttributionBar({ data }) {
  const [hoveredAgent, setHoveredAgent] = useState(null);

  // Calculate totals
  const totalRevenue = data.reduce((sum, item) => sum + item.revenue, 0);
  const totalExpenses = data.reduce((sum, item) => sum + item.expenses, 0);
  const totalNet = data.reduce((sum, item) => sum + item.net, 0);

  // Agent colors
  const agentColors = {
    Scalper: '#10b981',
    John: '#3b82f6',
    Cliff: '#f59e0b',
  };

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-[#1a1a2e]/95 border border-[#00d4ff]/30 rounded-lg p-3 backdrop-blur-sm">
          <p className="text-white text-xs font-bold">{payload[0].payload.agent}</p>
          <p className="text-gray-300 text-xs mt-1">
            {payload[0].name}: ${(payload[0].value || 0).toLocaleString()}
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="bg-gradient-to-br from-amber-900/20 to-amber-800/10 border border-amber-500/30 rounded-xl p-6 backdrop-blur-sm">
      <div className="mb-4">
        <h2 className="text-xl font-bold text-white flex items-center gap-2">
          <span>👥</span>
          Agent Attribution
        </h2>
        <p className="text-sm text-gray-400 mt-1">Revenue, Expenses & Net P&L by Agent</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4 mb-6">
        {/* Overview Cards */}
        <div className="bg-amber-500/10 border border-amber-500/20 rounded-lg p-4">
          <p className="text-gray-400 text-xs font-medium">Total Revenue</p>
          <p className="text-amber-300 font-bold text-lg mt-2">
            ${totalRevenue.toLocaleString()}
          </p>
        </div>
        <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4">
          <p className="text-gray-400 text-xs font-medium">Total Expenses</p>
          <p className="text-red-300 font-bold text-lg mt-2">
            ${totalExpenses.toLocaleString()}
          </p>
        </div>
        <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-lg p-4">
          <p className="text-gray-400 text-xs font-medium">Total Net P&L</p>
          <p className="text-emerald-300 font-bold text-lg mt-2">
            ${totalNet.toLocaleString()}
          </p>
        </div>
        <div className="bg-cyan-500/10 border border-cyan-500/20 rounded-lg p-4">
          <p className="text-gray-400 text-xs font-medium">Avg Margin</p>
          <p className="text-cyan-300 font-bold text-lg mt-2">
            {((totalNet / totalRevenue) * 100).toFixed(1)}%
          </p>
        </div>
      </div>

      {/* Bar Chart */}
      <div className="bg-[#1a1a2e]/50 rounded-lg overflow-hidden border border-amber-500/10 mb-6">
        <ResponsiveContainer width="100%" height={320}>
          <BarChart
            data={data}
            margin={{ top: 20, right: 30, left: 0, bottom: 20 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#00d4ff/10" />
            <XAxis
              dataKey="agent"
              stroke="#999"
              style={{ fontSize: '12px' }}
              tick={{ fill: '#999' }}
            />
            <YAxis
              stroke="#999"
              style={{ fontSize: '12px' }}
              tick={{ fill: '#999' }}
              tickFormatter={(value) => `$${(value / 1000).toFixed(0)}K`}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend wrapperStyle={{ color: '#999', paddingTop: '20px' }} />
            <Bar
              dataKey="revenue"
              fill="#10b981"
              name="Revenue"
              radius={[8, 8, 0, 0]}
              animationDuration={600}
            />
            <Bar
              dataKey="expenses"
              fill="#ef4444"
              name="Expenses"
              radius={[8, 8, 0, 0]}
              animationDuration={600}
            />
            <Bar
              dataKey="net"
              fill="#00d4ff"
              name="Net P&L"
              radius={[8, 8, 0, 0]}
              animationDuration={600}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Agent Details */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {data.map((agent, index) => {
          const margin = ((agent.net / agent.revenue) * 100).toFixed(1);
          const revenuePercent = ((agent.revenue / totalRevenue) * 100).toFixed(1);

          return (
            <div
              key={index}
              className="bg-[#1a1a2e]/50 border border-amber-500/20 rounded-lg p-4 hover:border-amber-500/50 transition-all cursor-pointer"
              onMouseEnter={() => setHoveredAgent(agent.agent)}
              onMouseLeave={() => setHoveredAgent(null)}
            >
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-bold text-white">{agent.agent}</h3>
                <div
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: agentColors[agent.agent] || '#00d4ff' }}
                />
              </div>

              <div className="space-y-2 text-xs">
                <div className="flex justify-between">
                  <span className="text-gray-400">Revenue</span>
                  <span className="text-green-300 font-bold">
                    ${agent.revenue.toLocaleString()}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Expenses</span>
                  <span className="text-red-300 font-bold">
                    ${agent.expenses.toLocaleString()}
                  </span>
                </div>
                <div className="border-t border-amber-500/10 pt-2 mt-2 flex justify-between">
                  <span className="text-gray-400">Net P&L</span>
                  <span className="text-cyan-300 font-bold">
                    ${agent.net.toLocaleString()}
                  </span>
                </div>
              </div>

              <div className="mt-4 pt-3 border-t border-amber-500/10">
                <div className="flex justify-between text-xs mb-2">
                  <span className="text-gray-400">Contribution</span>
                  <span className="text-amber-300 font-bold">{revenuePercent}%</span>
                </div>
                <div className="w-full bg-gray-700/30 rounded-full h-2 overflow-hidden">
                  <div
                    className="h-full rounded-full"
                    style={{
                      width: `${revenuePercent}%`,
                      backgroundColor: agentColors[agent.agent] || '#00d4ff',
                    }}
                  />
                </div>
              </div>

              <div className="mt-3 text-xs">
                <span className="text-gray-400">Margin: </span>
                <span className="text-amber-300 font-bold">{margin}%</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
