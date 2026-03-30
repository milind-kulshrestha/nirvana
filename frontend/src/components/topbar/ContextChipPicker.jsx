import { useState, useEffect } from 'react';
import useAIContextStore from '../../stores/aiContextStore';
import { API_BASE } from '../../config';
import { Plus, BarChart3, PieChart, X } from 'lucide-react';

export default function ContextChipPicker() {
  const [open, setOpen] = useState(false);
  const [watchlists, setWatchlists] = useState([]);
  const [loading, setLoading] = useState(false);
  const { attachContext, attachedContexts } = useAIContextStore();

  const fetchWatchlists = async () => {
    if (watchlists.length > 0) return; // already fetched
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/watchlists`, { credentials: 'include' });
      if (res.ok) setWatchlists(await res.json());
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  };

  const handleOpen = () => {
    setOpen(true);
    fetchWatchlists();
  };

  const isAttached = (id) => attachedContexts.some((c) => c.id === id);

  const handleAttachWatchlist = (wl) => {
    attachContext({
      id: `watchlist-${wl.id}`,
      type: 'watchlist',
      label: wl.name,
      data: { watchlistId: wl.id },
    });
  };

  return (
    <div className="relative">
      <button
        onClick={handleOpen}
        className="flex items-center gap-1 text-[11px] text-muted-foreground hover:text-foreground px-2 py-1 rounded-lg hover:bg-muted transition-colors duration-fast"
        title="Attach context"
      >
        <Plus className="h-3 w-3" />
        Context
      </button>

      {open && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setOpen(false)} />
          <div className="absolute top-full left-0 mt-1 z-50 w-64 bg-popover border border-border rounded-xl shadow-lg overflow-hidden">
            <div className="flex items-center justify-between px-3 py-2 border-b border-border">
              <span className="text-xs font-medium text-foreground">Attach Context</span>
              <button
                onClick={() => setOpen(false)}
                className="p-0.5 rounded text-muted-foreground hover:text-foreground"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            </div>

            <div className="max-h-64 overflow-y-auto">
              {/* Watchlists */}
              <div className="px-3 pt-2 pb-1 text-[10px] font-semibold uppercase tracking-widest text-muted-foreground/60">
                Watchlists
              </div>
              {loading ? (
                <p className="text-xs text-muted-foreground px-3 py-2">Loading...</p>
              ) : watchlists.length === 0 ? (
                <p className="text-xs text-muted-foreground px-3 py-2">No watchlists</p>
              ) : (
                watchlists.map((wl) => {
                  const attached = isAttached(`watchlist-${wl.id}`);
                  return (
                    <button
                      key={wl.id}
                      onClick={() => {
                        if (!attached) handleAttachWatchlist(wl);
                      }}
                      disabled={attached}
                      className={`flex items-center gap-2 w-full px-3 py-2 text-xs text-left transition-colors duration-fast ${
                        attached
                          ? 'text-muted-foreground/50 cursor-default'
                          : 'text-foreground hover:bg-muted'
                      }`}
                    >
                      <BarChart3 className="h-3.5 w-3.5 text-primary/60 shrink-0" />
                      <span className="flex-1 truncate">{wl.name}</span>
                      {attached && <span className="text-[10px] text-muted-foreground/40">Added</span>}
                      {!attached && wl.items_count > 0 && (
                        <span className="text-[10px] text-muted-foreground/40">
                          {wl.items_count} stocks
                        </span>
                      )}
                    </button>
                  );
                })
              )}

              {/* ETF placeholder */}
              <div className="px-3 pt-3 pb-1 text-[10px] font-semibold uppercase tracking-widest text-muted-foreground/60">
                ETF Slices
              </div>
              <button
                onClick={() => {
                  attachContext({
                    id: 'etf-portfolio',
                    type: 'etf',
                    label: 'ETF Portfolio',
                    data: { source: 'etf-snapshot' },
                  });
                }}
                disabled={isAttached('etf-portfolio')}
                className={`flex items-center gap-2 w-full px-3 py-2 text-xs text-left transition-colors duration-fast ${
                  isAttached('etf-portfolio')
                    ? 'text-muted-foreground/50 cursor-default'
                    : 'text-foreground hover:bg-muted'
                }`}
              >
                <PieChart className="h-3.5 w-3.5 text-success/60 shrink-0" />
                <span className="flex-1">Full ETF Portfolio</span>
                {isAttached('etf-portfolio') && <span className="text-[10px] text-muted-foreground/40">Added</span>}
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
