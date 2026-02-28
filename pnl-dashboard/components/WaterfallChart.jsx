import React from 'react';
import { Waterfall } from '@ant-design/charts';

export default function WaterfallChart({ data }) {
  // Transform data for waterfall chart
  const waterfallData = [
    {
      name: 'Starting Value',
      value: 0,
      type: 'total',
    },
    {
      name: 'Revenue',
      value: data.revenue,
      type: 'segment',
    },
    {
      name: 'Expenses',
      value: -data.expenses,
      type: 'segment',
    },
    {
      name: 'Net P&L',
      value: data.netPnL,
      type: 'total',
    },
  ];

  const config = {
    data: waterfallData,
    xField: 'name',
    yField: 'value',
    seriesField: 'type',
    color: {
      segment: '#00d4ff',
      total: '#10b981',
    },
    label: {
      formatter: (datum) => {
        return `$${Math.abs(datum.value).toLocaleString()}`;
      },
    },
    height: 400,
    theme: 'dark',
    // Styling for dark theme
    style: {
      background: 'transparent',
    },
  };

  return (
    <div className="bg-gradient-to-br from-blue-900/20 to-blue-800/10 border border-blue-500/30 rounded-xl p-6 backdrop-blur-sm">
      <div className="mb-4">
        <h2 className="text-xl font-bold text-white flex items-center gap-2">
          <span>📊</span>
          P&L Waterfall
        </h2>
        <p className="text-sm text-gray-400 mt-1">Revenue → Expenses → Net Profit</p>
      </div>

      <div className="bg-[#1a1a2e]/50 rounded-lg overflow-hidden border border-blue-500/10">
        <Waterfall {...config} />
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4 mt-6">
        <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-4">
          <p className="text-gray-400 text-xs font-medium">Revenue</p>
          <p className="text-xl font-bold text-blue-300 mt-1">
            ${data.revenue.toLocaleString()}
          </p>
        </div>
        <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4">
          <p className="text-gray-400 text-xs font-medium">Expenses</p>
          <p className="text-xl font-bold text-red-300 mt-1">
            ${data.expenses.toLocaleString()}
          </p>
        </div>
        <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-lg p-4">
          <p className="text-gray-400 text-xs font-medium">Net P&L</p>
          <p className="text-xl font-bold text-emerald-300 mt-1">
            ${data.netPnL.toLocaleString()}
          </p>
        </div>
      </div>
    </div>
  );
}
