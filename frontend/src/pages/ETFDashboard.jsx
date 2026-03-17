import { useEffect, useRef, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import useAuthStore from '../stores/authStore';
import useEtfStore from '../stores/etfStore';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Skeleton } from '@/components/ui/skeleton';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { RefreshCw, Plus, X, TrendingUp, Settings, Compass, BarChart2 } from 'lucide-react';
import { API_BASE } from '../config';

// --- ABC Rating badge ---
function AbcBadge({ rating }) {
  if (!rating) return <span className="text-muted-foreground">—</span>;
  const colors = { A: 'bg-blue-500', B: 'bg-green-500', C: 'bg-amber-500' };
  return (
    <span className={`inline-flex items-center justify-center w-5 h-5 rounded-full text-white text-xs font-bold ${colors[rating] ?? 'bg-gray-500'}`}>
      {rating}
    </span>
  );
}

// --- Color-coded cell with background bar ---
function BarCell({ value, range, decimals = 2 }) {
  if (value == null) return <span className="text-muted-foreground text-xs">—</span>;
  const [min, max] = range ?? [-10, 10];
  const positive = value >= 0;
  const pct = Math.min(100, Math.abs(value) / Math.max(Math.abs(min), Math.abs(max)) * 100);
  return (
    <span className="relative inline-block min-w-[48px] text-right px-1">
      <span
        className={`absolute top-0 h-full rounded opacity-20 z-0 ${positive ? 'bg-green-500 left-0' : 'bg-red-500 right-0'}`}
        style={{ width: `${pct}%` }}
      />
      <span className={`relative z-10 font-medium ${positive ? 'text-green-500' : 'text-red-500'}`}>
        {value.toFixed(decimals)}%
      </span>
    </span>
  );
}

// --- RS sparkline SVG ---
function RsSparkline({ data }) {
  if (!data || data.length < 2) return <span className="text-muted-foreground text-xs">—</span>;
  const w = 80, h = 28;
  const min = Math.min(...data), max = Math.max(...data);
  const range = max - min || 1;
  const maxIdx = data.indexOf(Math.max(...data));
  return (
    <svg width={w} height={h} className="block">
      {data.map((v, i) => {
        const x = (i / (data.length - 1)) * w;
        const barH = Math.abs(((v - min) / range) * h * 0.8);
        return (
          <rect
            key={i}
            x={x - 1.5}
            y={h / 2 - (v >= 0 ? barH : 0)}
            width={3}
            height={barH || 1}
            fill={i === maxIdx ? '#4ade80' : '#9ca3af'}
            opacity={0.8}
          />
        );
      })}
    </svg>
  );
}

