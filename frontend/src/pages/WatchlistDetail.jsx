import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import StockRow from '../components/StockRow';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '../components/ui/dialog';
import { API_BASE } from '../config';

export default function WatchlistDetail() {
  const { id } = useParams();
  const [watchlist, setWatchlist] = useState(null);
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [newSymbol, setNewSymbol] = useState('');
  const [adding, setAdding] = useState(false);
  const [error, setError] = useState(null);
  const [expandedStockId, setExpandedStockId] = useState(null);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    fetchWatchlistData();
  }, [id]);

  const fetchWatchlistData = async () => {
    try {
      // Fetch watchlist details
      const watchlistsRes = await fetch(`${API_BASE}/api/watchlists`, {
        credentials: 'include',
      });
      const watchlistsData = await watchlistsRes.json();
      const currentWatchlist = watchlistsData.find((w) => w.id === parseInt(id));
      setWatchlist(currentWatchlist);

      // Fetch items with quotes
      await refreshStocks();
    } catch (error) {
      console.error('Error fetching watchlist:', error);
    } finally {
      setLoading(false);
    }
  };

  const refreshStocks = async () => {
    setRefreshing(true);
    try {
      // Fetch watchlist items
      const itemsRes = await fetch(`${API_BASE}/api/watchlists/${id}/items`, {
        credentials: 'include',
      });

      if (!itemsRes.ok) {
        setRefreshing(false);
        return;
      }

      const itemsData = await itemsRes.json();

      // Show items immediately with loading state
      setItems(itemsData.map(item => ({ ...item, loading: true })));

      // Fetch quote data for each item
      const itemsWithQuotes = await Promise.all(
        itemsData.map(async (item) => {
          try {
            const stockRes = await fetch(
              `${API_BASE}/api/securities/${item.symbol}?include=quote,ma200,estimates,performance`,
              { credentials: 'include' }
            );
            if (stockRes.ok) {
              const stockData = await stockRes.json();
              return { ...item, ...stockData, loading: false };
            }
            return { ...item, loading: false, error: 'Failed to fetch quote' };
          } catch (err) {
            console.error(`Error fetching ${item.symbol}:`, err);
            return { ...item, loading: false, error: err.message };
          }
        })
      );

      setItems(itemsWithQuotes);
      setRefreshing(false);
    } catch (error) {
      console.error('Error refreshing stocks:', error);
      setRefreshing(false);
    }
  };

  const addStock = async (e) => {
    e.preventDefault();
    setAdding(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE}/api/watchlists/${id}/items`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ symbol: newSymbol.toUpperCase() }),
      });

      if (response.ok) {
        const newItem = await response.json();

        // Fetch full stock data
        try {
          const stockRes = await fetch(
            `${API_BASE}/api/securities/${newItem.symbol}?include=quote,ma200,estimates,performance`,
            { credentials: 'include' }
          );
          if (stockRes.ok) {
            const stockData = await stockRes.json();
            setItems([...items, { ...newItem, ...stockData }]);
          } else {
            // Stock added to watchlist but market data unavailable — show it anyway
            setItems([...items, { ...newItem, loading: false, error: 'Market data temporarily unavailable' }]);
          }
        } catch {
          // Network error fetching market data — still show the stock
          setItems([...items, { ...newItem, loading: false, error: 'Market data temporarily unavailable' }]);
        }
        setNewSymbol('');
        setShowAddModal(false);
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Failed to add stock');
      }
    } catch (error) {
      setError(error.message);
    } finally {
      setAdding(false);
    }
  };

  const removeStock = async (itemId) => {
    try {
      const response = await fetch(`${API_BASE}/api/watchlists/${id}/items/${itemId}`, {
        method: 'DELETE',
        credentials: 'include',
      });

      if (response.ok) {
        setItems(items.filter((item) => item.id !== itemId));
        if (expandedStockId === itemId) {
          setExpandedStockId(null);
        }
      }
    } catch (error) {
      console.error('Error removing stock:', error);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-muted-foreground">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link
                to="/watchlists"
                className="text-sm text-muted-foreground hover:text-foreground transition-colors duration-fast"
              >
                ← Back
              </Link>
              <h1 className="text-lg font-semibold text-foreground">
                {watchlist?.name || 'Watchlist'}
              </h1>
            </div>
            <div className="flex gap-3">
              <Button
                variant="secondary"
                size="sm"
                onClick={refreshStocks}
                disabled={refreshing}
              >
                {refreshing ? 'Refreshing...' : '↻ Refresh'}
              </Button>
              <Button size="sm" onClick={() => setShowAddModal(true)}>
                + Add Stock
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {items.length === 0 ? (
          <div className="bg-card rounded-lg border p-12 text-center">
            <p className="text-muted-foreground mb-4">No stocks in this watchlist</p>
            <Button
              variant="link"
              onClick={() => setShowAddModal(true)}
            >
              Add your first stock
            </Button>
          </div>
        ) : (
          <div className="space-y-2">
            {items.map((item) => (
              <StockRow
                key={item.id}
                item={item}
                onRemove={() => removeStock(item.id)}
                onToggle={() => setExpandedStockId(expandedStockId === item.id ? null : item.id)}
                isExpanded={expandedStockId === item.id}
              />
            ))}
          </div>
        )}

        {items.length >= 50 && (
          <div className="mt-4 text-center text-sm text-muted-foreground">
            Maximum stocks reached (50/50)
          </div>
        )}
      </main>

      {/* Add Stock Dialog */}
      <Dialog open={showAddModal} onOpenChange={(open) => {
        setShowAddModal(open);
        if (!open) {
          setNewSymbol('');
          setError(null);
        }
      }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add Stock</DialogTitle>
            <DialogDescription>
              Enter a valid stock ticker symbol to add to this watchlist.
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={addStock}>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="symbol">Ticker Symbol</Label>
                <Input
                  id="symbol"
                  value={newSymbol}
                  onChange={(e) => setNewSymbol(e.target.value)}
                  placeholder="e.g., AAPL, MSFT"
                  required
                  maxLength={20}
                  autoFocus
                />
              </div>

              {error && (
                <div className="p-3 bg-destructive/10 border border-destructive/20 rounded-lg text-destructive text-sm">
                  {error}
                </div>
              )}
            </div>
            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  setShowAddModal(false);
                  setNewSymbol('');
                  setError(null);
                }}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={adding}>
                {adding ? 'Adding...' : 'Add'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
