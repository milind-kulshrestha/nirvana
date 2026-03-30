import { Link, useLocation } from 'react-router-dom';
import useLayoutStore from '../../stores/layoutStore';
import useAuthStore from '../../stores/authStore';
import {
  Bot,
  BarChart3,
  Compass,
  PieChart,
  Settings,
  PanelLeftClose,
  PanelLeftOpen,
  LogOut,
} from 'lucide-react';

const NAV_ITEMS = [
  { label: 'Agent', icon: Bot, path: '/', group: 'ai' },
  { label: 'Watchlists', icon: BarChart3, path: '/watchlists', group: 'market' },
  { label: 'Discover', icon: Compass, path: '/discover', group: 'market' },
  { label: 'ETF', icon: PieChart, path: '/etf', group: 'market' },
];

const BOTTOM_ITEMS = [
  { label: 'Settings', icon: Settings, path: '/settings' },
];

export default function LeftSidebar() {
  const { sidebarCollapsed, toggleSidebar } = useLayoutStore();
  const { logout } = useAuthStore();
  const location = useLocation();

  const isActive = (path) => {
    if (path === '/') return location.pathname === '/';
    return location.pathname.startsWith(path);
  };

  const NavItem = ({ item }) => {
    const Icon = item.icon;
    const active = isActive(item.path);

    return (
      <Link
        to={item.path}
        className={`
          flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors duration-fast
          ${active
            ? 'bg-primary/10 text-primary'
            : 'text-muted-foreground hover:text-foreground hover:bg-muted'
          }
          ${sidebarCollapsed ? 'justify-center' : ''}
        `}
        title={sidebarCollapsed ? item.label : undefined}
      >
        <Icon className="h-[18px] w-[18px] shrink-0" strokeWidth={active ? 2.25 : 1.75} />
        {!sidebarCollapsed && <span>{item.label}</span>}
      </Link>
    );
  };

  return (
    <aside
      className={`
        flex flex-col h-full bg-card border-r border-border shrink-0 transition-all duration-normal
        ${sidebarCollapsed ? 'w-16' : 'w-60'}
      `}
    >
      {/* Logo */}
      <div className={`flex items-center h-14 border-b border-border shrink-0 ${sidebarCollapsed ? 'justify-center px-2' : 'px-4'}`}>
        {!sidebarCollapsed && (
          <span className="text-base font-bold tracking-tight text-foreground">Nirvana</span>
        )}
        {sidebarCollapsed && (
          <span className="text-base font-bold text-primary">N</span>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto px-2 py-3 space-y-1">
        {/* AI Section */}
        {!sidebarCollapsed && (
          <div className="px-3 pb-1 pt-1 text-[10px] font-semibold uppercase tracking-widest text-muted-foreground/60">
            Research
          </div>
        )}
        <NavItem item={NAV_ITEMS[0]} />

        {/* Market Section */}
        {!sidebarCollapsed && (
          <div className="px-3 pb-1 pt-4 text-[10px] font-semibold uppercase tracking-widest text-muted-foreground/60">
            Market
          </div>
        )}
        {sidebarCollapsed && <div className="my-2 mx-3 border-t border-border" />}
        {NAV_ITEMS.slice(1).map((item) => (
          <NavItem key={item.path} item={item} />
        ))}
      </nav>

      {/* Bottom */}
      <div className="border-t border-border px-2 py-3 space-y-1">
        {BOTTOM_ITEMS.map((item) => (
          <NavItem key={item.path} item={item} />
        ))}

        {/* Logout */}
        <button
          onClick={logout}
          className={`
            flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium w-full
            text-muted-foreground hover:text-foreground hover:bg-muted transition-colors duration-fast
            ${sidebarCollapsed ? 'justify-center' : ''}
          `}
          title={sidebarCollapsed ? 'Sign out' : undefined}
        >
          <LogOut className="h-[18px] w-[18px] shrink-0" strokeWidth={1.75} />
          {!sidebarCollapsed && <span>Sign Out</span>}
        </button>

        {/* Collapse toggle */}
        <button
          onClick={toggleSidebar}
          className={`
            flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium w-full
            text-muted-foreground hover:text-foreground hover:bg-muted transition-colors duration-fast
            ${sidebarCollapsed ? 'justify-center' : ''}
          `}
          title={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {sidebarCollapsed ? (
            <PanelLeftOpen className="h-[18px] w-[18px] shrink-0" strokeWidth={1.75} />
          ) : (
            <PanelLeftClose className="h-[18px] w-[18px] shrink-0" strokeWidth={1.75} />
          )}
          {!sidebarCollapsed && <span>Collapse</span>}
        </button>
      </div>
    </aside>
  );
}
