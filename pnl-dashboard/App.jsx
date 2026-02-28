import React, { useState, useEffect } from 'react';
import KPICard from './components/KPICard';
import WaterfallChart from './components/WaterfallChart';
import TrendLineChart from './components/TrendLineChart';
import CostBreakdownPie from './components/CostBreakdownPie';
import AgentAttributionBar from './components/AgentAttributionBar';

// Mock data - will be replaced with WebSocket stream
const mockPnLData = {
  revenue: 125450,
  expenses: 48320,
  netPnL: 77130,
  previousRevenue: 118200,
  previousExpenses: 45600,
  previousNetPnL: 72600,
};

const mock30DaysTrend = [
  { date: '2026-01-27', revenue: 108000, expenses: 42000, net: 66000 },
  { date: '2026-01-28', revenue: 112500, expenses: 43500, net: 69000 },
  { date: '2026-01-29', revenue: 115000, expenses: 44200, net: 70800 },
  { date: '2026-01-30', revenue: 118200, expenses: 45600, net: 72600 },
  { date: '2026-01-31', revenue: 119800, expenses: 46100, net: 73700 },
  { date: '2026-02-01', revenue: 121500, expenses: 46800, net: 74700 },
  { date: '2026-02-02', revenue: 120000, expenses: 46200, net: 73800 },
  { date: '2026-02-03', revenue: 122300, expenses: 47100, net: 75200 },
  { date: '2026-02-04', revenue: 123500, expenses: 47600, net: 75900 },
  { date: '2026-02-05', revenue: 122000, expenses: 47000, net: 75000 },
  { date: '2026-02-06', revenue: 124200, expenses: 48000, net: 76200 },
  { date: '2026-02-07', revenue: 125000, expenses: 48200, net: 76800 },
  { date: '2026-02-08', revenue: 124800, expenses: 48100, net: 76700 },
  { date: '2026-02-09', revenue: 126000, expenses: 48500, net: 77500 },
  { date: '2026-02-10', revenue: 127200, expenses: 49000, net: 78200 },
  { date: '2026-02-11', revenue: 128500, expenses: 49500, net: 79000 },
  { date: '2026-02-12', revenue: 127800, expenses: 49200, net: 78600 },
  { date: '2026-02-13', revenue: 129000, expenses: 49800, net: 79200 },
  { date: '2026-02-14', revenue: 130500, expenses: 50200, net: 80300 },
  { date: '2026-02-15', revenue: 131200, expenses: 50500, net: 80700 },
  { date: '2026-02-16', revenue: 130000, expenses: 50000, net: 80000 },
  { date: '2026-02-17', revenue: 132000, expenses: 50800, net: 81200 },
  { date: '2026-02-18', revenue: 133500, expenses: 51200, net: 82300 },
  { date: '2026-02-19', revenue: 134200, expenses: 51500, net: 82700 },
  { date: '2026-02-20', revenue: 133000, expenses: 51000, net: 82000 },
  { date: '2026-02-21', revenue: 135000, expenses: 51800, net: 83200 },
  { date: '2026-02-22', revenue: 136500, expenses: 52200, net: 84300 },
  { date: '2026-02-23', revenue: 137200, expenses: 52500, net: 84700 },
  { date: '2026-02-24', revenue: 136000, expenses: 52000, net: 84000 },
  { date: '2026-02-25', revenue: 125450, expenses: 48320, net: 77130 },
];

const mockCostBreakdown = [
  { name: 'Trading Fees', value: 18500, percentage: 38.3 },
  { name: 'Infrastructure', value: 12800, percentage: 26.5 },
  { name: 'Personnel', value: 11200, percentage: 23.2 },
  { name: 'Other', value: 5820, percentage: 12.0 },
];

const mockAgentAttribution = [
  { agent: 'Scalper', revenue: 75000, expenses: 28500, net: 46500 },
  { agent: 'John', revenue: 32000, expenses: 12800, net: 19200 },
  { agent: 'Cliff', revenue: 18450, expenses: 7020, net: 11430 },
];

export default function App() {
  const [pnlData, setPnlData] = useState(mockPnLData);
  const [trendsData, setTrendsData] = useState(mock30DaysTrend);
  const [costBreakdown, setCostBreakdown] = useState(mockCostBreakdown);
  const [agentAttribution, setAgentAttribution] = useState(mockAgentAttribution);

  // WebSocket connection setup (placeholder)
  useEffect(() => {
    // TODO: Connect to WebSocket stream
    // const ws = new WebSocket('ws://your-server/pnl-stream');
    // ws.onmessage = (event) => {
    //   const data = JSON.parse(event.data);
    //   setPnlData(data.pnl);
    //   setTrendsData(data.trends);
    //   setCostBreakdown(data.costBreakdown);
    //   setAgentAttribution(data.agentAttribution);
    // };
    // return () => ws.close();
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#1a1a2e] via-[#16213e] to-[#0f3460]">
      {/* Header */}
      <div className="border-b border-[#00d4ff]/20 bg-[#1a1a2e]/80 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-[#00d4ff] to-cyan-400 flex items-center justify-center">
                <span className="text-[#1a1a2e] font-bold text-lg">N</span>
              </div>
              <div>
                <h1 className="text-2xl font-bold text-white">NorthStar Synergy</h1>
                <p className="text-xs text-[#00d4ff]">P&L Dashboard</p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-sm text-gray-400">Real-time Analytics</p>
              <p className="text-xs text-[#00d4ff]">Updated: {new Date().toLocaleTimeString()}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* KPI Cards Section */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <KPICard
            title="Total Revenue"
            value={pnlData.revenue}
            previousValue={pnlData.previousRevenue}
            color="green"
            icon="📈"
          />
          <KPICard
            title="Total Expenses"
            value={pnlData.expenses}
            previousValue={pnlData.previousExpenses}
            color="red"
            icon="💸"
          />
          <KPICard
            title="Net P&L"
            value={pnlData.netPnL}
            previousValue={pnlData.previousNetPnL}
            color={pnlData.netPnL >= 0 ? 'green' : 'red'}
            icon="💰"
          />
        </div>

        {/* Charts Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Waterfall Chart */}
          <div className="lg:col-span-2">
            <WaterfallChart data={pnlData} />
          </div>

          {/* Trend Line Chart */}
          <TrendLineChart data={trendsData} />

          {/* Cost Breakdown Pie */}
          <CostBreakdownPie data={costBreakdown} />
        </div>

        {/* Agent Attribution */}
        <div className="w-full">
          <AgentAttributionBar data={agentAttribution} />
        </div>
      </div>

      {/* Footer */}
      <div className="border-t border-[#00d4ff]/20 bg-[#1a1a2e]/50 backdrop-blur-sm mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <p className="text-center text-xs text-gray-500">
            © 2026 NorthStar Synergy. Real-time data connection ready for WebSocket integration.
          </p>
        </div>
      </div>
    </div>
  );
}
