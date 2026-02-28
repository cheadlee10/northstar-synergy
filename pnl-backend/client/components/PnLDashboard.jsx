import React, { useEffect } from 'react';
import {
  usePnLSocket,
  usePnLMetrics,
  usePnLComponents,
  usePnLConnection,
  useLastUpdate
} from '../pnlStore';
import PnLCard from './PnLCard';
import ComponentBreakdown from './ComponentBreakdown';
import ConnectionStatus from './ConnectionStatus';

/**
 * Main P&L Dashboard Component
 */
export default function PnLDashboard() {
  const { initSocket, disconnect } = usePnLSocket();
  const metrics = usePnLMetrics();
  const components = usePnLComponents();
  const { connected, loading, error } = usePnLConnection();
  const lastUpdate = useLastUpdate();

  // Initialize socket on mount
  useEffect(() => {
    initSocket();

    return () => {
      disconnect();
    };
  }, [initSocket, disconnect]);

  return (
    <div className="pnl-dashboard">
      <header className="dashboard-header">
        <h1>Real-Time P&L Dashboard</h1>
        <ConnectionStatus connected={connected} loading={loading} lastUpdate={lastUpdate} />
      </header>

      {error && (
        <div className="error-banner">
          <p>⚠️ {error}</p>
        </div>
      )}

      <div className="metrics-grid">
        <PnLCard
          label="Total Revenue"
          value={metrics.totalRevenue}
          icon="📈"
          className="revenue"
        />

        <PnLCard
          label="Total Expenses"
          value={metrics.totalExpenses}
          icon="💰"
          className="expense"
          isNegative
        />

        <PnLCard
          label="Net P&L"
          value={metrics.netPnL}
          icon="📊"
          className={metrics.netPnL >= 0 ? 'positive' : 'negative'}
        />

        <PnLCard
          label="Gross Margin"
          value={`${metrics.grossMargin}%`}
          icon="📐"
          className="margin"
        />

        <PnLCard
          label="Daily Trend"
          value={`${metrics.dailyTrend > 0 ? '+' : ''}${metrics.dailyTrend}%`}
          icon={metrics.dailyTrend >= 0 ? '📈' : '📉'}
          className={metrics.dailyTrend >= 0 ? 'positive' : 'negative'}
        />
      </div>

      <div className="breakdown-section">
        <h2>Component Breakdown</h2>
        <ComponentBreakdown components={components} />
      </div>

      <div className="metadata">
        <small>
          Last updated: {lastUpdate ? new Date(lastUpdate).toLocaleTimeString() : 'Never'}
          {' '} | Status: {connected ? '🟢 Connected' : '🔴 Disconnected'}
        </small>
      </div>
    </div>
  );
}