// --- Holdings popover ---
function HoldingsPopover({ symbol }) {
  const [open, setOpen] = useState(false);
  const [holdings, setHoldings] = useState(null);
  const [loading, setLoading] = useState(false);
  const containerRef = useRef(null);

  useEffect(() => {
    if (!open) return;
    const handler = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setOpen(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [open]);

  const load = async () => {
    if (open) { setOpen(false); return; }
    if (holdings !== null) { setOpen(true); return; }
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/etf/holdings/${symbol}`, { credentials: 'include' });
      const data = await res.json();
      setHoldings(data ?? []);
    } catch { setHoldings([]); }
    finally { setLoading(false); setOpen(true); }
  };

  return (
    <div ref={containerRef} className="relative inline-block">
      <button
        onClick={load}
        aria-label={`View top holdings for ${symbol}`}
        aria-expanded={open}
        className="text-xs px-1.5 py-0.5 rounded bg-muted hover:bg-muted/80 text-muted-foreground font-mono"
      >
        H
      </button>
      {open && (
        <div className="absolute left-0 top-6 z-50 w-52 bg-popover border border-border rounded shadow-lg p-2 text-xs">
          <div className="font-semibold mb-1">{symbol} Top Holdings</div>
          {loading && <div className="text-muted-foreground">Loading…</div>}
          {holdings && holdings.length === 0 && <div className="text-muted-foreground">No data</div>}
          {holdings && holdings.map((h, i) => {
            const pct = h.weight != null ? Math.round(h.weight * 100 * 10) / 10 : null;
            return (
              <div key={i} className="py-0.5">
                <div className="flex justify-between mb-0.5">
                  <span>{h.symbol}</span>
                  <span className="text-muted-foreground">{pct != null ? `${pct}%` : '—'}</span>
                </div>
                {pct != null && (
                  <div className="h-0.5 bg-muted rounded-full w-full">
                    <div className="h-full bg-primary rounded-full" style={{ width: `${Math.min(100, pct * 5)}%` }} />
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

// --- ETF table ---
const COLUMNS = [
  { key: 'ticker',         label: 'Ticker',  sortable: false },
  { key: 'abc',            label: 'Grade',   sortable: true  },
  { key: 'daily',          label: 'Daily',   sortable: true  },
  { key: 'intra',          label: 'Intra',   sortable: true  },
  { key: '5d',             label: '5D',      sortable: true  },
  { key: '20d',            label: '20D',     sortable: true  },
  { key: 'atr_pct',        label: 'ATR%',    sortable: true  },
  { key: 'dist_sma50_atr', label: 'ATRx',    sortable: true  },
  { key: 'rs',             label: 'VARS',    sortable: true  },
  { key: 'rrs_chart',      label: 'Chart',   sortable: false },
];

function ETFTable({ rows, ranges }) {
  const [sortKey, setSortKey] = useState('rs');
  const [sortDir, setSortDir] = useState('desc');

  const sorted = [...rows].sort((a, b) => {
    const av = a[sortKey], bv = b[sortKey];
    if (av == null && bv == null) return 0;
    if (av == null) return 1;
    if (bv == null) return -1;
    if (sortKey === 'abc') {
      const order = { A: 0, B: 1, C: 2 };
      return sortDir === 'asc'
        ? (order[av] ?? 3) - (order[bv] ?? 3)
        : (order[bv] ?? 3) - (order[av] ?? 3);
    }
    return sortDir === 'asc' ? av - bv : bv - av;
  });

  const toggleSort = (key) => {
    if (!COLUMNS.find(c => c.key === key)?.sortable) return;
    if (sortKey === key) setSortDir(d => d === 'asc' ? 'desc' : 'asc');
    else { setSortKey(key); setSortDir('desc'); }
  };

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs border-collapse">
        <thead>
          <tr className="bg-muted/50 text-muted-foreground">
            {COLUMNS.map(col => (
              <th
                key={col.key}
                onClick={() => toggleSort(col.key)}
                className={`px-2 py-1.5 text-left font-medium border-b border-border whitespace-nowrap ${col.sortable ? 'cursor-pointer hover:text-foreground' : ''} ${sortKey === col.key ? 'text-foreground' : ''}`}
              >
                {col.label}{col.sortable && sortKey === col.key && (sortDir === 'asc' ? ' ↑' : ' ↓')}
              </th>
            ))}
            <th className="px-2 py-1.5 text-left font-medium border-b border-border">Lev</th>
            <th className="px-2 py-1.5 text-left font-medium border-b border-border">Hold</th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((row) => (
            <tr key={row.ticker} className="border-b border-border/50 hover:bg-muted/30 transition-colors">
              <td className="px-2 py-1.5 font-mono font-semibold whitespace-nowrap">{row.ticker}</td>
              <td className="px-2 py-1.5"><AbcBadge rating={row.abc} /></td>
              <td className="px-2 py-1.5"><BarCell value={row.daily} range={ranges?.daily} /></td>
              <td className="px-2 py-1.5"><BarCell value={row.intra} range={ranges?.intra} /></td>
              <td className="px-2 py-1.5"><BarCell value={row['5d']} range={ranges?.['5d']} /></td>
              <td className="px-2 py-1.5"><BarCell value={row['20d']} range={ranges?.['20d']} /></td>
              <td className="px-2 py-1.5 text-muted-foreground">{row.atr_pct != null ? `${row.atr_pct}%` : '—'}</td>
              <td className="px-2 py-1.5 text-muted-foreground">{row.dist_sma50_atr != null ? row.dist_sma50_atr.toFixed(1) : '—'}</td>
              <td className="px-2 py-1.5 text-muted-foreground">{row.rs != null ? Math.round(row.rs) : '—'}</td>
              <td className="px-2 py-1.5"><RsSparkline data={row.rrs_chart} /></td>
              <td className="px-2 py-1.5 whitespace-nowrap">
                {(row.long ?? []).map(s => <span key={s} className="text-green-500 text-xs mr-1">{s}</span>)}
                {(row.short ?? []).map(s => <span key={s} className="text-red-400 text-xs mr-1">{s}</span>)}
              </td>
              <td className="px-2 py-1.5"><HoldingsPopover symbol={row.ticker} /></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// --- Main page ---
const GROUP_ORDER = ['Indices', 'S&P Style', 'Sel Sectors', 'EW Sectors', 'Industries', 'Countries', 'Custom'];

export default function ETFDashboard() {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();
  const {
    snapshot, status, progress, customSymbols,
    fetchSnapshot, fetchCustomSymbols, startRefresh,
    addCustomSymbol, removeCustomSymbol,
  } = useEtfStore();

  const [activeGroup, setActiveGroup] = useState('Indices');
  const [newSymbol, setNewSymbol] = useState('');

  useEffect(() => {
    fetchSnapshot();
    fetchCustomSymbols();
  }, [fetchSnapshot, fetchCustomSymbols]);

  const groups = snapshot?.groups ?? {};
  const availableGroups = GROUP_ORDER.filter(g => groups[g]?.length > 0 || g === 'Custom');

  useEffect(() => {
    if (!availableGroups.includes(activeGroup)) {
      setActiveGroup(availableGroups[0] ?? 'Indices');
    }
  }, [snapshot]);

  const handleAddSymbol = async () => {
    const sym = newSymbol.trim().toUpperCase();
    if (!sym) return;
    await addCustomSymbol(sym);
    setNewSymbol('');
  };

  const handleLogout = async () => { await logout(); navigate('/'); };

  return (
    <div className="flex flex-col h-screen bg-background">
      {/* Nav */}
      <header className="flex items-center justify-between px-4 py-3 border-b border-border shrink-0">
        <div className="flex items-center gap-4">
          <Link to="/watchlists" className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors">
            <TrendingUp className="h-4 w-4" /> Watchlists
          </Link>
          <Link to="/discover" className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors">
            <Compass className="h-4 w-4" /> Discover
          </Link>
          <span className="flex items-center gap-1.5 text-sm font-medium text-foreground">
            <BarChart2 className="h-4 w-4" /> ETF Dashboard
          </span>
        </div>
        <div className="flex items-center gap-3">
          {snapshot?.built_at && (
            <span className="text-xs text-muted-foreground hidden sm:block">
              Updated {new Date(snapshot.built_at).toLocaleTimeString()}
            </span>
          )}
          <Button
            size="sm"
            variant="outline"
            onClick={startRefresh}
            disabled={status === 'refreshing'}
            className="flex items-center gap-1.5"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${status === 'refreshing' ? 'animate-spin' : ''}`} />
            {status === 'refreshing'
              ? `${progress.done}/${progress.total || '…'}`
              : 'Refresh'}
          </Button>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="sm" className="h-8 w-8 rounded-full p-0">
                <Avatar className="h-7 w-7">
                  <AvatarFallback className="text-xs">{user?.email?.[0]?.toUpperCase()}</AvatarFallback>
                </Avatar>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuLabel className="text-xs font-normal text-muted-foreground">{user?.email}</DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={() => navigate('/settings')}>
                <Settings className="h-3.5 w-3.5 mr-2" /> Settings
              </DropdownMenuItem>
              <DropdownMenuItem onClick={handleLogout}>Sign Out</DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </header>

      {/* Progress bar */}
      {status === 'refreshing' && (
        <div className="h-0.5 bg-muted shrink-0">
          <div
            className="h-full bg-primary transition-all duration-300"
            style={{ width: progress.total > 0 ? `${(progress.done / progress.total) * 100}%` : '5%' }}
          />
        </div>
      )}

      {/* Group tabs */}
      <div className="flex gap-0.5 px-4 pt-3 border-b border-border shrink-0 overflow-x-auto">
        {availableGroups.map(g => (
          <button
            key={g}
            onClick={() => setActiveGroup(g)}
            className={`px-3 py-1.5 text-sm rounded-t font-medium whitespace-nowrap transition-colors border-b-2 ${
              activeGroup === g
                ? 'text-foreground border-primary'
                : 'text-muted-foreground border-transparent hover:text-foreground'
            }`}
          >
            {g}
            {groups[g]?.length > 0 && (
              <span className="ml-1.5 text-xs text-muted-foreground">({groups[g].length})</span>
            )}
          </button>
        ))}
      </div>

      {/* Table area */}
      <div className="flex-1 overflow-auto">
        {status === 'loading' && (
          <div className="p-4 space-y-2">
            {[...Array(10)].map((_, i) => <Skeleton key={i} className="h-8 w-full" />)}
          </div>
        )}

        {status !== 'loading' && !snapshot && (
          <div className="flex flex-col items-center justify-center h-full gap-3 text-muted-foreground">
            <BarChart2 className="h-12 w-12 opacity-20" />
            <p className="text-sm">No ETF data yet.</p>
            <p className="text-xs">Click <strong>Refresh</strong> to fetch ~180 ETFs from Yahoo Finance.</p>
          </div>
        )}

        {snapshot && activeGroup !== 'Custom' && groups[activeGroup] && (
          <ETFTable
            rows={groups[activeGroup]}
            ranges={snapshot.column_ranges?.[activeGroup]}
          />
        )}

        {activeGroup === 'Custom' && (
          <div>
            {groups['Custom']?.length > 0 && (
              <ETFTable
                rows={groups['Custom']}
                ranges={snapshot?.column_ranges?.['Custom']}
              />
            )}
            <div className="p-4 border-t border-border">
              <p className="text-xs text-muted-foreground mb-3">
                Custom symbols are fetched alongside presets on next Refresh.
              </p>
              <div className="flex gap-2 mb-4">
                <Input
                  value={newSymbol}
                  onChange={e => setNewSymbol(e.target.value.toUpperCase())}
                  onKeyDown={e => e.key === 'Enter' && handleAddSymbol()}
                  placeholder="e.g. TQQQ"
                  className="h-8 w-32 font-mono text-sm"
                  maxLength={20}
                />
                <Button size="sm" onClick={handleAddSymbol} className="h-8">
                  <Plus className="h-3.5 w-3.5 mr-1" /> Add
                </Button>
              </div>
              {customSymbols.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {customSymbols.map(sym => (
                    <Badge key={sym} variant="secondary" className="flex items-center gap-1 font-mono text-xs">
                      {sym}
                      <button
                        onClick={() => removeCustomSymbol(sym)}
                        className="ml-0.5 hover:text-destructive transition-colors"
                      >
                        <X className="h-3 w-3" />
                      </button>
                    </Badge>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
