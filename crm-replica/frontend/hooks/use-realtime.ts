'use client';

import { useEffect } from 'react';
import { getSocket } from '@/lib/api/socket';

export function useRealtime(onRefresh: () => void) {
  useEffect(() => {
    const socket = getSocket();
    socket.on('orders:changed', onRefresh);
    socket.on('orders:status_changed', onRefresh);
    socket.on('dashboard:refresh', onRefresh);

    return () => {
      socket.off('orders:changed', onRefresh);
      socket.off('orders:status_changed', onRefresh);
      socket.off('dashboard:refresh', onRefresh);
    };
  }, [onRefresh]);
}
