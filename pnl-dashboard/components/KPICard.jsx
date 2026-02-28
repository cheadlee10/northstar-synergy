import React, { useState, useEffect } from 'react';

// Animated counter component
function AnimatedCounter({ value, duration = 1000 }) {
  const [displayValue, setDisplayValue] = useState(0);

  useEffect(() => {
    let startTime = Date.now();
    const startValue = displayValue;
    const diff = value - startValue;

    const animate = () => {
      const elapsed = Date.now() - startTime;
      const progress = Math.min(elapsed / duration, 1);
      setDisplayValue(Math.round(startValue + diff * progress));

      if (progress < 1) {
        requestAnimationFrame(animate);
      }
    };

    requestAnimationFrame(animate);
  }, [value, duration]);

  return displayValue;
}

export default function KPICard({ title, value, previousValue, color = 'green', icon = '📊' }) {
  const change = value - previousValue;
  const percentChange = ((change / previousValue) * 100).toFixed(2);
  const isPositive = change >= 0;

  const colorClasses = {
    green: {
      bg: 'from-emerald-900/20 to-emerald-800/10',
      border: 'border-emerald-500/30',
      text: 'text-emerald-400',
      accent: 'bg-emerald-500/20',
    },
    red: {
      bg: 'from-red-900/20 to-red-800/10',
      border: 'border-red-500/30',
      text: 'text-red-400',
      accent: 'bg-red-500/20',
    },
  };

  const currentColors = colorClasses[color] || colorClasses.green;

  return (
    <div
      className={`bg-gradient-to-br ${currentColors.bg} border ${currentColors.border} rounded-xl p-6 backdrop-blur-sm transition-all duration-300 hover:border-[#00d4ff]/50 group`}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div>
          <p className="text-gray-400 text-sm font-medium">{title}</p>
        </div>
        <div className="text-3xl">{icon}</div>
      </div>

      {/* Main Value */}
      <div className="mb-4">
        <div className="text-4xl font-bold text-white font-mono tracking-tight">
          $<AnimatedCounter value={Math.abs(value)} duration={800} />
        </div>
      </div>

      {/* Change Indicator */}
      <div className="flex items-center gap-2 mb-2">
        <div
          className={`
            inline-flex items-center gap-1 px-3 py-1 rounded-lg font-mono text-sm
            ${isPositive ? 'bg-emerald-500/20 text-emerald-300' : 'bg-red-500/20 text-red-300'}
          `}
        >
          <span>{isPositive ? '↑' : '↓'}</span>
          <span>${Math.abs(change).toLocaleString()}</span>
          <span className="text-xs">({percentChange}%)</span>
        </div>
      </div>

      {/* Trend Bar */}
      <div className="w-full bg-gray-700/30 rounded-full h-2 overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ${
            isPositive ? 'bg-gradient-to-r from-emerald-500 to-emerald-400' : 'bg-gradient-to-r from-red-500 to-red-400'
          }`}
          style={{ width: `${Math.min((percentChange / 10) * 100, 100)}%` }}
        />
      </div>

      {/* Footer */}
      <p className="text-xs text-gray-500 mt-3">vs previous: ${previousValue.toLocaleString()}</p>
    </div>
  );
}
