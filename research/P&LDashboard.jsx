/**
 * REAL-TIME P&L DASHBOARD - REACT COMPONENT
 * Handles WebSocket + SSE + Polling fallback
 * Target: NorthStar Synergy live P&L display
 */

import React, { useEffect, useState, useRef, useCallback } from 'react';
import './P&LDashboard.css';

const P&LDashboard = ({ wsUrl = 'ws://localhost:8080' }) => {
  // State: P&L data
  const [pnl, setPnl] = useState(null);
  const [history, setHistory] = useState([]); // For sparkline chart

  // State: Connection
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const [protocol, setProtocol] = useState(null);
  const [latency, setLatency] = useState(null);

  // References
  const wsRef = useRef(null);
  const sseRef = useRef(null);
  const pollingRef = useRef(null);
  const reconnectAttemptsRef = useRef(0);
  const lastUpdateRef = useRef(Date.now());

  // =========================================================================
  // PRIMARY: WebSocket Connection
  // =========================================================================

  const connectWebSocket = useCallback(() => {
    if (wsRef.current) return; // Already connected

    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const url = wsUrl.startsWith('ws') ? wsUrl : `${protocol}//localhost:8080`;

      console.log('[WS] Connecting to', url);
      const ws = new WebSocket(url);

      ws.onopen = () => {
        console.log('[WS] Connected');
        setConnectionStatus('connected');
        setProtocol('WebSocket');
        reconnectAttemptsRef.current = 0;

        // Send initial ping to check latency
        const startTime = Date.now();
        ws.send(JSON.stringify({ type: 'ping' }));

        // Expect pong response
        const pongTimeout = setTimeout(() => {
          console.warn('[WS] No pong response');
        }, 1000);

        ws.onmessage = (event) => {
          const msg = JSON.parse(event.data);
          if (msg.type === 'pong') {
            clearTimeout(pongTimeout);
            setLatency(Date.now() - startTime);
          }
        };
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          handleP&LUpdate(message);
        } catch (err) {
          console.error('[WS] Message parse error:', err);
        }
      };

      ws.onerror = (event) => {
        console.error('[WS] Error:', event);
        setConnectionStatus('error');
      };

      ws.onclose = () => {
        console.log('[WS] Closed, attempting fallback...');
        setConnectionStatus('disconnected');
        wsRef.current = null;

        // Exponential backoff
        const delay = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 30000);
        reconnectAttemptsRef.current++;

        setTimeout(() => {
          if (wsRef.current === null && sseRef.current === null && pollingRef.current === null) {
            connectWebSocket();
          }
        }, delay);
      };

      wsRef.current = ws;
    } catch (err) {
      console.error('[WS] Connection failed:', err);
      // Fall through to SSE
      connectSSE();
    }
  }, [wsUrl]);

  // =========================================================================
  // FALLBACK 1: Server-Sent Events (SSE)
  // =========================================================================

  const connectSSE = useCallback(() => {
    if (sseRef.current || wsRef.current) return; // Already have connection

    try {
      console.log('[SSE] Connecting to /api/pnl/stream');
      const sse = new EventSource('/api/pnl/stream');

      sse.onopen = () => {
        console.log('[SSE] Connected');
        setConnectionStatus('connected');
        setProtocol('SSE');
        reconnectAttemptsRef.current = 0;
      };

      sse.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          handleP&LUpdate(message);
        } catch (err) {
          console.error('[SSE] Parse error:', err);
        }
      };

      sse.onerror = () => {
        console.error('[SSE] Error, closing');
        sse.close();
        sseRef.current = null;

        // Fall back to polling
        connectPolling();
      };

      sseRef.current = sse;
    } catch (err) {
      console.error('[SSE] Failed:', err);
      connectPolling();
    }
  }, []);

  // =========================================================================
  // FALLBACK 2: HTTP Polling
  // =========================================================================

  const connectPolling = useCallback(() => {
    if (pollingRef.current || wsRef.current || sseRef.current) return;

    console.log('[POLL] Starting 30s polling');
    setConnectionStatus('connected');
    setProtocol('HTTP Polling');

    const poll = async () => {
      try {
        const startTime = Date.now();
        const response = await fetch('/api/pnl/current', {
          method: 'GET',
          headers: { 'Content-Type': 'application/json' }
        });

        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        const data = await response.json();
        const fetchLatency = Date.now() - startTime;
        setLatency(fetchLatency);

        handleP&LUpdate({ type: 'snapshot', data });
      } catch (err) {
        console.error('[POLL] Fetch error:', err);
        setConnectionStatus('error');
      }
    };

    // Poll every 30 seconds
    poll(); // Immediate first poll
    const pollInterval = setInterval(poll, 30000);
    pollingRef.current = pollInterval;
  }, []);

  // =========================================================================
  // Handle P&L Updates (from any source)
  // =========================================================================

  const handleP&LUpdate = useCallback((message) => {
    if (message.type === 'snapshot') {
      // Full snapshot
      setPnl(message.data);
      addToHistory(message.data);
      lastUpdateRef.current = Date.now();
    } else if (message.type === 'delta') {
      // Incremental delta
      setPnl((prev) => {
        if (!prev) return null;
        return {
          ...prev,
          netP&L: prev.netP&L + message.data.netP&LDelta,
          kalshiP&L: prev.kalshiP&L + message.data.kalshiDelta,
          totalCosts: prev.totalCosts + message.data.costsDelta,
          totalRevenue: prev.totalRevenue + message.data.revenueDelta,
          timestamp: message.timestamp
        };
      });
      lastUpdateRef.current = Date.now();
    }
  }, []);

  const addToHistory = useCallback((pnlSnapshot) => {
    setHistory((prev) => {
      const next = [
        ...prev.slice(-59), // Keep last 60 points
        {
          timestamp: pnlSnapshot.timestamp,
          netP&L: pnlSnapshot.netP&L
        }
      ];
      return next;
    });
  }, []);

  // =========================================================================
  // Effects
  // =========================================================================

  useEffect(() => {
    // Start connection attempts
    connectWebSocket();

    return () => {
      // Cleanup
      if (wsRef.current) wsRef.current.close();
      if (sseRef.current) sseRef.current.close();
      if (pollingRef.current) clearInterval(pollingRef.current);
    };
  }, [connectWebSocket]);

  // Fallback timer: if no update in 60s, force reconnect
  useEffect(() => {
    const fallbackTimer = setInterval(() => {
      const timeSinceUpdate = Date.now() - lastUpdateRef.current;
      if (timeSinceUpdate > 60000) {
        console.warn('[FALLBACK] No update for 60s, reconnecting...');
        if (wsRef.current) wsRef.current.close();
        if (sseRef.current) sseRef.current.close();
        wsRef.current = null;
        sseRef.current = null;
        pollingRef.current = null;
        connectWebSocket();
      }
    }, 10000); // Check every 10s

    return () => clearInterval(fallbackTimer);
  }, [connectWebSocket]);

  // =========================================================================
  // Render
  // =========================================================================

  if (!pnl) {
    return (
      <div className="pnl-dashboard loading">
        <div className="spinner"></div>
        <p>Connecting to P&L feed...</p>
        <small className="status-text">
          {connectionStatus === 'error' ? '❌ Connection Error' : '⏳ Connecting'}
        </small>
      </div>
    );
  }

  const netP&LColor = pnl.netP&L >= 0 ? '#22c55e' : '#ef4444'; // green or red
  const formattedTime = new Date(pnl.timestamp).toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  });

  return (
    <div className="pnl-dashboard">
      {/* Header */}
      <div className="dashboard-header">
        <h1>NorthStar P&L</h1>
        <div className="connection-badge">
          {connectionStatus === 'connected' && <span className="dot green"></span>}
          {connectionStatus === 'error' && <span className="dot red"></span>}
          {connectionStatus === 'disconnected' && <span className="dot yellow"></span>}
          <span className="status-text">
            {protocol || 'Disconnected'}
            {latency && ` • ${latency}ms`}
          </span>
        </div>
      </div>

      {/* Main P&L Display */}
      <div className="pnl-main">
        <div className="pnl-value" style={{ color: netP&LColor }}>
          ${pnl.netP&L.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
        </div>
        <div className="pnl-label">Net P&L</div>
        <div className="pnl-updated">
          Last update: {formattedTime}
        </div>
      </div>

      {/* Breakdown */}
      <div className="pnl-breakdown">
        <div className="breakdown-card trades">
          <div className="card-title">Kalshi Trades</div>
          <div className="card-value" style={{
            color: pnl.breakdown.trades >= 0 ? '#22c55e' : '#ef4444'
          }}>
            ${pnl.breakdown.trades.toLocaleString('en-US', { minimumFractionDigits: 2 })}
          </div>
          <div className="card-meta">{pnl.components?.openTradeCount || 0} open</div>
        </div>

        <div className="breakdown-card revenue">
          <div className="card-title">Revenue</div>
          <div className="card-value" style={{ color: '#22c55e' }}>
            ${pnl.breakdown.revenue.toLocaleString('en-US', { minimumFractionDigits: 2 })}
          </div>
          <div className="card-meta">{pnl.components?.recentDeals || 0} deals</div>
        </div>

        <div className="breakdown-card costs">
          <div className="card-title">Costs</div>
          <div className="card-value" style={{ color: '#ef4444' }}>
            ${pnl.breakdown.costs.toLocaleString('en-US', { minimumFractionDigits: 2 })}
          </div>
          <div className="card-meta">Anthropic API</div>
        </div>
      </div>

      {/* History Chart (Simple Sparkline) */}
      {history.length > 1 && (
        <div className="pnl-history">
          <div className="history-title">60-Second History</div>
          <Sparkline data={history.map(h => h.netP&L)} />
        </div>
      )}

      {/* Offline Notice */}
      {connectionStatus !== 'connected' && (
        <div className="offline-notice">
          ⚠️ Using cached data • Last live update: {formattedTime}
        </div>
      )}
    </div>
  );
};

// =========================================================================
// Sparkline Chart Component
// =========================================================================

const Sparkline = ({ data }) => {
  if (!data || data.length === 0) return null;

  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;

  const width = 500;
  const height = 100;
  const padding = 10;
  const pointWidth = (width - padding * 2) / (data.length - 1);

  const points = data.map((value, i) => {
    const x = padding + i * pointWidth;
    const y = height - padding - ((value - min) / range) * (height - padding * 2);
    return `${x},${y}`;
  }).join(' ');

  return (
    <svg width={width} height={height} className="sparkline">
      <polyline
        points={points}
        fill="none"
        stroke="#3b82f6"
        strokeWidth="2"
      />
    </svg>
  );
};

export default P&LDashboard;
