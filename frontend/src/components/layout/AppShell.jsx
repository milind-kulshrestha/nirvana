import { Outlet, useLocation } from 'react-router-dom';
import LeftSidebar from './LeftSidebar';
import RightRail from './RightRail';
import CommandPalette from '../CommandPalette';
import ErrorBoundary from '../ErrorBoundary';

export default function AppShell() {
  const location = useLocation();
  const isAgentHub = location.pathname === '/';

  return (
    <div className="flex h-screen w-screen overflow-hidden">
      <LeftSidebar />
      <main className="flex-1 min-w-0 overflow-auto">
        <ErrorBoundary>
          <Outlet />
        </ErrorBoundary>
      </main>
      {isAgentHub && <RightRail />}
      <CommandPalette />
    </div>
  );
}
