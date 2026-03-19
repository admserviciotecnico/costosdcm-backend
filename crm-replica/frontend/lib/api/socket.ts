import { io, Socket } from 'socket.io-client';

let socketInstance: Socket | null = null;

export function getSocket() {
  if (!socketInstance) {
    socketInstance = io(process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4000', {
      transports: ['websocket']
    });
  }
  return socketInstance;
}
