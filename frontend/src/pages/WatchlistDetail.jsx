import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import StockRow from '../components/StockRow';

const API_BASE = 'http://localhost:8000';

export default function WatchlistDetail() {
  const { id } = useParams();
  const [watchlist, setWatchlist] = useState(null);
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [newSymbol, setNewSymbol] = useState('');
  const [adding, setAdding] = useState(false);
  const [error, setError] = useState(null);
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
              `${API_BASE}/api/securities/${item.symbol}?include=quote,ma200`,
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
        const stockRes = await fetch(
          `${API_BASE}/api/securities/${newItem.symbol}?include=quote,ma200`,
          { credentials: 'include' }
        );
        const stockData = await stockRes.json();

        setItems([...items, { ...newItem, ...stockData }]);
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
      }
    } catch (error) {
      console.error('Error removing stock:', error);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-gray-600">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-3 sm:px-4 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link
                to="/watchlists"
                className="text-gray-600 hover:text-gray-900"
              >
                ← Back
              </Link>
              <h1 className="text-2xl font-bold text-gray-900">
                {watchlist?.name || 'Watchlist'}
              </h1>
            </div>
            <div className="flex gap-3">
              <button
                onClick={refreshStocks}
                disabled={refreshing}
                className="bg-gray-200 hover:bg-gray-300 text-gray-700 font-semibold py-2 px-4 rounded-lg transition disabled:opacity-50"
              >
                {refreshing ? 'Refreshing...' : '↻ Refresh'}
              </button>
              <button
                onClick={() => setShowAddModal(true)}
                className="bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-2 px-4 rounded-lg transition"
              >
                + Add Stock
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-3 sm:px-4 py-4">
        {/* Stocks List */}
        {items.length === 0 ? (
          <div className="bg-white rounded-lg shadow-sm p-12 text-center">
            <p className="text-gray-500 mb-4">No stocks in this watchlist</p>
            <button
              onClick={() => setShowAddModal(true)}
              className="text-indigo-600 hover:text-indigo-700 font-medium"
            >
              Add your first stock
            </button>
          </div>
        ) : (
          <div className="space-y-1.5">
            {items.map((item) => (
              <StockRow
                key={item.id}
                item={item}
                onRemove={() => removeStock(item.id)}
              />
            ))}
          </div>
        )}

        {items.length >= 50 && (
          <div className="mt-4 text-center text-sm text-gray-500">
            Maximum stocks reached (50/50)
          </div>
        )}
      </main>

      {/* Add Stock Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Add Stock</h2>
            <form onSubmit={addStock}>
              <input
                type="text"
                value={newSymbol}
                onChange={(e) => setNewSymbol(e.target.value)}
                placeholder="Ticker symbol (e.g., AAPL, MSFT)"
                required
                maxLength={20}
                className="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none mb-2"
                autoFocus
              />
              <p className="text-xs text-gray-500 mb-4">
                Enter a valid stock ticker symbol
              </p>

              {error && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-600 text-sm mb-4">
                  {error}
                </div>
              )}

              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={() => {
                    setShowAddModal(false);
                    setNewSymbol('');
                    setError(null);
                  }}
                  className="flex-1 bg-gray-200 hover:bg-gray-300 text-gray-700 font-semibold py-2 px-4 rounded-lg transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={adding}
                  className="flex-1 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-2 px-4 rounded-lg transition disabled:opacity-50"
                >
                  {adding ? 'Adding...' : 'Add'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
