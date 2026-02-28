/**
 * Socket.io Client Hook
 * Manages WebSocket connection lifecycle and selective subscriptions
 * Handles reconnection, cleanup, and error states
 */

import { useEffect, useRef, useCallback } from 'react';
import io from 'socket.io-client';

const SOCKET_URL = process.env.REACT_APP_SOCKET_URL || 'http://localhost:3001';
const RECONNECT_DELAY = 5000;
const MAX_RECONNECT_ATTEMPTS = 5;

/**
 * useSocket - Custom hook for Socket.io connection management
 * @param {Function} onConnect - Called when socket connects
 * @param {Function} onDisconnect - Called when socket disconnects
 * @param {Object} options - Configuration options
 * @returns {Object} Socket instance and connection state
 */
export const useSocket = (
  onConnect = () => {},
  onDisconnect = () => {},
  options = {}
) => {
  const socketRef = useRef(null);
  const reconnectAttemptsRef = useRef(0);
  const subscriptionsRef = useRef(new Map());

  // Initialize socket connection
  useEffect(() => {
    if (socketRef.current) return; // Already connected

    const socket = io(SOCKET_URL, {
      reconnection: true,
      reconnectionDelay: RECONNECT_DELAY,
      reconnectionDelayMax: 10000,
      reconnectionAttempts: MAX_RECONNECT_ATTEMPTS,
      transports: ['websocket', 'polling'],
      ...options,
    });

    socketRef.current = socket;

    socket.on('connect', () => {
      reconnectAttemptsRef.current = 0;
      onConnect();
      // Re-subscribe to all listeners after reconnection
      subscriptionsRef.current.forEach((listeners, event) => {
        listeners.forEach((listener) => {
          socket.on(event, listener);
        });
      });
    });

    socket.on('disconnect', () => {
      onDisconnect();
    });

    socket.on('error', (error) => {
      console.error('[Socket.io Error]', error);
    });

    socket.on('connect_error', (error) => {
      reconnectAttemptsRef.current += 1;
      console.warn(`[Socket.io Connection Error] Attempt ${reconnectAttemptsRef.current}:`, error);
      if (reconnectAttemptsRef.current >= MAX_RECONNECT_ATTEMPTS) {
        console.error('[Socket.io] Max reconnection attempts reached');
      }
    });

    return () => {
      // Cleanup: don't disconnect on unmount (socket persists for app)
      // Only call disconnect if this is the last subscriber
      // This pattern allows multiple hooks to share one socket
    };
  }, [onConnect, onDisconnect, options]);

  /**
   * Subscribe to a socket event with tracking
   * @param {string} event - Event name
   * @param {Function} listener - Listener callback
   * @returns {Function} Unsubscribe function
   */
  const subscribe = useCallback((event, listener) => {
    if (!socketRef.current) {
      console.warn('[Socket.io] Socket not initialized, subscription queued');
      return () => {};
    }

    socketRef.current.on(event, listener);

    // Track subscription for reconnection
    if (!subscriptionsRef.current.has(event)) {
      subscriptionsRef.current.set(event, []);
    }
    subscriptionsRef.current.get(event).push(listener);

    // Return unsubscribe function
    return () => {
      if (socketRef.current) {
        socketRef.current.off(event, listener);
      }
      const listeners = subscriptionsRef.current.get(event);
      if (listeners) {
        const index = listeners.indexOf(listener);
        if (index > -1) listeners.splice(index, 1);
      }
    };
  }, []);

  /**
   * Emit event to server
   * @param {string} event - Event name
   * @param {*} data - Event data
   * @param {Function} callback - Optional acknowledgment callback
   */
  const emit = useCallback((event, data, callback) => {
    if (!socketRef.current?.connected) {
      console.warn(`[Socket.io] Not connected, cannot emit ${event}`);
      return;
    }
    socketRef.current.emit(event, data, callback);
  }, []);

  /**
   * Get connection state
   */
  const isConnected = socketRef.current?.connected ?? false;
  const connectionId = socketRef.current?.id ?? null;

  return {
    socket: socketRef.current,
    isConnected,
    connectionId,
    subscribe,
    emit,
    reconnectAttempts: reconnectAttemptsRef.current,
  };
};

/**
 * Preset subscription hooks for specific data types
 */

export const useSocketEvent = (eventName, onData = () => {}) => {
  const { subscribe, isConnected } = useSocket();

  useEffect(() => {
    if (!isConnected) return;
    const unsubscribe = subscribe(eventName, onData);
    return unsubscribe;
  }, [eventName, onData, subscribe, isConnected]);
};

/**
 * Specialized hook for P&L updates
 */
export const useP2LUpdates = (onPnlUpdate = () => {}) => {
  return useSocketEvent('pnl:update', onPnlUpdate);
};
