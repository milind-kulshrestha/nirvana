import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import useAuthStore from '../stores/authStore';

const API_BASE = 'http://localhost:8000';

export default function Watchlists() {
  const [watchlists, setWatchlists] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newWatchlistName, setNewWatchlistName] = useState('');
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();

  useEffect(() => {
    fetchWatchlists();
  }, []);

  const fetchWatchlists = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/watchlists`, {
        credentials: 'include',
      });
      if (response.ok) {
        const data = await response.json();
        setWatchlists(data);
      }
    } catch (error) {
      console.error('Error fetching watchlists:', error);
    } finally {
      setLoading(false);
    }
  };

  const createWatchlist = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch(`${API_BASE}/api/watchlists`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ name: newWatchlistName }),
      });

      if (response.ok) {
        await fetchWatchlists();
        setNewWatchlistName('');
        setShowCreateModal(false);
      }
    } catch (error) {
      console.error('Error creating watchlist:', error);
    }
  };

  const deleteWatchlist = async (id) => {
    if (!confirm('Delete this watchlist?')) return;

    try {
      const response = await fetch(`${API_BASE}/api/watchlists/${id}`, {
        method: 'DELETE',
        credentials: 'include',
      });

      if (response.ok) {
        await fetchWatchlists();
      }
    } catch (error) {
      console.error('Error deleting watchlist:', error);
    }
  };

  const handleLogout = async () => {
    await logout();
    navigate('/');
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
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900">My Watchlists</h1>
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-600">{user?.email}</span>
            <button
              onClick={handleLogout}
              className="text-sm text-gray-600 hover:text-gray-900"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Create Button */}
        <div className="mb-6">
          <button
            onClick={() => setShowCreateModal(true)}
            className="bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-2 px-6 rounded-lg transition"
          >
            + New Watchlist
          </button>
        </div>

        {/* Watchlists Grid */}
        {watchlists.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-500 mb-4">No watchlists yet</p>
            <button
              onClick={() => setShowCreateModal(true)}
              className="text-indigo-600 hover:text-indigo-700 font-medium"
            >
              Create your first watchlist
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {watchlists.map((watchlist) => (
              <Link
                key={watchlist.id}
                to={`/watchlists/${watchlist.id}`}
                className="bg-white rounded-lg shadow-sm hover:shadow-md transition p-6 border border-gray-200 group"
              >
                <div className="flex justify-between items-start mb-4">
                  <h2 className="text-xl font-semibold text-gray-900 group-hover:text-indigo-600 transition">
                    {watchlist.name}
                  </h2>
                  <button
                    onClick={(e) => {
                      e.preventDefault();
                      deleteWatchlist(watchlist.id);
                    }}
                    className="text-gray-400 hover:text-red-600 transition"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
                <div className="text-sm text-gray-500">
                  {watchlist.items_count} {watchlist.items_count === 1 ? 'stock' : 'stocks'}
                </div>
                <div className="text-xs text-gray-400 mt-2">
                  Created {new Date(watchlist.created_at).toLocaleDateString()}
                </div>
              </Link>
            ))}
          </div>
        )}

        {watchlists.length > 0 && watchlists.length >= 10 && (
          <div className="mt-6 text-center text-sm text-gray-500">
            Maximum watchlists reached (10/10)
          </div>
        )}
      </main>

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Create Watchlist</h2>
            <form onSubmit={createWatchlist}>
              <input
                type="text"
                value={newWatchlistName}
                onChange={(e) => setNewWatchlistName(e.target.value)}
                placeholder="Watchlist name"
                required
                maxLength={50}
                className="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none mb-4"
                autoFocus
              />
              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={() => {
                    setShowCreateModal(false);
                    setNewWatchlistName('');
                  }}
                  className="flex-1 bg-gray-200 hover:bg-gray-300 text-gray-700 font-semibold py-2 px-4 rounded-lg transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-2 px-4 rounded-lg transition"
                >
                  Create
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
