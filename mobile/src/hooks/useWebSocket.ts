/**
 * WebSocket Hook for Real-time Processing Updates
 * 
 * This hook provides WebSocket connection management with automatic
 * reconnection, message handling, and connection state management
 * for real-time processing updates.
 */

import { useEffect, useRef, useState, useCallback } from 'react';

export interface WebSocketMessage {
  type: string;
  timestamp: string;
  [key: string]: any;
}

export interface WebSocketOptions {
  onMessage?: (message: WebSocketMessage) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Event) => void;
  onReconnect?: (attempt: number) => void;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  heartbeatInterval?: number;
  autoReconnect?: boolean;
}

export interface WebSocketState {
  socket: WebSocket | null;
  isConnected: boolean;
  isConnecting: boolean;
  error: string | null;
  reconnectAttempts: number;
  lastMessage: WebSocketMessage | null;
  connectionId: string | null;
}

export const useWebSocket = (url: string, options: WebSocketOptions = {}) => {
  const {
    onMessage,
    onConnect,
    onDisconnect,
    onError,
    onReconnect,
    reconnectInterval = 3000,
    maxReconnectAttempts = 5,
    heartbeatInterval = 30000,
    autoReconnect = true,
  } = options;

  const [state, setState] = useState<WebSocketState>({
    socket: null,
    isConnected: false,
    isConnecting: false,
    error: null,
    reconnectAttempts: 0,
    lastMessage: null,
    connectionId: null,
  });

  const socketRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const heartbeatTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const mountedRef = useRef(true);

  // Cleanup function
  const cleanup = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    if (heartbeatTimeoutRef.current) {
      clearTimeout(heartbeatTimeoutRef.current);
      heartbeatTimeoutRef.current = null;
    }
  }, []);

  // Send heartbeat ping
  const sendHeartbeat = useCallback(() => {
    if (socketRef.current?.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify({ type: 'ping', timestamp: new Date().toISOString() }));
      
      heartbeatTimeoutRef.current = setTimeout(sendHeartbeat, heartbeatInterval);
    }
  }, [heartbeatInterval]);

  // Connect to WebSocket
  const connect = useCallback(() => {
    if (!mountedRef.current || state.isConnecting) return;

    setState(prev => ({ ...prev, isConnecting: true, error: null }));

    try {
      const socket = new WebSocket(url);
      socketRef.current = socket;

      socket.onopen = () => {
        if (!mountedRef.current) return;

        console.log('WebSocket connected:', url);
        reconnectAttemptsRef.current = 0;

        setState(prev => ({
          ...prev,
          socket,
          isConnected: true,
          isConnecting: false,
          error: null,
          reconnectAttempts: 0,
        }));

        // Start heartbeat
        if (heartbeatInterval > 0) {
          sendHeartbeat();
        }

        onConnect?.();
      };

      socket.onmessage = (event) => {
        if (!mountedRef.current) return;

        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          
          setState(prev => ({ ...prev, lastMessage: message }));

          // Handle connection confirmation
          if (message.type === 'connection_established') {
            setState(prev => ({ ...prev, connectionId: message.user_id }));
          }

          // Handle pong response
          if (message.type === 'pong') {
            console.log('WebSocket heartbeat pong received');
            return;
          }

          onMessage?.(message);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      socket.onclose = (event) => {
        if (!mountedRef.current) return;

        console.log('WebSocket closed:', event.code, event.reason);
        
        setState(prev => ({
          ...prev,
          socket: null,
          isConnected: false,
          isConnecting: false,
          connectionId: null,
        }));

        cleanup();
        onDisconnect?.();

        // Auto-reconnect if enabled and not a normal closure
        if (autoReconnect && event.code !== 1000 && reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current++;
          
          setState(prev => ({ ...prev, reconnectAttempts: reconnectAttemptsRef.current }));

          console.log(`WebSocket reconnecting... Attempt ${reconnectAttemptsRef.current}/${maxReconnectAttempts}`);
          
          reconnectTimeoutRef.current = setTimeout(() => {
            if (mountedRef.current) {
              onReconnect?.(reconnectAttemptsRef.current);
              connect();
            }
          }, reconnectInterval * Math.pow(1.5, reconnectAttemptsRef.current - 1)); // Exponential backoff
        } else if (reconnectAttemptsRef.current >= maxReconnectAttempts) {
          setState(prev => ({
            ...prev,
            error: 'Max reconnection attempts reached',
          }));
        }
      };

      socket.onerror = (error) => {
        if (!mountedRef.current) return;

        console.error('WebSocket error:', error);
        
        setState(prev => ({
          ...prev,
          error: 'WebSocket connection error',
          isConnecting: false,
        }));

        onError?.(error);
      };

    } catch (error) {
      setState(prev => ({
        ...prev,
        error: 'Failed to create WebSocket connection',
        isConnecting: false,
      }));
    }
  }, [url, onMessage, onConnect, onDisconnect, onError, onReconnect, autoReconnect, maxReconnectAttempts, reconnectInterval, cleanup, sendHeartbeat, heartbeatInterval]);

  // Disconnect from WebSocket
  const disconnect = useCallback(() => {
    cleanup();
    
    if (socketRef.current) {
      socketRef.current.close(1000, 'Client disconnect');
      socketRef.current = null;
    }

    setState(prev => ({
      ...prev,
      socket: null,
      isConnected: false,
      isConnecting: false,
      connectionId: null,
    }));
  }, [cleanup]);

  // Send message
  const sendMessage = useCallback((message: any) => {
    if (socketRef.current?.readyState === WebSocket.OPEN) {
      const messageString = typeof message === 'string' ? message : JSON.stringify(message);
      socketRef.current.send(messageString);
      return true;
    }
    return false;
  }, []);

  // Force reconnect
  const reconnect = useCallback(() => {
    disconnect();
    reconnectAttemptsRef.current = 0;
    setState(prev => ({ ...prev, reconnectAttempts: 0, error: null }));
    setTimeout(connect, 100);
  }, [disconnect, connect]);

  // Subscribe to pipeline updates
  const subscribeToPipeline = useCallback((pipelineId: string) => {
    return sendMessage({
      type: 'subscribe_pipeline',
      pipeline_id: pipelineId,
      timestamp: new Date().toISOString(),
    });
  }, [sendMessage]);

  // Unsubscribe from pipeline updates
  const unsubscribeFromPipeline = useCallback((pipelineId: string) => {
    return sendMessage({
      type: 'unsubscribe_pipeline',
      pipeline_id: pipelineId,
      timestamp: new Date().toISOString(),
    });
  }, [sendMessage]);

  // Cancel pipeline
  const cancelPipeline = useCallback((pipelineId: string) => {
    return sendMessage({
      type: 'cancel_pipeline',
      pipeline_id: pipelineId,
      timestamp: new Date().toISOString(),
    });
  }, [sendMessage]);

  // Retry failed jobs
  const retryFailedJobs = useCallback((pipelineId: string) => {
    return sendMessage({
      type: 'retry_failed_jobs',
      pipeline_id: pipelineId,
      timestamp: new Date().toISOString(),
    });
  }, [sendMessage]);

  // Initialize connection
  useEffect(() => {
    if (url) {
      connect();
    }

    return () => {
      mountedRef.current = false;
      disconnect();
    };
  }, [url, connect, disconnect]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      mountedRef.current = false;
      cleanup();
    };
  }, [cleanup]);

  return {
    // Connection state
    ...state,
    
    // Connection management
    connect,
    disconnect,
    reconnect,
    
    // Message handling
    sendMessage,
    
    // Pipeline-specific actions
    subscribeToPipeline,
    unsubscribeFromPipeline,
    cancelPipeline,
    retryFailedJobs,
    
    // Utility properties
    readyState: socketRef.current?.readyState ?? WebSocket.CLOSED,
    url,
  };
};