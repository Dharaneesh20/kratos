import { useEffect, useState } from 'react';

export function useWebSocket(onMessage: (data: any) => void) {
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    const wsUrl = `ws://${window.location.host}/ws`;
    let socket: WebSocket | null = null;

    try {
      socket = new WebSocket(wsUrl);

      socket.onopen = () => {
        setIsConnected(true);
      };

      socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          onMessage(data);
        } catch (e) {
          console.error("Failed to parse WS message:", e);
        }
      };

      socket.onclose = () => {
        setIsConnected(false);
      };

      socket.onerror = (err) => {
        console.error("WS error:", err);
      };
    } catch (e) {
      console.warn("WS connection setup failed, will fall back to HTTP polling.");
    }

    return () => {
      if (socket) {
        socket.close();
      }
    };
  }, []);

  return { isConnected };
}
