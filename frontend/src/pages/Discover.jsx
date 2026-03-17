import { useState, useEffect, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import useAuthStore from '../stores/authStore';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { TrendingUp, Settings, Compass, RefreshCw, BarChart2 } from 'lucide-react';
import CalendarWidget from '../components/CalendarWidget';
import { API_BASE } from '../config';

export default function Discover() {
  const [tab, setTab] = useState('active');
  const [movers, setMovers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [watchlistSymbols, setWatchlistSymbols] = useState([]);
  const [sortKey, setSortKey] = useState(null);
  const [sortDir, setSortDir] = useState('desc');
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();

  const fetchMovers = useCallback(async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/api/market/movers?category=${tab}`, {
        credentials: 'include',
      });
      if (response.ok) {
        const data = await response.json();
        setMovers(data.items || []);
      }
    } catch (err) {
      console.error('Error fetching movers:', err);
    } finally {
      setLoading(false);
    }
  }, [tab]);

  useEffect(() => {
    fetchMovers();
  }, [fetchMovers]);

  useEffect(() => {
    fetchWatchlistSymbols();
  }, []);

  const fetchWatchlistSymbols = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/watchlists`, { credentials: 'include' });
      if (!response.ok) return;
      const watchlists = await response.json();

      const allSymbols = new Set();
      for (const wl of watchlists) {
        const itemsRes = await fetch(`${API_BASE}/api/watchlists/${wl.id}/items`, { credentials: 'include' });
        if (itemsRes.ok) {
          const items = await itemsRes.json();
          items.forEach((item) => allSymbols.add(item.symbol));
        }
      }
      setWatchlistSymbols([...allSymbols]);
    } catch (err) {
      console.error('Error fetching watchlist symbols:', err);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchMovers();
    setRefreshing(false);
  };

  const handleLogout = async () => {
    await logout();
    navigate('/');
  };

  const getInitials = (email) => (email ? email.substring(0, 2).toUpperCase() : 'U');

  const tabs = [
    { key: 'active', label: 'Most Active' },
    { key: 'gainers', label: 'Top Gainers' },
    { key: 'losers', label: 'Top Losers' },
  ];

  const handleSort = (key) => {
    if (sortKey === key) {
      setSortDir((d) => (d === 'desc' ? 'asc' : 'desc'));
    } else {
      setSortKey(key);
      setSortDir('desc');
    }
  };

  const sortedMovers = [...movers].sort((a, b) => {
    if (!sortKey) return 0;
    const aVal = a[sortKey] ?? 0;
    const bVal = b[sortKey] ?? 0;
    return sortDir === 'desc' ? bVal - aVal : aVal - bVal;
  });

  const SortArrow = ({ column }) => {
    if (sortKey !== column) return null;
    return <span className="ml-1">{sortDir === 'desc' ? '↓' : '↑'}</span>;
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-3">
              <Compass className="h-6 w-6 text-primary" />
              <h1 className="text-2xl font-bold tracking-tight">Discover</h1>
            </div>
            <nav className="hidden sm:flex items-center gap-1 text-sm">
              <Link
                to="/watchlists"
                className="px-3 py-1.5 rounded-md text-muted-foreground hover:text-foreground hover:bg-accent transition"
              >
                Watchlists
              </Link>
              <span className="px-3 py-1.5 rounded-md bg-accent text-foreground font-medium">
                Discover
              </span>
              <Link
                to="/etf"
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-muted-foreground hover:text-foreground hover:bg-accent transition"
              >
                <BarChart2 className="h-4 w-4" /> ETF
              </Link>
            </nav>
          </div>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="relative h-10 w-10 rounded-full" aria-label="User menu">
                <Avatar>
                  <AvatarFallback>{getInitials(user?.email)}</AvatarFallback>
                </Avatar>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent className="w-56" align="end">
              <DropdownMenuLabel>
                <div className="flex flex-col space-y-1">
                  <p className="text-sm font-medium leading-none">My Account</p>
                  <p className="text-xs leading-none text-muted-foreground">{user?.email}</p>
                </div>
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={() => navigate('/settings')}>
                <Settings className="mr-2 h-4 w-4" />
                Settings
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={handleLogout}>Log out</DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Market Movers — 2/3 width */}
          <div className="lg:col-span-2">
            <div className="flex items-center justify-between mb-4">
              <div className="flex gap-1 bg-gray-100 rounded-lg p-1">
                {tabs.map((t) => (
                  <button
                    key={t.key}
                    onClick={() => setTab(t.key)}
                    className={`px-4 py-2 rounded-md text-sm font-medium transition ${
                      tab === t.key
                        ? 'bg-white shadow-sm text-gray-900'
                        : 'text-gray-600 hover:text-gray-900'
                    }`}
                  >
                    {t.label}
                  </button>
                ))}
              </div>
              <Button variant="ghost" size="sm" onClick={handleRefresh} disabled={refreshing}>
                <RefreshCw className={`h-4 w-4 mr-1 ${refreshing ? 'animate-spin' : ''}`} />
                Refresh
              </Button>
            </div>

            {loading ? (
              <div className="space-y-2">
                {Array.from({ length: 10 }).map((_, i) => (
                  <Skeleton key={i} className="h-14 rounded-lg" />
                ))}
              </div>
            ) : movers.length === 0 ? (
              <div className="text-center py-12 text-muted-foreground">
                No market data available
              </div>
            ) : (
              <div className="border rounded-lg overflow-hidden">
                {/* Table header */}
                <div className="grid grid-cols-12 gap-2 px-4 py-2 bg-gray-50 text-xs font-medium text-gray-500 uppercase">
                  <div className="col-span-4">Symbol</div>
                  <button className="col-span-2 text-right cursor-pointer hover:text-gray-700" onClick={() => handleSort('price')}>
                    Price<SortArrow column="price" />
                  </button>
                  <button className="col-span-3 text-right cursor-pointer hover:text-gray-700" onClick={() => handleSort('change_percent')}>
                    Change<SortArrow column="change_percent" />
                  </button>
                  <button className="col-span-3 text-right hidden sm:block cursor-pointer hover:text-gray-700" onClick={() => handleSort('volume')}>
                    Volume<SortArrow column="volume" />
                  </button>
                </div>

                {/* Table rows */}
                {sortedMovers.map((mover, idx) => {
                  const isPositive = mover.change >= 0;
                  const isWatchlist = watchlistSymbols.includes(mover.symbol);
                  return (
                    <div
                      key={mover.symbol + idx}
                      className={`grid grid-cols-12 gap-2 px-4 py-3 border-t items-center hover:bg-gray-50 transition ${
                        isWatchlist ? 'bg-indigo-50/40' : ''
                      }`}
                    >
                      <div className="col-span-4 flex items-center gap-2">
                        <span className="font-semibold text-sm text-gray-900">{mover.symbol}</span>
                        {mover.name && (
                          <span className="text-xs text-gray-500 truncate hidden md:inline">
                            {mover.name}
                          </span>
                        )}
                        {isWatchlist && (
                          <Badge variant="outline" className="text-[10px] px-1.5 py-0">
                            <TrendingUp className="h-2.5 w-2.5 mr-0.5" />
                            WL
                          </Badge>
                        )}
                      </div>
                      <div className="col-span-2 text-right font-medium text-sm">
                        ${mover.price.toFixed(2)}
                      </div>
                      <div className={`col-span-3 text-right text-sm font-medium ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
                        {isPositive ? '+' : ''}{mover.change.toFixed(2)} ({(mover.change_percent).toFixed(2)}%)
                      </div>
                      <div className="col-span-3 text-right text-sm text-gray-600 hidden sm:block">
                        {mover.volume ? (mover.volume / 1000000).toFixed(1) + 'M' : 'N/A'}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Calendar sidebar — 1/3 width */}
          <div className="lg:col-span-1">
            <div className="bg-card rounded-lg border p-4">
              <h2 className="text-lg font-semibold mb-4">Upcoming Events</h2>
              <CalendarWidget watchlistSymbols={watchlistSymbols} filterMode="mine" />
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
