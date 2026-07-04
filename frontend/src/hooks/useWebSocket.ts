'use client';

import { useEffect, useState, useRef } from 'react';

export const useWebSocket = (path: string = '/ws/events') => {
  const [event, setEvent] = useState<any>(null);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    let reconnectTimeout: any;

    const connect = () => {
      const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws';
      const token = localStorage.getItem('token') || '';
      const url = `${wsUrl}/events?token=${token}`;

      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        setConnected(true);
        console.log('WebSocket connection established');
      };

      ws.onmessage = (messageEvent) => {
        try {
          const payload = JSON.parse(messageEvent.data);
          setEvent(payload);
        } catch (e) {
          console.error('Error parsing WebSocket message data:', e);
        }
      };

      ws.onclose = () => {
        setConnected(false);
        console.log('WebSocket disconnected, reconnecting in 5s...');
        reconnectTimeout = setTimeout(connect, 5000);
      };

      ws.onerror = (err) => {
        console.error('WebSocket encountered an error:', err);
        ws.close();
      };
    };

    connect();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      clearTimeout(reconnectTimeout);
    };
  }, [path]);

  return { event, connected };
};
