import React from 'react';

/**
 * Metric Card Component
 */
export default function PnLCard({ label, value, icon = '📊', className = '' }) {
  const isNumeric = typeof value === 'number';
  const displayValue = isNumeric ? value.toFixed(2) : value;

  return (
    <div className={`pnl-card ${className}`}>
      <div className="card-icon">{icon}</div>
      <div className="card-label">{label}</div>
      <div className="card-value">
        {isNumeric && <span className="currency">$</span>}
        <span className="amount">{displayValue}</span>
      </div>
    </div>
  );
}
