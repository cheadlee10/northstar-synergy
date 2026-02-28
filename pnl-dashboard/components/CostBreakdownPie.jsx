import React from 'react';
import {
  PieChart,
  Pie,
  Cell,
  Legend,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

export default function CostBreakdownPie({ data }) {
  const colors = ['#f97316', '#ef4444', '#ec4899', '#8b5cf6'];

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-[#1a1a2e]/95 border border-[#00d4ff]/30 rounded-lg p-3 backdrop-blur-sm">
          <p className="text-white text-xs font-bold">{payload[0].name}</p>
          <p className="text-cyan-300 text-xs font-mono mt-1">
            ${(payload[0].value || 0).toLocaleString()}
          </p>
          <p className="text-gray-400 text-xs mt-1">{payload[0].payload.percentage}%</p>
        </div>
      );
    }
    return null;
  };

  const renderCustomLabel = ({ name, percentage }) => {
    return `${percentage}%`;
  };

  return (
    <div className="bg-gradient-to-br from-orange-900/20 to-orange-800/10 border border-orange-500/30 rounded-xl p-6 backdrop-blur-sm">
      <div className="mb-4">
        <h2 className="text-xl font-bold text-white flex items-center gap-2">
          <span>🥧</span>
          Cost Breakdown
        </h2>
        <p className="text-sm text-gray-400 mt-1">Expense distribution by category</p>
      </div>

      <div className="bg-[#1a1a2e]/50 rounded-lg overflow-hidden border border-orange-500/10">
        <ResponsiveContainer width="100%" height={280}>
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={renderCustomLabel}
              outerRadius={80}
              fill="#8884d8"
              dataKey="value"
              animationBegin={0}
              animationDuration={600}
            >
              {data.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={colors[index % colors.length]}
                />
              ))}
            </Pie>
            <Tooltip content={<CustomTooltip />} />
          </PieChart>
        </ResponsiveContainer>
      </div>

      {/* Legend */}
      <div className="grid grid-cols-2 gap-3 mt-4">
        {data.map((item, index) => (
          <div key={index} className="flex items-center gap-2 text-xs">
            <div
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: colors[index % colors.length] }}
            />
            <div className="flex-1">
              <p className="text-gray-400">{item.name}</p>
              <p className="text-white font-bold">${item.value.toLocaleString()}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Total */}
      <div className="bg-orange-500/10 border border-orange-500/20 rounded-lg p-3 mt-4">
        <p className="text-gray-400 text-xs">Total Expenses</p>
        <p className="text-orange-300 font-bold mt-1 text-lg">
          ${data.reduce((sum, item) => sum + item.value, 0).toLocaleString()}
        </p>
      </div>
    </div>
  );
}
