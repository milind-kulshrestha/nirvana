import { useState, useEffect, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { RefreshCw, TrendingUp } from 'lucide-react';
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
      <main className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Market Movers */}
          <div className="lg:col-span-2">
            <div className="flex items-center justify-between mb-4">
              <div className="flex gap-0.5 bg-muted rounded-lg p-1">
                {tabs.map((t) => (
                  <button
                    key={t.key}
                    onClick={() => setTab(t.key)}
                    className={`px-4 py-2 rounded-md text-sm font-medium transition-colors duration-fast ${
                      tab === t.key
                        ? 'bg-background shadow-sm text-foreground'
                        : 'text-muted-foreground hover:text-foreground'
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
              <div className="border border-border rounded-lg overflow-hidden">
                {/* Table header */}
                <div className="grid grid-cols-12 gap-2 px-4 py-2 bg-muted/50 text-xs font-medium text-muted-foreground uppercase">
                  <div className="col-span-4">Symbol</div>
                  <button className="col-span-2 text-right cursor-pointer hover:text-foreground transition-colors" onClick={() => handleSort('price')}>
                    Price<SortArrow column="price" />
                  </button>
                  <button className="col-span-3 text-right cursor-pointer hover:text-foreground transition-colors" onClick={() => handleSort('change_percent')}>
                    Change<SortArrow column="change_percent" />
                  </button>
                  <button className="col-span-3 text-right hidden sm:block cursor-pointer hover:text-foreground transition-colors" onClick={() => handleSort('volume')}>
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
                      className={`grid grid-cols-12 gap-2 px-4 py-3 border-t border-border items-center hover:bg-muted/30 transition-colors duration-fast ${
                        isWatchlist ? 'bg-primary/5' : ''
                      }`}
                    >
                      <div className="col-span-4 flex items-center gap-2">
                        <span className="font-semibold text-sm text-foreground font-mono">{mover.symbol}</span>
                        {mover.name && (
                          <span className="text-xs text-muted-foreground truncate hidden md:inline">
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
                      <div className="col-span-2 text-right font-medium text-sm font-mono">
                        ${mover.price.toFixed(2)}
                      </div>
                      <div className={`col-span-3 text-right text-sm font-medium font-mono ${isPositive ? 'text-success' : 'text-destructive'}`}>
                        {isPositive ? '+' : ''}{mover.change.toFixed(2)} ({(mover.change_percent).toFixed(2)}%)
                      </div>
                      <div className="col-span-3 text-right text-sm text-muted-foreground hidden sm:block font-mono">
                        {mover.volume ? (mover.volume / 1000000).toFixed(1) + 'M' : 'N/A'}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Calendar sidebar */}
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
