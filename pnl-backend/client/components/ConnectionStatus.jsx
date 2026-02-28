import React from 'react';

/**
 * Connection Status Component
 */
export default function ConnectionStatus({ connected, loading, lastUpdate }) {
  const getStatusColor = () => {
    if (loading) return '#ffa500'; // Orange
    if (connected) return '#00aa00'; // Green
    return '#ff0000'; // Red
  };

  const getStatusText = () => {
    if (loading) return 'Connecting...';
    if (connected) return 'Connected';
    return 'Disconnected';
  };

  const formattedTime = lastUpdate 
    ? new Date(lastUpdate).toLocaleTimeString()
    : 'Never';

  return (
    <div className="connection-status">
      <div className="status-indicator" style={{ backgroundColor: getStatusColor() }} />
      <span className="status-text">{getStatusText()}</span>
      <span className="last-update">Last: {formattedTime}</span>
    </div>
  );
}
