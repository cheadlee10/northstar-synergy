import React from 'react';

/**
 * Component Breakdown Component - Shows detailed breakdown by source
 */
export default function ComponentBreakdown({ components }) {
  return (
    <div className="component-breakdown">
      <div className="component-section">
        <h3>🎯 Kalshi Trading</h3>
        <div className="component-details">
          <div className="detail-row">
            <span className="label">Balance:</span>
            <span className="value">${components.kalshi?.balance?.toFixed(2) || '0.00'}</span>
          </div>
          <div className="detail-row">
            <span className="label">Open Positions:</span>
            <span className="value">{components.kalshi?.positions || 0}</span>
          </div>
          <div className="detail-row">
            <span className="label">P&L:</span>
            <span className={`value ${components.kalshi?.pnl >= 0 ? 'positive' : 'negative'}`}>
              ${components.kalshi?.pnl?.toFixed(2) || '0.00'}
            </span>
          </div>
        </div>
      </div>

      <div className="component-section">
        <h3>🤖 Anthropic API</h3>
        <div className="component-details">
          <div className="detail-row">
            <span className="label">Daily Spend:</span>
            <span className="value negative">-${components.anthropic?.dailySpend?.toFixed(2) || '0.00'}</span>
          </div>
        </div>
      </div>

      <div className="component-section">
        <h3>💼 John's Revenue</h3>
        <div className="component-details">
          <div className="detail-row">
            <span className="label">Invoiced:</span>
            <span className="value">${components.johns?.invoiced?.toFixed(2) || '0.00'}</span>
          </div>
          <div className="detail-row">
            <span className="label">Collected:</span>
            <span className={`value ${components.johns?.collected > 0 ? 'positive' : ''}`}>
              ${components.johns?.collected?.toFixed(2) || '0.00'}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
