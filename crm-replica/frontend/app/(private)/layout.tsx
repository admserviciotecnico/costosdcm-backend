import { ReactNode } from 'react';
import { Sidebar } from '@/components/layout/sidebar';
import { Header } from '@/components/layout/header';
import { Protected } from '@/components/layout/protected';

export default function PrivateLayout({ children }: { children: ReactNode }) {
  return (
    <Protected>
      <div className="flex">
        <Sidebar />
        <div className="flex-1 min-h-screen">
          <Header />
          <main className="p-6">{children}</main>
        </div>
      </div>
    </Protected>
  );
}
