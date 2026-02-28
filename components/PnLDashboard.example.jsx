/**
 * Example P&L Dashboard Component
 * Demonstrates complete integration of all layers:
 * - WebSocket connection (useSocket hook)
 * - State management (Zustand store)
 * - Selective subscriptions (usePnL + selectors)
 * - Data transformation (formatCurrency, normalizeTimestamp)
 * - Error handling (ErrorBoundary)
 * - Mock data for development
 *
 * Copy and adapt this as a starting point for your dashboard.
 */

import React, { useState } from 'react';
import {
  usePnL,
  useRevenueOnly,
  useExpensesOnly,
  useNetProfitOnly,
  useTrendsOnly,
} from '../hooks/usePnL';
import {
  formatCurrency,
  formatDate,
  calculatePercentage,
} from '../utils/dataTransform';
import ErrorBoundary from './ErrorBoundary';

/**
 * Main Dashboard Component
 * Orchestrates all P&L display sections
 */
const PnLDashboard = ({ useMockData = false }) => {
  const [expandedSection, setExpandedSection] = useState(null);

  return (
    <ErrorBoundary
      showDetails={process.env.NODE_ENV === 'development'}
      onError={(error, errorInfo) => {
        console.error('Dashboard error:', error);
      }}
    >
      <div className="pnl-dashboard">
        <DashboardHeader />

        <div className="dashboard-grid">
          {/* Main KPI Cards */}
          <RevenueCard />
          <ExpensesCard />
          <ProfitCard />
          <MarginCard />

          {/* Trends Section */}
          <TrendsSection />

          {/* Status Footer */}
          <ConnectionStatus useMockData={useMockData} />
        </div>

        {/* Debug Panel (Dev Only) */}
        {process.env.NODE_ENV === 'development' && (
          <DebugPanel expandedSection={expandedSection} setExpandedSection={setExpandedSection} />
        )}
      </div>
    </ErrorBoundary>
  );
};

/**
 * Dashboard Header
 */
const DashboardHeader = () => {
  const { lastUpdated, isLoading } = usePnL();

  return (
    <div className="dashboard-header">
      <h1>📊 P&L Dashboard</h1>
      <div className="header-meta">
        <span className="update-status">
          {isLoading ? '⟳ Updating...' : `✓ Updated ${formatDate(lastUpdated || new Date())}`}
        </span>
      </div>
    </div>
  );
};

/**
 * Revenue Card
 * Uses selective subscription (only revenue changes trigger re-render)
 */
const RevenueCard = () => {
  const { revenue, lastUpdated } = useRevenueOnly();

  return (
    <MetricCard
      title="Revenue"
      value={formatCurrency(revenue)}
      color="green"
      icon="📈"
    />
  );
};

/**
 * Expenses Card
 * Uses selective subscription (only expenses changes trigger re-render)
 */
const ExpensesCard = () => {
  const { expenses, lastUpdated } = useExpensesOnly();

  return (
    <MetricCard
      title="Expenses"
      value={formatCurrency(expenses)}
      color="red"
      icon="💰"
    />
  );
};

/**
 * Net Profit Card
 * Uses selective subscription (only net profit changes trigger re-render)
 */
const ProfitCard = () => {
  const { net, lastUpdated } = useNetProfitOnly();
  const isPositive = net > 0;

  return (
    <MetricCard
      title="Net Profit"
      value={formatCurrency(net)}
      color={isPositive ? 'blue' : 'orange'}
      icon={isPositive ? '💹' : '⚠️'}
      trend={isPositive ? 'up' : 'down'}
    />
  );
};

/**
 * Margin Card
 */
const MarginCard = () => {
  const { marginPercent } = useNetProfitOnly();

  return (
    <MetricCard
      title="Margin %"
      value={`${marginPercent.toFixed(2)}%`}
      color="purple"
      icon="📊"
    />
  );
};

/**
 * Reusable Metric Card Component
 */
