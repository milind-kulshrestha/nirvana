import { useState, useEffect } from 'react';
import { Badge } from '@/components/ui/badge';
import { API_BASE } from '../config';

export default function CalendarWidget({ watchlistSymbols = [], filterMode = 'mine' }) {
  const [tab, setTab] = useState('earnings');
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    fetchEvents();
  }, [tab]);

  const fetchEvents = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/api/market/calendar?type=${tab}&days=30`, {
        credentials: 'include',
      });
      if (response.ok) {
        const data = await response.json();
        setEvents(data.events || []);
      }
    } catch (err) {
      console.error('Error fetching calendar:', err);
    } finally {
      setLoading(false);
    }
  };

  const filteredEvents = filter === 'mine' && watchlistSymbols.length > 0
    ? events.filter((e) => watchlistSymbols.includes(e.symbol))
    : events;

  const daysUntil = (dateStr) => {
    if (!dateStr) return null;
    const diff = Math.ceil((new Date(dateStr) - new Date()) / (1000 * 60 * 60 * 24));
    return diff >= 0 ? diff : null;
  };

  return (
    <div>
      {/* Tab + Filter controls */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex gap-1 bg-gray-100 rounded-lg p-1">
          <button
            onClick={() => setTab('earnings')}
            className={`px-3 py-1.5 rounded-md text-sm font-medium transition ${
              tab === 'earnings' ? 'bg-white shadow-sm text-gray-900' : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Earnings
          </button>
          <button
            onClick={() => setTab('dividends')}
            className={`px-3 py-1.5 rounded-md text-sm font-medium transition ${
              tab === 'dividends' ? 'bg-white shadow-sm text-gray-900' : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Dividends
          </button>
        </div>

        {watchlistSymbols.length > 0 && (
          <div className="flex gap-1 bg-gray-100 rounded-lg p-1">
            <button
              onClick={() => setFilter('mine')}
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition ${
                filter === 'mine' ? 'bg-white shadow-sm text-gray-900' : 'text-gray-600'
              }`}
            >
              My Stocks
            </button>
            <button
              onClick={() => setFilter('all')}
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition ${
                filter === 'all' ? 'bg-white shadow-sm text-gray-900' : 'text-gray-600'
              }`}
            >
              All
            </button>
          </div>
        )}
      </div>

      {/* Events list */}
      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-12 bg-gray-100 rounded-lg animate-pulse" />
          ))}
        </div>
      ) : filteredEvents.length === 0 ? (
        <div className="text-center py-8 text-gray-500 text-sm">
          {filter === 'mine' ? 'No upcoming events for your watchlist stocks' : 'No upcoming events'}
        </div>
      ) : (
        <div className="space-y-2 max-h-[400px] overflow-y-auto">
          {filteredEvents.map((event, idx) => {
            const days = daysUntil(event.date || event.ex_dividend_date);
            const isWatchlist = watchlistSymbols.includes(event.symbol);

            return (
              <div
                key={`${event.symbol}-${idx}`}
                className={`flex items-center justify-between p-3 rounded-lg border ${
                  isWatchlist ? 'border-indigo-200 bg-indigo-50/50' : 'border-gray-200 bg-white'
                }`}
              >
                <div className="flex items-center gap-3">
                  <div className="font-semibold text-sm text-gray-900 w-16">{event.symbol}</div>
                  <div className="text-xs text-gray-500">
                    {event.name && <span className="mr-2">{event.name}</span>}
                    {event.date || event.ex_dividend_date}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {tab === 'earnings' && event.eps_estimated != null && (
                    <span className="text-xs text-gray-500">
                      Est. ${event.eps_estimated.toFixed(2)}
                    </span>
                  )}
                  {tab === 'dividends' && event.dividend != null && (
                    <span className="text-xs text-gray-500">
                      ${event.dividend.toFixed(4)}
                    </span>
                  )}
                  {days != null && days <= 7 && (
                    <Badge variant={days <= 1 ? 'destructive' : 'secondary'} className="text-[10px]">
                      {days === 0 ? 'Today' : days === 1 ? 'Tomorrow' : `${days}d`}
                    </Badge>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
