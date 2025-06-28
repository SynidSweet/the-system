import { useRef, useEffect, useCallback } from 'react';
import { ConnectionStatus, WebSocketMessage } from '../types';

interface UseWebSocketOptions {
  url: string;
  onMessage: (message: WebSocketMessage) => void;
  onConnectionStatusChange: (status: ConnectionStatus) => void;
  reconnectInterval?: number;
}

export const useWebSocket = ({
  url,
  onMessage,
  onConnectionStatusChange,
  reconnectInterval = 3000
}: UseWebSocketOptions) => {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const connect = useCallback(() => {
    // Prevent multiple connections
    if (wsRef.current && (
      wsRef.current.readyState === WebSocket.CONNECTING || 
      wsRef.current.readyState === WebSocket.OPEN
    )) {
      return;
    }
    
    const ws = new WebSocket(url);
    wsRef.current = ws;
    
    ws.onopen = () => {
      console.log('WebSocket connected');
      onConnectionStatusChange('connected');
      
      // Clear any pending reconnection attempts
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }
    };
    
    ws.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data);
        onMessage(message);
      } catch (e) {
        console.error('Error parsing WebSocket message:', e);
      }
    };
    
    ws.onclose = () => {
      console.log('WebSocket disconnected, reconnecting...');
      onConnectionStatusChange('disconnected');
      wsRef.current = null;
      
      // Attempt to reconnect after a delay
      reconnectTimeoutRef.current = setTimeout(connect, reconnectInterval);
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      onConnectionStatusChange('error');
    };
  }, [url, onMessage, onConnectionStatusChange, reconnectInterval]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.close();
      wsRef.current = null;
    }
  }, []);

  const sendMessage = useCallback((message: any) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
      return true;
    }
    return false;
  }, []);

  useEffect(() => {
    connect();
    
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    sendMessage,
    disconnect,
    isConnected: wsRef.current?.readyState === WebSocket.OPEN
  };
};