const MetricCard = ({
  title,
  value,
  color = 'blue',
  icon = '📌',
  trend = null,
}) => {
  const colorMap = {
    green: '#10b981',
    red: '#ef4444',
    blue: '#3b82f6',
    purple: '#8b5cf6',
    orange: '#f59e0b',
  };

  return (
    <div
      className="metric-card"
      style={{
        backgroundColor: '#f9fafb',
        border: `2px solid ${colorMap[color]}`,
        borderRadius: '8px',
        padding: '20px',
        minHeight: '120px',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
        <h3 style={{ margin: 0, fontSize: '14px', fontWeight: '600', color: '#374151' }}>
          {title}
        </h3>
        <span style={{ fontSize: '20px' }}>{icon}</span>
      </div>

      <div>
        <p style={{ margin: '12px 0 0 0', fontSize: '24px', fontWeight: 'bold', color: '#1f2937' }}>
          {value}
        </p>
        {trend && (
          <p style={{ margin: '8px 0 0 0', fontSize: '12px', color: colorMap[color] }}>
            {trend === 'up' ? '↗️ Trending up' : '↘️ Trending down'}
          </p>
        )}
      </div>
    </div>
  );
};

/**
 * Trends Section
 * Displays historical data
 */
const TrendsSection = () => {
  const { trends, lastUpdated } = useTrendsOnly();
  const [timeframe, setTimeframe] = useState('all');

  if (!trends.dates || trends.dates.length === 0) {
    return (
      <div className="trends-section" style={{ gridColumn: '1 / -1' }}>
        <h2>📈 Trends</h2>
        <p style={{ color: '#999' }}>No trend data available yet</p>
      </div>
    );
  }

  // Simple calculation of averages
  const getMetrics = () => {
    const revenueAvg =
      trends.revenue.reduce((a, b) => a + b, 0) / trends.revenue.length;
    const expensesAvg =
      trends.expenses.reduce((a, b) => a + b, 0) / trends.expenses.length;
    const netAvg = trends.net.reduce((a, b) => a + b, 0) / trends.net.length;

    return {
      avgRevenue: revenueAvg,
      avgExpenses: expensesAvg,
      avgNet: netAvg,
      minRevenue: Math.min(...trends.revenue),
      maxRevenue: Math.max(...trends.revenue),
      dataPoints: trends.revenue.length,
    };
  };

  const metrics = getMetrics();

  return (
    <div
      className="trends-section"
      style={{
        gridColumn: '1 / -1',
        backgroundColor: '#f9fafb',
        border: '2px solid #e5e7eb',
        borderRadius: '8px',
        padding: '20px',
      }}
    >
      <h2 style={{ margin: '0 0 16px 0' }}>📈 Trends Analysis</h2>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
        <TrendMetric
          label="Avg Revenue"
          value={formatCurrency(metrics.avgRevenue)}
        />
        <TrendMetric
          label="Avg Expenses"
          value={formatCurrency(metrics.avgExpenses)}
        />
        <TrendMetric
          label="Avg Net"
          value={formatCurrency(metrics.avgNet)}
        />
        <TrendMetric
          label="Revenue Range"
          value={`${formatCurrency(metrics.minRevenue)} - ${formatCurrency(metrics.maxRevenue)}`}
        />
        <TrendMetric
          label="Data Points"
          value={`${metrics.dataPoints} days`}
        />
      </div>

      <p style={{ marginTop: '16px', fontSize: '12px', color: '#666' }}>
        📊 Chart integration: Replace this with Recharts, Chart.js, or similar
      </p>
    </div>
  );
};

/**
 * Trend Metric Display
 */
const TrendMetric = ({ label, value }) => (
  <div style={{ padding: '12px', backgroundColor: 'white', borderRadius: '6px', border: '1px solid #e5e7eb' }}>
    <p style={{ margin: 0, fontSize: '12px', color: '#666' }}>{label}</p>
    <p style={{ margin: '8px 0 0 0', fontSize: '16px', fontWeight: '600' }}>
      {value}
    </p>
  </div>
);

/**
 * Connection Status Footer
 */
const ConnectionStatus = ({ useMockData }) => {
  const { isConnected, error, dataSource, isLoading } = usePnL({
    source: useMockData ? 'mock' : 'live',
  });

  const statusColor = isConnected ? '#10b981' : error ? '#ef4444' : '#f59e0b';
  const statusText = isConnected
    ? '🟢 Connected'
    : error
      ? '🔴 Error'
      : '🟡 Connecting...';

  return (
    <div
      style={{
        gridColumn: '1 / -1',
        padding: '12px',
        backgroundColor: '#f3f4f6',
        borderTop: '2px solid #e5e7eb',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        fontSize: '12px',
        color: '#666',
        marginTop: '16px',
      }}
    >
      <span>
        {statusText} — Source: {dataSource} {isLoading && '| Loading...'}
      </span>
      {error && <span style={{ color: '#ef4444' }}>Error: {error}</span>}
    </div>
  );
};

/**
 * Debug Panel (Development Only)
 */
const DebugPanel = ({ expandedSection, setExpandedSection }) => {
  const pnlFull = usePnL();

  return (
    <div
      style={{
        marginTop: '32px',
        padding: '16px',
        backgroundColor: '#1f2937',
        color: '#e5e7eb',
        borderRadius: '6px',
        fontFamily: 'monospace',
        fontSize: '11px',
        maxHeight: '300px',
        overflowY: 'auto',
      }}
    >
      <button
        onClick={() => setExpandedSection(expandedSection ? null : 'debug')}
        style={{
          background: '#374151',
          color: '#e5e7eb',
          border: 'none',
          padding: '8px 12px',
          borderRadius: '4px',
          cursor: 'pointer',
          marginBottom: '8px',
          fontSize: '11px',
        }}
      >
        {expandedSection === 'debug' ? '🔽' : '▶️'} Debug Panel
      </button>

      {expandedSection === 'debug' && (
        <pre
          style={{
            margin: 0,
            whiteSpace: 'pre-wrap',
            wordBreak: 'break-word',
          }}
        >
          {JSON.stringify(pnlFull, null, 2)}
        </pre>
      )}
    </div>
  );
};

/**
 * Export both component and standalone example
 */
export default PnLDashboard;

/**
 * Standalone Demo
 * Use this for Storybook or isolated testing
 */
export const PnLDashboardDemo = () => {
  const [useMock, setUseMock] = useState(true);

  return (
    <div style={{ padding: '20px', backgroundColor: '#ffffff' }}>
      <label style={{ marginBottom: '20px', display: 'block' }}>
        <input
          type="checkbox"
          checked={useMock}
          onChange={(e) => setUseMock(e.target.checked)}
        />{' '}
        Use Mock Data
      </label>
      <PnLDashboard useMockData={useMock} />
    </div>
  );
};

/**
 * Stylesheet
 * Add this to your CSS:
 */
const DASHBOARD_STYLES = `
.pnl-dashboard {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
  background: white;
}

.dashboard-header {
  margin-bottom: 32px;
  border-bottom: 2px solid #e5e7eb;
  padding-bottom: 16px;
}

.dashboard-header h1 {
  margin: 0;
  font-size: 32px;
  color: #1f2937;
}

.header-meta {
  margin-top: 8px;
  font-size: 13px;
  color: #666;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 16px;
}

.metric-card {
  transition: all 0.2s ease;
}

.metric-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.trends-section {
  margin-top: 16px;
}

.trends-section h2 {
  margin: 0 0 16px 0;
  font-size: 18px;
  color: #1f2937;
}
`;

// Optional: Auto-inject styles
if (typeof document !== 'undefined') {
  const style = document.createElement('style');
  style.innerHTML = DASHBOARD_STYLES;
  document.head.appendChild(style);
}
