import { useState, useEffect, useRef, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import useChatStore from '../stores/chatStore';
import useCanvasStore from '../stores/canvasStore';
import useKeyboardShortcuts from '../hooks/useKeyboardShortcuts';
import { Search, MessageSquare, BarChart3, Compass, PieChart, Settings, Plus, StickyNote, Bot } from 'lucide-react';

const STATIC_ACTIONS = [
  { id: 'new-analysis', label: 'New Analysis', icon: Plus, category: 'Actions' },
  { id: 'add-note', label: 'Add Note to Canvas', icon: StickyNote, category: 'Actions' },
  { id: 'nav-agent', label: 'Go to Agent Hub', icon: Bot, category: 'Navigate' },
  { id: 'nav-watchlists', label: 'Go to Watchlists', icon: BarChart3, category: 'Navigate' },
  { id: 'nav-discover', label: 'Go to Discover', icon: Compass, category: 'Navigate' },
  { id: 'nav-etf', label: 'Go to ETF Dashboard', icon: PieChart, category: 'Navigate' },
  { id: 'nav-settings', label: 'Go to Settings', icon: Settings, category: 'Navigate' },
];

const QUICK_PROMPTS = [
  { id: 'prompt-scan', label: 'Scan my watchlist for opportunities', icon: MessageSquare, category: 'Quick Prompts' },
  { id: 'prompt-etf', label: 'Summarize ETF trends today', icon: MessageSquare, category: 'Quick Prompts' },
  { id: 'prompt-aapl', label: 'Deep-dive AAPL valuation', icon: MessageSquare, category: 'Quick Prompts' },
];

export default function CommandPalette() {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef(null);
  const navigate = useNavigate();
  const { createConversation, sendMessage } = useChatStore();
  const { addNote } = useCanvasStore();

  useKeyboardShortcuts({
    'mod+k': () => setOpen(true),
  });

  useEffect(() => {
    if (open) {
      setQuery('');
      setSelectedIndex(0);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [open]);

  const allActions = useMemo(() => [...STATIC_ACTIONS, ...QUICK_PROMPTS], []);

  const filtered = useMemo(() => {
    if (!query.trim()) return allActions;
    const q = query.toLowerCase();
    return allActions.filter((a) => a.label.toLowerCase().includes(q));
  }, [query, allActions]);

  // Group by category
  const grouped = useMemo(() => {
    const groups = {};
    filtered.forEach((a) => {
      if (!groups[a.category]) groups[a.category] = [];
      groups[a.category].push(a);
    });
    return groups;
  }, [filtered]);

  const flatFiltered = filtered;

  // Pre-compute flat index for each action id
  const flatIndexMap = useMemo(() => {
    const map = {};
    flatFiltered.forEach((a, i) => { map[a.id] = i; });
    return map;
  }, [flatFiltered]);

  const executeAction = async (action) => {
    setOpen(false);
    switch (action.id) {
      case 'new-analysis':
        await createConversation();
        navigate('/');
        break;
      case 'add-note':
        navigate('/');
        addNote();
        break;
      case 'nav-agent':
        navigate('/');
        break;
      case 'nav-watchlists':
        navigate('/watchlists');
        break;
      case 'nav-discover':
        navigate('/discover');
        break;
      case 'nav-etf':
        navigate('/etf');
        break;
      case 'nav-settings':
        navigate('/settings');
        break;
      default:
        if (action.id.startsWith('prompt-')) {
          navigate('/');
          await sendMessage(action.label);
        }
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Escape') {
      setOpen(false);
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex((i) => Math.min(i + 1, flatFiltered.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex((i) => Math.max(i - 1, 0));
    } else if (e.key === 'Enter' && flatFiltered[selectedIndex]) {
      e.preventDefault();
      executeAction(flatFiltered[selectedIndex]);
    }
  };

  if (!open) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-[100] bg-black/40 backdrop-blur-sm"
        onClick={() => setOpen(false)}
      />

      {/* Palette */}
      <div className="fixed inset-0 z-[101] flex items-start justify-center pt-[20vh]">
        <div className="w-full max-w-lg bg-popover border border-border rounded-2xl shadow-2xl overflow-hidden">
          {/* Search input */}
          <div className="flex items-center gap-3 px-4 py-3 border-b border-border">
            <Search className="h-4 w-4 text-muted-foreground shrink-0" />
            <input
              ref={inputRef}
              value={query}
              onChange={(e) => {
                setQuery(e.target.value);
                setSelectedIndex(0);
              }}
              onKeyDown={handleKeyDown}
              placeholder="Type a command or search..."
              className="flex-1 bg-transparent text-sm text-foreground placeholder:text-muted-foreground outline-none"
            />
            <kbd className="text-[10px] text-muted-foreground/50 bg-muted px-1.5 py-0.5 rounded">ESC</kbd>
          </div>

          {/* Results */}
          <div className="max-h-80 overflow-y-auto py-2">
            {flatFiltered.length === 0 && (
              <p className="text-sm text-muted-foreground text-center py-6">No results</p>
            )}

            {Object.entries(grouped).map(([category, items]) => (
              <div key={category}>
                <div className="px-4 py-1 text-[10px] font-semibold uppercase tracking-widest text-muted-foreground/50">
                  {category}
                </div>
                {items.map((action) => {
                  const idx = flatIndexMap[action.id];
                  const Icon = action.icon;
                  const isSelected = idx === selectedIndex;
                  return (
                    <button
                      key={action.id}
                      onClick={() => executeAction(action)}
                      onMouseEnter={() => setSelectedIndex(idx)}
                      className={`flex items-center gap-3 w-full px-4 py-2 text-sm text-left transition-colors duration-fast ${
                        isSelected ? 'bg-primary/10 text-primary' : 'text-foreground hover:bg-muted'
                      }`}
                    >
                      <Icon className={`h-4 w-4 shrink-0 ${isSelected ? 'text-primary' : 'text-muted-foreground'}`} />
                      <span>{action.label}</span>
                    </button>
                  );
                })}
              </div>
            ))}
          </div>

          {/* Footer */}
          <div className="flex items-center gap-4 px-4 py-2 border-t border-border text-[10px] text-muted-foreground/40">
            <span>↑↓ navigate</span>
            <span>↵ select</span>
            <span>esc close</span>
          </div>
        </div>
      </div>
    </>
  );
}
